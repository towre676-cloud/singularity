"""Stream official NFL tracking into operational movement *targets*.

This module never creates pre-draft predictor measurements.  Snap-to-LOS is the
supplied primary outcome; its tracked decomposition is a separate, quality-
filtered diagnostic.  Motion onset is a sustained-motion tracking proxy, not
physiological reaction time.  Distances are yards and durations are seconds.

Two sequential scans per requested season first find unique snap observations,
then retain only selected athlete/play windows.  Full-game trajectories are
never accumulated.  Records retain failures and counts, so missing tracking
does not silently become a zero target or a favorable player profile.
"""

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from math import hypot, isfinite
from pathlib import Path

from .crossing import extract_crossing
from .official import _number, _rows, _timestamp, exact_id
from .schema import Frame


EXTRACTION_VERSION = "official-nfl-movement-targets-1"
DEFAULT_CHANNELS = ("onset_delay", "motion_to_los", "forward_displacement_05")
CHANNEL_UNITS = {
    "onset_delay": "seconds", "motion_to_los": "seconds",
    "forward_displacement_05": "yards", "directional_retention_05": "dimensionless",
    "forward_path_fraction_05": "dimensionless", "forward_speed_05": "yards/second",
    "tracked_snap_to_los": "seconds",
}


@dataclass
class MovementTargetRecord:
    athlete_id: str
    season: int
    play_id: str
    game_id: str
    supplied_get_off: float
    context: dict
    channels: dict = field(default_factory=dict)
    frames: list = field(default_factory=list)
    flags: list = field(default_factory=list)
    usable: bool = False
    usable_for_post_snap_onset: bool = False
    lineage: dict = field(default_factory=dict)


@dataclass
class MovementTargetDataset:
    records: list
    audit: dict
    manifest: dict


def _id(value, name="id", allow_empty=False):
    """Fast common IDs, with exact decimal parsing for noncanonical forms."""
    text = str(value).strip()
    if text.isdecimal():
        return str(int(text))
    return exact_id(text, name, allow_empty)


def _play_key(play):
    parts = str(play.play_id).split(":")
    if len(parts) != 2:
        raise ValueError("official movement target requires a game_id:play_id key")
    return (_id(parts[0], "game_id"), _id(parts[1], "play_id"),
            _id(play.athlete_id, "nfl_id"))


def select_target_plays(dataset, athlete_ids=None, season_before=None):
    """Select past athlete plays, with an explicit-ID future-season guard.

    ``season_before=2025`` retains NFL target seasons less than 2025 when all
    athletes are requested. Explicit athlete IDs activate a strict guard: a
    requested athlete's future target raises instead of silently entering fit.
    A held-out target extraction can omit the guard; it still cannot be used as
    a prospect input.  This does not establish that a dataset is an untouched
    holdout: historical inspections remain the caller's responsibility.
    """
    if season_before is not None:
        season_before = int(_id(season_before, "season_before"))
    ids = None if athlete_ids is None else {_id(aid) for aid in athlete_ids}
    selected = {}
    for play in dataset.plays:
        if ids is not None and _id(play.athlete_id) not in ids:
            continue
        if season_before is not None and play.season >= season_before:
            if ids is not None:
                raise ValueError("future NFL target season reaches or exceeds training cutoff")
            continue
        key = _play_key(play)
        if key in selected:
            raise ValueError(f"duplicate target player/play identity: {key!r}")
        if key[2] not in dataset.athletes:
            raise ValueError(f"target athlete absent from dataset: {key[2]}")
        if play.season != dataset.athletes[key[2]].draft_year:
            raise ValueError("movement target is not a rookie-season observation")
        selected[key] = play
    return selected


def _line_geometry(row):
    """Official field x convention and defensive forward direction toward LOS."""
    yardline = _number(row.get("yardline_number"))
    direction = row.get("play_direction", "").strip().lower()
    side = row.get("yardline_side", "").strip()
    possession = row.get("possession_team", "").strip()
    if yardline is None or not 0 <= yardline <= 50 or direction not in ("left", "right"):
        raise ValueError("invalid_los_geometry")
    if not side or not possession:
        raise ValueError("missing_yardline_side")
    yards = yardline if side == possession else 100-yardline
    right = direction == "right"
    los_x = 10+yards if right else 110-yards
    return (los_x, 0.0), ((-1.0, 0.0) if right else (1.0, 0.0))


def extract_movement_record(play, frames, snap_time, los_point, forward_axis,
                            extraction_kwargs=None):
    """Extract from tracked geometry; covariant under rotations/reflections.

    ``forward_axis`` must point from the defensive start side toward the line.
    Canonical record frames have t relative to snap, x projected toward LOS,
    and y along the perpendicular axis, both relative to the snap position.
    A nonpositive starting depth is excluded rather than abs()-flipped into a
    different movement task.  The supplied primary target is always retained.
    """
    key = _play_key(play)
    record = MovementTargetRecord(key[2], play.season, play.play_id, key[0],
                                  play.outcome, dict(play.context))
    ordered = sorted(frames, key=lambda f: f.t)
    try:
        snap = float(snap_time)
        ux, uy = map(float, forward_axis)
        lx, ly = map(float, los_point)
    except (ValueError, TypeError):
        raise ValueError("finite snap, LOS point and forward axis required") from None
    length = hypot(ux, uy)
    if not all(isfinite(v) for v in (snap, ux, uy, lx, ly)) or length == 0:
        raise ValueError("finite snap, LOS point and nonzero forward axis required")
    ux, uy = ux/length, uy/length
    if not ordered or any(not all(isfinite(float(v)) for v in (f.t, f.x, f.y)) for f in ordered):
        record.flags.append("missing_or_nonfinite_tracking")
        return record
    if any(b.t <= a.t for a, b in zip(ordered, ordered[1:])):
        record.flags.append("duplicate_tracking_timestamp")
        return record
    snap_frames = [f for f in ordered if abs(f.t-snap) <= 1e-8]
    if len(snap_frames) != 1:
        record.flags.append("missing_or_nonunique_snap_frame")
        return record
    origin = snap_frames[0]
    depth = (lx-origin.x)*ux+(ly-origin.y)*uy
    record.lineage = {
        "extraction_version": EXTRACTION_VERSION, "target_only": True,
        "reaction_time_interpretation": False, "snap_time": snap,
        "raw_snap_position": [origin.x, origin.y], "los_point": [lx, ly],
        "forward_axis": [ux, uy], "distance_to_los": depth,
        "channel_units": dict(CHANNEL_UNITS),
        "context_scope": "NFL outcome normalization only; unavailable prospect input",
    }
    record.frames = [Frame(f.t-snap, (f.x-origin.x)*ux+(f.y-origin.y)*uy,
                           -(f.x-origin.x)*uy+(f.y-origin.y)*ux) for f in ordered]
    record.lineage["observed_time_range_relative_snap"] = [record.frames[0].t, record.frames[-1].t]
    if depth <= 0:
        record.flags.append("snap_not_on_defensive_side_of_los")
        return record
    kwargs = dict(extraction_kwargs or {})
    reserved = {"axis", "direction", "snap_time", "distance_los", "frames_or_attempt"}
    if reserved.intersection(kwargs):
        raise ValueError("geometry/snap arguments cannot be overridden in extraction_kwargs")
    horizon = kwargs.get("post_onset_horizon", 0.5)
    if abs(float(horizon)-0.5) > 1e-12:
        raise ValueError("named half-second channels require a 0.5 second horizon")
    result = extract_crossing(record.frames, 0.0, depth, **kwargs)
    record.flags = list(result["flags"])
    record.usable = result["usable"]
    record.usable_for_post_snap_onset = result["usable_for_post_snap_onset"]
    record.lineage["crossing_assumptions"] = result["assumptions"]
    record.lineage["reconstruction_identity_error"] = result["reconstruction_identity_error"]
    if result["snap_to_los"] is not None:
        record.lineage["supplied_minus_tracked_get_off"] = play.outcome-result["snap_to_los"]
    if not record.usable:
        return record
    record.channels = {
        "onset_delay": result["onset_delay"], "motion_to_los": result["motion_to_los"],
        "forward_displacement_05": result["post_onset_displacement"],
        "tracked_snap_to_los": result["snap_to_los"],
    }
    onset, end = result["motion_onset_time"], result["motion_onset_time"]+0.5
    path = 0.0
    for a, b in zip(record.frames, record.frames[1:]):
        lo, hi = max(a.t, onset), min(b.t, end)
        if hi > lo:
            path += hypot(b.x-a.x, b.y-a.y)*(hi-lo)/(b.t-a.t)
    if path > 0:
        record.channels["forward_path_fraction_05"] = result["post_onset_displacement"]/path
    # The finite-interval endpoint velocity avoids a second derivative. At an
    # exact endpoint use the immediately preceding interval; otherwise use the
    # bracket containing it. This readout is a tracking proxy, not an exact
    # instantaneous physical velocity. A gap cannot yield a retention channel.
    maximum_gap = kwargs.get("maximum_gap", 0.15)
    for a, b in zip(record.frames, record.frames[1:]):
        if a.t < end <= b.t+1e-10:
            dt = b.t-a.t
            if dt <= maximum_gap+1e-9:
                forward_speed = (b.x-a.x)/dt
                total_speed = hypot(b.x-a.x, b.y-a.y)/dt
                record.channels["forward_speed_05"] = forward_speed
                if total_speed > 1e-12:
                    record.channels["directional_retention_05"] = forward_speed/total_speed
                record.lineage["endpoint_velocity_interval_relative_snap"] = [a.t, b.t]
            break
    return record


def load_movement_targets(root, dataset, *, athlete_ids=None, season_before=None,
                          window=(-0.5, 2.5), extraction_kwargs=None,
                          maximum_frames_per_record=128):
    """Two-pass stream of selected official trajectories with explicit rejects.

    The requested plays come from the official adapter and are independently
    rechecked against games/player_play metadata.  Every requested play gets a
    record, including invalid/missing windows.  Only selected, in-window frames
    enter memory, capped per record even for malformed duplicate-heavy input.
    """
    if len(window) != 2:
        raise ValueError("window must bracket the snap with finite endpoints")
    window = tuple(map(float, window))
    if not all(isfinite(t) for t in window) or not window[0] < 0 < window[1]:
        raise ValueError("window must bracket the snap with finite endpoints")
    if isinstance(maximum_frames_per_record, bool) or int(maximum_frames_per_record) != maximum_frames_per_record or maximum_frames_per_record < 2:
        raise ValueError("maximum_frames_per_record must be at least two")
    if season_before is not None:
        season_before = int(_id(season_before, "season_before"))
    selected = select_target_plays(dataset, athlete_ids, season_before)
    root = Path(root)
    audit = {"requested_records": len(selected), "metadata_rejections": Counter(),
             "tracking_rejections": Counter(), "rows_scanned_pass1": Counter(),
             "rows_scanned_pass2": Counter(), "retained_window_frames": 0,
             "maximum_retained_frames_per_record": 0, "quality_flags": Counter()}
    audit["cutoff_excluded_records"] = sum(
        play.season >= season_before for play in dataset.plays) if season_before is not None and athlete_ids is None else 0
    games = {}
    for row in _rows(root/"games.csv", ("game_id", "season", "season_type")):
        gid = _id(row["game_id"], "game_id")
        if gid in games:
            raise ValueError(f"games.csv: duplicate identity {gid!r}")
        games[gid] = row
    metadata, invalid = {}, {}
    columns = ("game_id", "play_id", "nfl_id", "play_nullified_by_penalty",
               "yardline_number", "yardline_side", "possession_team", "play_direction")
    for row in _rows(root/"player_play.csv", columns):
        aid = _id(row["nfl_id"], "nfl_id", True)
        if aid is None:
            continue
        key = (_id(row["game_id"], "game_id"), _id(row["play_id"], "play_id"), aid)
        if key not in selected:
            continue
        if key in metadata or key in invalid:
            raise ValueError(f"player_play.csv: duplicate selected identity {key!r}")
        try:
            game = games.get(key[0])
            if game is None:
                raise ValueError("missing_game_metadata")
            season = int(_id(game["season"], "season"))
            if season != selected[key].season or season != dataset.athletes[aid].draft_year:
                raise ValueError("not_rookie_season")
            if game["season_type"].strip() != "REG":
                raise ValueError("not_regular_season")
            if row["play_nullified_by_penalty"].strip() != "N":
                raise ValueError("nullified_or_unknown_penalty")
            metadata[key] = (season, *_line_geometry(row))
        except ValueError as exc:
            invalid[key] = str(exc)
            audit["metadata_rejections"][str(exc)] += 1
    for key in selected.keys()-metadata.keys()-invalid.keys():
        invalid[key] = "missing_player_play_metadata"
        audit["metadata_rejections"][invalid[key]] += 1
    keys_by_year = defaultdict(set)
    for key, (year, _, _) in metadata.items():
        keys_by_year[year].add(key)
    snaps, frame_groups = {}, defaultdict(list)
    bad_snap, overflow, malformed = set(), set(), set()
    file_lineage = {}
    tracking_columns = ("game_id", "play_id", "nfl_id", "event", "time", "x", "y")
    for year, keys in sorted(keys_by_year.items()):
        path = root/f"game_tracking_{year}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Official movement tracking missing: {path.name}")
        counts = Counter()
        candidate_ids = {key[2] for key in keys}
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            if not set(tracking_columns).issubset(header):
                raise ValueError(f"{path.name}: missing movement tracking columns")
            ix = {name: header.index(name) for name in tracking_columns}
            for row in reader:
                audit["rows_scanned_pass1"][str(year)] += 1
                if row[ix["event"]] != "ball_snap":
                    continue
                aid = _id(row[ix["nfl_id"]], "nfl_id", True)
                if aid not in candidate_ids:
                    continue
                key = (_id(row[ix["game_id"]], "game_id"), _id(row[ix["play_id"]], "play_id"), aid)
                if key not in keys:
                    continue
                counts[key] += 1
                try:
                    stamp = _timestamp(row[ix["time"]])
                    # An NFL season crosses the calendar-year boundary. The
                    # authoritative REG/season selection is games.csv; January
                    # (and plausible early-February) dates belong to season+1.
                    if stamp.year != year and not (stamp.year == year+1 and stamp.month <= 2):
                        raise ValueError("tracking_timestamp_season_mismatch")
                    snaps[key] = stamp
                except ValueError:
                    bad_snap.add(key)
        for key in keys:
            if counts[key] != 1 or key in bad_snap:
                reason = "missing_snap_record" if counts[key] == 0 else "nonunique_or_invalid_snap_record"
                invalid[key] = reason
                audit["tracking_rejections"][reason] += 1
                snaps.pop(key, None)
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            ix = {name: header.index(name) for name in tracking_columns}
            for row in reader:
                audit["rows_scanned_pass2"][str(year)] += 1
                aid = _id(row[ix["nfl_id"]], "nfl_id", True)
                if aid not in candidate_ids:
                    continue
                key = (_id(row[ix["game_id"]], "game_id"), _id(row[ix["play_id"]], "play_id"), aid)
                if key not in snaps or key in overflow:
                    continue
                try:
                    stamp = _timestamp(row[ix["time"]])
                    if (stamp.tzinfo is None) != (snaps[key].tzinfo is None):
                        raise ValueError("mixed_timestamp_timezones")
                except ValueError:
                    malformed.add(key)
                    continue
                relative = (stamp-snaps[key]).total_seconds()
                if not window[0]-1e-8 <= relative <= window[1]+1e-8:
                    continue
                x, y = _number(row[ix["x"]]), _number(row[ix["y"]])
                if x is None or y is None:
                    malformed.add(key)
                    continue
                if len(frame_groups[key]) >= maximum_frames_per_record:
                    overflow.add(key)
                    frame_groups.pop(key, None)
                    continue
                frame_groups[key].append(Frame(relative, x, y))
                audit["retained_window_frames"] += 1
        file_lineage[path.name] = dict(dataset.manifest.get(path.name, {}))
    records = []
    for key, play in sorted(selected.items()):
        reason = invalid.get(key)
        if key in overflow:
            reason = "tracking_window_frame_limit_exceeded"
        if key in malformed:
            reason = "malformed_selected_tracking"
        if reason:
            record = MovementTargetRecord(key[2], play.season, play.play_id, key[0],
                                          play.outcome, dict(play.context), flags=[reason])
        else:
            _, line, axis = metadata[key]
            record = extract_movement_record(play, frame_groups.get(key, []), 0.0,
                                              line, axis, extraction_kwargs)
            record.lineage["raw_snap_timestamp"] = snaps[key].isoformat()
        record.lineage.update({"extraction_version": EXTRACTION_VERSION, "target_only": True,
                               "source_file": f"game_tracking_{play.season}.csv",
                               "player_play_key": list(key), "window_relative_snap": list(window),
                               "supplied_primary_outcome_retained": True})
        audit["maximum_retained_frames_per_record"] = max(
            audit["maximum_retained_frames_per_record"], len(record.frames))
        audit["quality_flags"].update(record.flags)
        records.append(record)
    audit["usable_records"] = sum(record.usable for record in records)
    audit["usable_post_snap_onset_records"] = sum(record.usable_for_post_snap_onset for record in records)
    audit["usable_athletes"] = len({record.athlete_id for record in records if record.usable})
    for name, value in tuple(audit.items()):
        if isinstance(value, Counter):
            audit[name] = dict(value)
    return MovementTargetDataset(records, audit, {
        "version": EXTRACTION_VERSION, "synthetic": dataset.synthetic,
        "target_only": True, "files": file_lineage, "season_before": season_before,
        "channels": dict(CHANNEL_UNITS), "coordinate_frame": "snap-relative forward/perpendicular yards",
        "onset_interpretation": "sustained forward-motion proxy; not physiological reaction time",
        "population_scope": "quality-filtered tracked decomposition among supplied eligible get-off records",
        "primary_outcome": "supplied player_get_off; not replaced by an intermediate movement target",
    })


def summarize_movement_targets(records, channels=DEFAULT_CHANNELS, *, minimum_plays=1,
                                minimum_games=2, weights=None, residuals=None,
                                require_post_snap_onset=False):
    """Joint-support player means and game-cluster covariance of those means.

    Weights map ``(athlete_id, play_id)`` to nonnegative play weights; defaults
    are equal play weights.  Optional residuals use the same key and contain
    channel values already computed by a training-only context model.  This
    module does not fit that model.  The covariance is the finite-game corrected
    cluster sandwich, G/(G-1) sum_g S_g S_g', where S_g is the weighted residual
    sum and weights sum to one.  With fewer than two games covariance is unknown,
    never zero.  Components use one common complete-case support; marginal
    availability is separately reported.  No cross-player precision is invented.
    """
    channels = tuple(channels)
    if not channels or len(set(channels)) != len(channels) or any(c not in CHANNEL_UNITS for c in channels):
        raise ValueError("unique known movement channels required")
    if minimum_plays < 1 or minimum_games < 1:
        raise ValueError("positive minimum play/game counts required")
    records = list(records)
    groups, all_counts, available_counts = defaultdict(list), Counter(), defaultdict(Counter)
    seen = set()
    for record in records:
        key = (record.athlete_id, record.play_id)
        if key in seen:
            raise ValueError("duplicate player/play in movement summary")
        seen.add(key)
        aid = record.athlete_id
        all_counts[aid] += 1
        values = record.channels if residuals is None else residuals.get(key, {})
        for channel in channels:
            value = values.get(channel)
            if value is not None and isfinite(float(value)):
                available_counts[aid][channel] += 1
        if not record.usable or (require_post_snap_onset and not record.usable_for_post_snap_onset):
            continue
        row = [values.get(channel) for channel in channels]
        if any(value is None or not isfinite(float(value)) for value in row):
            continue
        weight = 1.0 if weights is None else float(weights.get(key, 0.0))
        if not isfinite(weight) or weight < 0:
            raise ValueError("finite nonnegative summary weights required")
        if weight:
            groups[aid].append((record.game_id, list(map(float, row)), weight))
    result = {}
    for aid in sorted(all_counts):
        rows = groups[aid]
        n, games = len(rows), len({game for game, _, _ in rows})
        total = sum(weight for _, _, weight in rows)
        means = [sum(weight*row[j] for _, row, weight in rows)/total
                 for j in range(len(channels))] if total else None
        covariance = None
        if games >= 2:
            scores = defaultdict(lambda: [0.0]*len(channels))
            for game, row, weight in rows:
                for j in range(len(channels)):
                    scores[game][j] += weight/total*(row[j]-means[j])
            covariance = [[games/(games-1)*sum(score[i]*score[j] for score in scores.values())
                           for j in range(len(channels))] for i in range(len(channels))]
        result[aid] = {
            "channels": list(channels), "mean": means, "covariance": covariance,
            "n_plays": n, "n_games": games, "requested_plays": all_counts[aid],
            "channel_available_counts": dict(available_counts[aid]),
            "eligible": n >= minimum_plays and games >= minimum_games,
            "precision_identified": covariance is not None,
            "effective_play_count": total*total/sum(weight*weight for _, _, weight in rows) if total else 0.0,
            "target_only": True, "context_adjusted": residuals is not None,
            "uncertainty_scope": "game-cluster sampling covariance conditional on supplied context residuals; excludes context-model fitting uncertainty",
        }
    return result
