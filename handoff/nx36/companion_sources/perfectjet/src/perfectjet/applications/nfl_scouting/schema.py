"""Data contracts, source manifests, and availability rules.

Every derived quantity carries its lineage: athlete, attempt, drill, frame range,
units, extraction version, and the date it became available. A pre-draft model
may use a quantity only if it was available on or before the decision date.
NFL tracking may define the outcome; it never enters a Combine-only predictor.
"""
import csv
import hashlib
import json
from math import isfinite
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path


@dataclass
class Frame:
    t: float  # seconds
    x: float  # yards
    y: float  # yards


@dataclass
class Attempt:
    athlete_id: str
    attempt_id: str
    drill: str
    frames: list
    recorded_on: str  # ISO date


@dataclass
class Athlete:
    athlete_id: str
    position: str
    draft_year: int
    measurements: dict  # name -> value; pre-draft only
    available_on: dict  # name -> ISO date the measurement existed
    bootstrap_group: str | None = None  # original athlete; copies remain together in every split


@dataclass
class Play:
    athlete_id: str
    season: int
    play_id: str
    outcome: float  # e.g. get-off in seconds; see outcome_definition
    context: dict  # permitted NFL context used only for outcome normalization


@dataclass
class Lineage:
    athlete_id: str
    attempt_id: str
    drill: str
    frame_range: tuple
    time_range: tuple
    units: str
    extraction_version: str
    available_on: str
    branch: dict = field(default_factory=dict)


@dataclass
class Dataset:
    athletes: dict
    attempts: list
    plays: list
    manifest: dict
    outcome_definition: dict
    synthetic: bool = False


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def available(record_date, decision_date):
    return date.fromisoformat(record_date) <= date.fromisoformat(decision_date)


def admissible_measurements(athlete, decision_date, allowed):
    """Measurements in the allowed list that existed by the decision date; the rest are reported."""
    use, rejected = {}, []
    for name in allowed:
        if name not in athlete.measurements:
            continue
        when = athlete.available_on.get(name)
        if when is None or not available(when, decision_date):
            rejected.append(name)
        else:
            use[name] = athlete.measurements[name]
    return use, rejected


def admissible_events(athlete, events, decision_date):
    """Keep only Combine events known at the declared pre-draft decision date."""
    keep, rejected = [], []
    for event in events:
        when = event.lineage.available_on
        if when is not None and available(when, decision_date):
            keep.append(event)
        else:
            rejected.append(event.attempt_id)
    return keep, rejected


DEFAULT_MAPPING = {
    "tracking": {"file": "tracking.csv", "athlete_id": "athlete_id", "attempt_id": "attempt_id",
                 "drill": "drill", "t": "t", "x": "x", "y": "y", "recorded_on": "recorded_on"},
    "athletes": {"file": "athletes.csv", "athlete_id": "athlete_id", "position": "position",
                 "draft_year": "draft_year", "measurements": ["height", "weight", "forty", "vertical", "broad",
                                                              "three_cone", "shuttle", "bench"],
                 "available_on": "measured_on"},
    "plays": {"file": "plays.csv", "athlete_id": "athlete_id", "season": "season", "play_id": "play_id",
              "outcome": "get_off", "context": ["alignment", "down", "distance", "pass_play"]},
    "outcome_definition": {"name": "get_off", "units": "seconds",
                           "meaning": "UNCONFIRMED: verify what the supplied variable measures before calling it reaction time",
                           "eligible_play": "defensive-front snap with tracked first movement",
                           "minimum_plays": 20, "lower_is_better": True}
}


def _float(v):
    try:
        out = float(v)
        return out if isfinite(out) else None
    except (TypeError, ValueError):
        return None


def load_directory(root, mapping=None):
    """Read tracking, athletes and plays CSVs through a declared column mapping, with a hash manifest."""
    root = Path(root)
    m = mapping or DEFAULT_MAPPING
    manifest = {}
    for part in ("tracking", "athletes", "plays"):
        p = root/m[part]["file"]
        manifest[m[part]["file"]] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    tm, am, pm = m["tracking"], m["athletes"], m["plays"]
    groups = {}
    with open(root/tm["file"], newline="") as f:
        for r in csv.DictReader(f):
            key = (r[tm["athlete_id"]], r[tm["attempt_id"]])
            g = groups.setdefault(key, {"drill": r[tm["drill"]], "recorded_on": r[tm["recorded_on"]], "frames": []})
            g["frames"].append(Frame(float(r[tm["t"]]), float(r[tm["x"]]), float(r[tm["y"]])))
    attempts = [Attempt(a, b, g["drill"], sorted(g["frames"], key=lambda fr: fr.t), g["recorded_on"])
                for (a, b), g in sorted(groups.items())]
    athletes = {}
    with open(root/am["file"], newline="") as f:
        for r in csv.DictReader(f):
            meas = {k: _float(r.get(k)) for k in am["measurements"] if _float(r.get(k)) is not None}
            when = r.get(am["available_on"])
            athletes[r[am["athlete_id"]]] = Athlete(r[am["athlete_id"]], r[am["position"]], int(r[am["draft_year"]]),
                                                    meas, {k: when for k in meas})
    plays = []
    with open(root/pm["file"], newline="") as f:
        for r in csv.DictReader(f):
            y = _float(r[pm["outcome"]])
            if y is None:
                continue
            ctx = {k: _float(r.get(k)) if _float(r.get(k)) is not None else r.get(k) for k in pm["context"]}
            plays.append(Play(r[pm["athlete_id"]], int(r[pm["season"]]), r[pm["play_id"]], y, ctx))
    return Dataset(athletes, attempts, plays, manifest, m["outcome_definition"])


def audit_joins(ds):
    """Identity and chronology audit: unmatched ids, plays before draft year, attempts after the draft."""
    tracked = {a.athlete_id for a in ds.attempts}
    played = {p.athlete_id for p in ds.plays}
    known = set(ds.athletes)
    early = [p.play_id for p in ds.plays if p.athlete_id in ds.athletes and p.season < ds.athletes[p.athlete_id].draft_year]
    late = [a.attempt_id for a in ds.attempts if a.athlete_id in ds.athletes
            and not available(a.recorded_on, f"{ds.athletes[a.athlete_id].draft_year}-04-20")]
    return {"athletes": len(known), "tracked_unknown": sorted(tracked-known), "played_unknown": sorted(played-known),
            "tracked_never_played": len((tracked & known)-played), "played_never_tracked": len((played & known)-tracked),
            "plays_before_draft": early[:20], "n_plays_before_draft": len(early),
            "attempts_after_draft": late[:20], "n_attempts_after_draft": len(late),
            "attempts_after_decision_date": late[:20], "n_attempts_after_decision_date": len(late),
            "decision_date_rule": "April 20 of draft year"}


def to_json(obj):
    def enc(o):
        if hasattr(o, "__dataclass_fields__"):
            return asdict(o)
        if isinstance(o, tuple):
            return list(o)
        return str(o)
    return json.dumps(obj, indent=2, default=enc)
