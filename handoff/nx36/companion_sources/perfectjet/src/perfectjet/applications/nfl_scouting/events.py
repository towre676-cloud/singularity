"""Turn events and normalized recovery travel.

A turn is detected operationally: a speed minimum (the plant) after which the
direction of travel differs from the incoming direction by at least a threshold.
This is a detected direction change, not a verified plant-and-recovery event;
`review_sample` draws an outcome-blinded sample for human review.

The recovery readout is normalized travel in the outgoing direction,

    eta = sum_k w_k v_k / (0.5 s_entry),

where v_k is velocity projected on the outgoing direction over the half second
after the plant and w_k are trapezoidal weights. It is not force, energy
efficiency, or physiological capacity. Smoothing and alignment branches are kept
because their spread exposes sensitivity to reasonable extraction choices; that
spread is a sensitivity range, not a calibrated interval.
"""
import random
from dataclasses import dataclass, asdict
from math import atan2, cos, sin, hypot, pi, degrees
from . import EXTRACTION_VERSION
from .schema import Lineage

RECOVERY = 0.5  # seconds
SMOOTHING = (1, 3, 5)
ALIGNMENT = ("chord", "heading")


@dataclass
class TurnEvent:
    athlete_id: str
    attempt_id: str
    drill: str
    entry_speed: float  # yards/s
    turn_angle: float  # degrees, 0..180
    eta: float  # primary branch
    eta_branches: dict
    plant_index: int
    lineage: Lineage

    @property
    def sensitivity(self):
        vals = list(self.eta_branches.values())
        return max(vals)-min(vals)


def smooth(frames, k):
    if k <= 1:
        return [(f.t, f.x, f.y) for f in frames]
    h = k//2
    out = []
    for i, f in enumerate(frames):
        lo, hi = max(0, i-h), min(len(frames), i+h+1)
        w = frames[lo:hi]
        out.append((f.t, sum(p.x for p in w)/len(w), sum(p.y for p in w)/len(w)))
    return out


def velocities(path):
    out = []
    for i in range(len(path)):
        a, b = path[max(0, i-1)], path[min(len(path)-1, i+1)]
        dt = b[0]-a[0]
        out.append(((b[1]-a[1])/dt, (b[2]-a[2])/dt) if dt > 0 else (0.0, 0.0))
    return out


def _unit(vx, vy):
    n = hypot(vx, vy)
    return (vx/n, vy/n) if n > 1e-9 else (0.0, 0.0)


def _angle(u, v):
    c = max(-1.0, min(1.0, u[0]*v[0]+u[1]*v[1]))
    s = u[0]*v[1]-u[1]*v[0]
    return abs(degrees(atan2(s, c)))


def _index_at(path, t):
    return min(range(len(path)), key=lambda i: abs(path[i][0]-t))


def trapezoid_weights(times):
    w = [0.0]*len(times)
    for i in range(len(times)-1):
        dt = times[i+1]-times[i]
        w[i] += dt/2
        w[i+1] += dt/2
    return w


def detect_plants(path, vel, min_drop=0.6, min_angle=30.0, lookback=1.0, lookahead=0.8):
    """Indices of speed minima that follow a speed drop and precede a direction change."""
    speed = [hypot(*v) for v in vel]
    t = [p[0] for p in path]
    plants = []
    for i in range(1, len(path)-1):
        if not (speed[i] <= speed[i-1] and speed[i] < speed[i+1]):
            continue
        if t[i]-t[0] < lookback or t[-1]-t[i] < lookahead:
            continue
        before = [speed[j] for j in range(len(path)) if t[i]-lookback <= t[j] < t[i]]
        if not before or speed[i] > min_drop*max(before):
            continue
        u_in = _unit(path[i][1]-path[_index_at(path, t[i]-lookback)][1], path[i][2]-path[_index_at(path, t[i]-lookback)][2])
        j = _index_at(path, t[i]+lookahead)
        u_out = _unit(path[j][1]-path[i][1], path[j][2]-path[i][2])
        if _angle(u_in, u_out) >= min_angle:
            if not plants or t[i]-t[plants[-1]] > lookahead:
                plants.append(i)
    return plants


def recovery_eta(path, vel, i, alignment, lookback=1.0, lookahead=0.8):
    t = [p[0] for p in path]
    lo = _index_at(path, t[i]-lookback)
    mid = _index_at(path, t[i]-RECOVERY)
    entry = [hypot(*vel[j]) for j in range(lo, mid+1)]
    s_entry = sum(entry)/len(entry)
    u_in = _unit(path[i][1]-path[lo][1], path[i][2]-path[lo][2])
    if alignment == "chord":
        j = _index_at(path, t[i]+lookahead)
        u_out = _unit(path[j][1]-path[i][1], path[j][2]-path[i][2])
    else:
        a, b = _index_at(path, t[i]+0.3), _index_at(path, t[i]+lookahead)
        u_out = _unit(sum(vel[k][0] for k in range(a, b+1)), sum(vel[k][1] for k in range(a, b+1)))
    end = _index_at(path, t[i]+RECOVERY)
    idx = list(range(i, end+1))
    w = trapezoid_weights([t[k] for k in idx])
    travel = sum(wk*(vel[k][0]*u_out[0]+vel[k][1]*u_out[1]) for wk, k in zip(w, idx))
    return travel/(RECOVERY*s_entry) if s_entry > 1e-6 else float("nan"), s_entry, _angle(u_in, u_out)


def extract(attempt, primary=(3, "chord"), **kw):
    """All turn events of one attempt, with every smoothing/alignment branch evaluated."""
    events = []
    base = smooth(attempt.frames, primary[0])
    plants = detect_plants(base, velocities(base), **kw)
    for i in plants:
        branches = {}
        for k in SMOOTHING:
            path = smooth(attempt.frames, k)
            vel = velocities(path)
            for al in ALIGNMENT:
                branches[f"s{k}-{al}"] = recovery_eta(path, vel, i, al)[0]
        eta, s_entry, angle = recovery_eta(base, velocities(base), i, primary[1])
        lin = Lineage(attempt.athlete_id, attempt.attempt_id, attempt.drill,
                      (i, _index_at(base, base[i][0]+RECOVERY)), (base[i][0]-1.0, base[i][0]+RECOVERY),
                      "eta: dimensionless (yards / (s * yards/s)); speed yards/s; angle degrees",
                      EXTRACTION_VERSION, attempt.recorded_on,
                      {"smoothing": primary[0], "alignment": primary[1]})
        events.append(TurnEvent(attempt.athlete_id, attempt.attempt_id, attempt.drill, s_entry, angle, eta,
                                branches, i, lin))
    return events


def extract_all(attempts, **kw):
    out = []
    for a in attempts:
        out.extend(extract(a, **kw))
    return out


def review_sample(events, per_stratum=2, seed=0):
    """Outcome-blinded review sheet stratified by drill, speed tercile and angle band."""
    rng = random.Random(seed)
    speeds = sorted(e.entry_speed for e in events)
    cut = [speeds[len(speeds)//3], speeds[2*len(speeds)//3]] if speeds else [0, 0]
    strata = {}
    for e in events:
        sp = 0 if e.entry_speed < cut[0] else (1 if e.entry_speed < cut[1] else 2)
        band = "shallow" if e.turn_angle < 60 else ("medium" if e.turn_angle < 120 else "sharp")
        strata.setdefault((e.drill, sp, band), []).append(e)
    sheet = []
    for key in sorted(strata):
        pick = rng.sample(strata[key], min(per_stratum, len(strata[key])))
        hard = max(strata[key], key=lambda e: e.sensitivity)
        if hard not in pick:
            pick.append(hard)
        for e in pick:
            sheet.append({"attempt_id": e.attempt_id, "drill": e.drill, "plant_frame": e.plant_index,
                          "time_range": e.lineage.time_range, "entry_speed": round(e.entry_speed, 2),
                          "turn_angle": round(e.turn_angle, 1), "branch_spread": round(e.sensitivity, 4),
                          "difficult_example": e is hard,
                          "reviewer_event_correct": "", "reviewer_entry_frame_ok": "", "reviewer_recovery_frame_ok": ""})
    return sheet
