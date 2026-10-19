"""Dependency-free SVG figures: demand support, a validated event, and the predictive comparison."""
from math import hypot
from .events import smooth, velocities, RECOVERY

W, H, PAD = 560, 360, 48
INK, MUTED, GRID, A, B = "#1f2937", "#6b7280", "#e5e7eb", "#2563eb", "#d97706"


def _scale(lo, hi, a, b):
    span = (hi-lo) or 1.0
    return lambda v: a+(v-lo)/span*(b-a)


def _frame(title, xlabel, ylabel):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'font-family="system-ui,sans-serif" font-size="12">',
            f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
            f'<text x="{PAD}" y="22" font-size="14" fill="{INK}">{title}</text>',
            f'<text x="{W/2}" y="{H-10}" text-anchor="middle" fill="{MUTED}">{xlabel}</text>',
            f'<text x="14" y="{H/2}" transform="rotate(-90 14 {H/2})" text-anchor="middle" fill="{MUTED}">{ylabel}</text>',
            f'<line x1="{PAD}" y1="{H-PAD}" x2="{W-PAD/2}" y2="{H-PAD}" stroke="{GRID}"/>',
            f'<line x1="{PAD}" y1="{PAD}" x2="{PAD}" y2="{H-PAD}" stroke="{GRID}"/>']


def _ticks(sx, sy, xr, yr):
    out = []
    for i in range(5):
        xv = xr[0]+(xr[1]-xr[0])*i/4
        yv = yr[0]+(yr[1]-yr[0])*i/4
        out.append(f'<text x="{sx(xv):.1f}" y="{H-PAD+16}" text-anchor="middle" fill="{MUTED}">{xv:.3g}</text>')
        out.append(f'<text x="{PAD-6}" y="{sy(yv)+4:.1f}" text-anchor="end" fill="{MUTED}">{yv:.3g}</text>')
    return out


def demand_support(events, frame):
    s = [e.entry_speed for e in events]
    a = [e.turn_angle for e in events]
    xr, yr = (min(s), max(s)), (0.0, 180.0)
    sx, sy = _scale(*xr, PAD, W-PAD/2), _scale(*yr, H-PAD, PAD)
    out = _frame("Observed turn demands (all athletes)", "entry speed (yd/s)", "turn angle (deg)")+_ticks(sx, sy, xr, yr)
    for x, y in zip(s, a):
        out.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="2.5" fill="{A}" fill-opacity="0.45"/>')
    return "\n".join(out+["</svg>"])


def event_trace(event, attempt):
    path = smooth(attempt.frames, 3)
    vel = velocities(path)
    t = [p[0] for p in path]
    sp = [hypot(*v) for v in vel]
    xr, yr = (t[0], t[-1]), (0.0, max(sp)*1.1)
    sx, sy = _scale(*xr, PAD, W-PAD/2), _scale(*yr, H-PAD, PAD)
    out = _frame(f"Detected turn, {event.drill}: speed trace and recovery window", "time (s)", "speed (yd/s)")+_ticks(sx, sy, xr, yr)
    tp = t[event.plant_index]
    out.append(f'<rect x="{sx(tp):.1f}" y="{PAD}" width="{sx(tp+RECOVERY)-sx(tp):.1f}" height="{H-2*PAD}" fill="{B}" fill-opacity="0.15"/>')
    out.append('<polyline fill="none" stroke="%s" stroke-width="2" points="%s"/>' % (
        A, " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in zip(t, sp))))
    out.append(f'<text x="{sx(tp)+4:.1f}" y="{PAD+14}" fill="{B}">recovery window, eta={event.eta:.3f}</text>')
    return "\n".join(out+["</svg>"])


def predictive_comparison(folds):
    rows = [(pb, pm, y) for f in folds for pb, pm, y in zip(f["baseline"]["pred"], f["movement"]["pred"], f["y_test"])]
    vals = [v for r in rows for v in r]
    lo, hi = min(vals), max(vals)
    sx, sy = _scale(lo, hi, PAD, W-PAD/2), _scale(lo, hi, H-PAD, PAD)
    out = _frame("Held-out target vs prediction", "prediction", "context-adjusted target")+_ticks(sx, sy, (lo, hi), (lo, hi))
    out.append(f'<line x1="{sx(lo):.1f}" y1="{sy(lo):.1f}" x2="{sx(hi):.1f}" y2="{sy(hi):.1f}" stroke="{GRID}" stroke-dasharray="4 4"/>')
    for pb, pm, y in rows:
        out.append(f'<circle cx="{sx(pb):.1f}" cy="{sy(y):.1f}" r="3" fill="none" stroke="{MUTED}"/>')
        out.append(f'<circle cx="{sx(pm):.1f}" cy="{sy(y):.1f}" r="3" fill="{A}" fill-opacity="0.7"/>')
    out.append(f'<text x="{W-PAD-150}" y="{PAD+4}" fill="{MUTED}">○ baseline</text>')
    out.append(f'<text x="{W-PAD-150}" y="{PAD+20}" fill="{A}">● with movement readout</text>')
    return "\n".join(out+["</svg>"])


def write_figures(out, events, folds, frame, attempts=()):
    if events:
        (out/"fig_demand_support.svg").write_text(demand_support(events, frame))
        by_id = {a.attempt_id: a for a in attempts}
        e = sorted(events, key=lambda e: e.sensitivity)[len(events)//2]
        if e.attempt_id in by_id:
            (out/"fig_event_trace.svg").write_text(event_trace(e, by_id[e.attempt_id]))
    if folds:
        (out/"fig_predictive_comparison.svg").write_text(predictive_comparison(folds))
