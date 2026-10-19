"""Synthetic Combine and NFL data with a planted (or null) movement signal.

SYNTHETIC: these data test whether the pipeline recovers a signal that exists
and declines to report one that does not. They are not evidence about football.

Each athlete has a latent recovery ability u. A turn attempt runs straight at
entry speed s, brakes to a plant, turns by angle a, then accelerates along the
new heading with time constant tau = tau0 * exp(-u) * (1 + c_s s + c_a a). NFL
get-off depends on conventional measurements, on u with weight `signal`, on play
context, and on noise; players with few snaps are noisier.
"""
import random
from math import cos, sin, radians, exp
from .schema import Athlete, Attempt, Frame, Play, Dataset

POSITIONS = ("DE", "DT", "OLB")
DRILLS = ("L-drill", "pro-agility", "bag-turn")
HZ = 10


def _trajectory(rng, s, a, tau, noise):
    frames = []
    t, x, y = 0.0, 0.0, 0.0
    heading = rng.uniform(0, 2*3.14159)
    dt = 1.0/HZ
    v = s

    def step(vx, vy):
        nonlocal t, x, y
        x += vx*dt
        y += vy*dt
        t += dt
        frames.append(Frame(round(t, 3), x+rng.gauss(0, noise), y+rng.gauss(0, noise)))
    frames.append(Frame(0.0, x, y))
    for _ in range(int(1.5*HZ)):  # approach
        step(v*cos(heading), v*sin(heading))
    brake = int(0.4*HZ)
    for k in range(brake):  # brake to plant
        v = s*(1-(k+1)/brake)*0.85+0.15*s*(1-(k+1)/brake)
        step(v*cos(heading), v*sin(heading))
    heading += radians(a)*(1 if rng.random() < 0.5 else -1)
    vmax = s*1.05
    for k in range(int(1.5*HZ)):  # recovery
        v = vmax*(1-exp(-(k+1)*dt/tau))
        step(v*cos(heading), v*sin(heading))
    return frames


def generate(n_athletes=90, years=(2021, 2022, 2023, 2024), signal=1.0, seed=0, attempts_per_drill=2,
             position_noise=0.03, plays_range=(5, 120)):
    rng = random.Random(seed)
    athletes, attempts, plays, latent = {}, [], [], {}
    for i in range(n_athletes):
        aid = f"A{i:04d}"
        pos = POSITIONS[i % len(POSITIONS)]
        year = years[i % len(years)]
        u = rng.gauss(0, 1)
        latent[aid] = u
        weight = {"DE": 265, "DT": 305, "OLB": 245}[pos]+rng.gauss(0, 10)
        forty = 4.6+(weight-260)*0.006+rng.gauss(0, 0.08)-0.03*u
        meas = {"weight": round(weight, 1), "forty": round(forty, 3), "vertical": round(33+rng.gauss(0, 2.5), 1),
                "three_cone": round(7.3+(weight-260)*0.004+rng.gauss(0, 0.12), 3)}
        measured_on = f"{year}-03-01"
        athletes[aid] = Athlete(aid, pos, year, meas, {k: measured_on for k in meas})
        # Not every athlete runs every drill: availability must not leak into the movement advantage.
        drills = [d for d in DRILLS if rng.random() < 0.85] or [DRILLS[0]]
        for d in drills:
            for r in range(attempts_per_drill):
                s = {"L-drill": 5.0, "pro-agility": 6.0, "bag-turn": 4.0}[d]+rng.gauss(0, 0.5)
                a = {"L-drill": 90, "pro-agility": 170, "bag-turn": 60}[d]+rng.gauss(0, 8)
                tau = 0.35*exp(-0.35*u)*(1+0.04*(s-5)+0.002*(a-90))
                frames = _trajectory(rng, s, max(5, min(178, a)), tau, position_noise)
                attempts.append(Attempt(aid, f"{aid}-{d}-{r}", d, frames, f"{year}-02-28"))
        n_plays = rng.randint(*plays_range)
        talent = 0.6*(-0.02*(forty-4.6)/0.1)+signal*0.025*u
        for k in range(n_plays):
            season = year+rng.randint(0, 2)
            align = rng.choice(["wide", "tight", "interior"])
            pass_play = rng.random() < 0.6
            ctx_effect = {"wide": 0.02, "tight": 0.0, "interior": -0.015}[align]+(-0.01 if pass_play else 0.0)
            y = 0.85-talent+ctx_effect+rng.gauss(0, 0.08)
            plays.append(Play(aid, season, f"{aid}-P{k}", round(y, 4),
                              {"alignment": align, "pass_play": 1.0 if pass_play else 0.0}))
    return Dataset(athletes, attempts, plays, {"synthetic": {"seed": seed, "signal": signal, "n": n_athletes, "latent": latent}},
                   {"name": "get_off", "units": "seconds", "meaning": "SYNTHETIC get-off",
                    "eligible_play": "all synthetic plays", "minimum_plays": 5, "lower_is_better": True},
                   synthetic=True)


def export_csv(ds, root):
    """Write a dataset in the default mapping's CSV layout (the data contract by example)."""
    import csv
    from pathlib import Path
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with open(root/"tracking.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["athlete_id", "attempt_id", "drill", "t", "x", "y", "recorded_on"])
        for a in ds.attempts:
            for fr in a.frames:
                w.writerow([a.athlete_id, a.attempt_id, a.drill, fr.t, round(fr.x, 4), round(fr.y, 4), a.recorded_on])
    names = sorted({k for a in ds.athletes.values() for k in a.measurements})
    with open(root/"athletes.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["athlete_id", "position", "draft_year", "measured_on"]+names)
        for a in ds.athletes.values():
            when = next(iter(a.available_on.values()), "")
            w.writerow([a.athlete_id, a.position, a.draft_year, when]+[a.measurements.get(k, "") for k in names])
    ctx = sorted({k for p in ds.plays for k in p.context})
    with open(root/"plays.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["athlete_id", "season", "play_id", "get_off"]+ctx)
        for p in ds.plays:
            w.writerow([p.athlete_id, p.season, p.play_id, p.outcome]+[p.context.get(k, "") for k in ctx])
