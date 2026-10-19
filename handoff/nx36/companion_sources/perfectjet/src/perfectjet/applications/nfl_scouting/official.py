"""Read the nine official Big Data Bowl 2027 CSVs into the scouting contract.

This is a real-data adapter, not an acquisition service or a synthetic fallback.
The supplied ``player_get_off`` is snap-to-line-of-scrimmage crossing time in
seconds. It is not a reaction-time measurement. Game features are outcome
context only; athlete predictors come exclusively from Combine observations.
"""

import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from math import isfinite
from pathlib import Path

from .schema import Athlete, Attempt, Dataset, Frame, Play, sha256_file


OFFICIAL_FILES = (
    "combine_results.csv", "combine_tracking.csv", "game_tracking_2023.csv",
    "game_tracking_2024.csv", "game_tracking_2025.csv", "games.csv",
    "player_career_successes.csv", "player_play.csv", "players.csv",
)
KNOWN_SHA256 = {
    "combine_results.csv": "e4773ef68167d508f3916d446cd411dfd77a87e5765d3babcb986201fb143b86",
    "combine_tracking.csv": "541c69f6629f5f803b08033c5c386735582120973562134b2c1e7ec6553fb0d3",
    "game_tracking_2023.csv": "385e620b6b94e8cd91f0d5776395b76b10d52a34401c764c21b4e98ab617855c",
    "game_tracking_2024.csv": "06b7f34304414306dab53d5cb4c5d28485c5f62376442bcb913f9f01184ece6d",
    "game_tracking_2025.csv": "419b6bc0388a9210f61911ec2f1351b1e8d56355c0ac8576f24a3bbcd95e54ca",
    "games.csv": "ca33543f6939af4ee393c568c60920c476ba91ddbfbdce5a06578b9492fa11fd",
    "player_career_successes.csv": "0d4b8975debda4e2481218f30a16429dad5b806ecdd2fc4367291ac1460ed0a9",
    "player_play.csv": "68926a268c0a49e58616001fb35ea179018d9cbbce1c5c31e7a4095273c35b2a",
    "players.csv": "2cd7e0309e7aa40533028dc537c2c877dbedbe0fdb14f337fc18af31a5861c12",
}
FRONT_POSITIONS = ("DE", "DT", "NT", "OLB", "EDGE", "DL")
FRONT_DRILLS = (
    "PASS_RUSH_DRILL", "RUN_THE_HOOP_DRILL", "FOUR_BAG_AGILITY_DRILL",
    "FRONT_START_WAVE_DRILL_AND_LATERAL_REACTION", "FORTY_YARD_DASH",
)
# All fifteen source measurements remain accessible to stronger comparators.
# Names shared with the existing eight-variable comparator are standardized.
MEASUREMENT_COLUMNS = {
    "combine_height": "height", "combine_weight": "weight",
    "hand_size": "hand_size", "arm_length": "arm_length", "wing_span": "wing_span",
    "ten_yd_split": "ten_yd_split", "forty": "forty", "vertical": "vertical",
    "broad_jump": "broad", "three_cone": "three_cone", "short_shuttle": "shuttle",
    "bench_reps": "bench", "ngs_athleticism_score": "ngs_athleticism_score",
    "ngs_college_production_score": "ngs_college_production_score",
    "ngs_final_score": "ngs_final_score",
}
NUMERIC_CONTEXT = (
    "down", "yards_to_go", "yardline_number", "quarter", "pre_snap_home_score",
    "pre_snap_visitor_score",
)
CATEGORICAL_CONTEXT = (
    "lined_up_position", "offense_formation", "blitzing", "team_abbr", "possession_team",
)


def exact_id(value, name="id", allow_empty=False):
    """Canonical integer identifiers without the precision loss of a float join."""
    value = str(value).strip()
    if value.lower() in ("", "nan", "na", "null"):
        if allow_empty:
            return None
        raise ValueError(f"missing {name}")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid {name}: {value!r}") from exc
    if not number.is_finite() or number != number.to_integral_value() or number < 0:
        raise ValueError(f"noninteger {name}: {value!r}")
    return str(int(number))


def _number(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if isfinite(value) else None


def _rows(path, required):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        absent = sorted(set(required) - set(reader.fieldnames or ()))
        if absent:
            raise ValueError(f"{Path(path).name}: missing columns {', '.join(absent)}")
        yield from reader


def _unique(rows, key_function, name):
    result = {}
    for row in rows:
        key = key_function(row)
        if key in result:
            raise ValueError(f"{name}: duplicate identity {key!r}")
        result[key] = row
    return result


def official_manifest(root, verify_known_hashes=False):
    """Hash all nine files; optionally require the retained official snapshot."""
    root = Path(root)
    missing = [name for name in OFFICIAL_FILES if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError("Official Big Data Bowl 2027 data missing: " + ", ".join(missing))
    result = {}
    for name in OFFICIAL_FILES:
        path = root / name
        digest = sha256_file(path)
        matches = digest == KNOWN_SHA256[name]
        if verify_known_hashes and not matches:
            raise ValueError(f"{name}: sha256 does not match retained official snapshot")
        result[name] = {
            "sha256": digest, "bytes": path.stat().st_size,
            "matches_retained_official_snapshot": matches,
        }
    return result


def _timestamp(value):
    """Parse the source clock without inventing an absent timezone.

    Official 2027 CSVs omit offsets. Their within-record time differences and
    source calendar dates remain usable. Offset-bearing inputs normalize to
    UTC; mixed naive/aware clocks within an attempt are rejected separately.
    """
    try:
        stamp = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError("invalid_timestamp") from exc
    return stamp if stamp.tzinfo is None else stamp.astimezone(timezone.utc)


def _load_attempts(root, combine, players, drills, positions, minimum_frames, audit):
    groups = defaultdict(list)
    candidate = {
        key for key, row in combine.items()
        if row["combine_position"].strip().upper() in positions and key[0] in players
    }
    columns = ("nfl_id", "draft_year", "event_id", "entity_type", "time", "drill_name", "x", "y")
    for row in _rows(root / "combine_tracking.csv", columns):
        if row["entity_type"].strip().upper() != "PLAYER" or row["drill_name"] not in drills:
            continue
        aid = exact_id(row["nfl_id"], "nfl_id", allow_empty=True)
        if aid is None:
            audit["source_rejections"]["player_frame_missing_id"] += 1
            continue
        if aid not in players:
            audit["unmatched_tracking_player_ids"].add(aid)
            continue
        year = int(exact_id(row["draft_year"], "draft_year"))
        if (aid, year) not in combine:
            audit["source_rejections"]["tracking_without_combine_result"] += 1
            continue
        if (aid, year) not in candidate:
            continue
        eid = row["event_id"].strip()
        if not eid:
            audit["source_rejections"]["missing_event_id"] += 1
            continue
        groups[(aid, year, eid)].append(row)
    attempts, dates = [], defaultdict(list)
    for (aid, year, eid), rows in sorted(groups.items()):
        try:
            if int(exact_id(players[aid]["draft_year"], "draft_year")) != year:
                raise ValueError("source_draft_year_mismatch")
            if len({row["drill_name"] for row in rows}) != 1:
                raise ValueError("inconsistent_attempt_drill")
            values = [(_timestamp(row["time"]), _number(row["x"]), _number(row["y"]))
                      for row in rows]
            if len({stamp.tzinfo is None for stamp, _, _ in values}) != 1:
                raise ValueError("mixed_timestamp_timezones")
            values.sort(key=lambda value: value[0])
            if len(values) < minimum_frames:
                raise ValueError("short_attempt")
            if any(x is None or y is None for _, x, y in values):
                raise ValueError("nonfinite_coordinates")
            if any(stamp.year != year or stamp.date().isoformat() > f"{year}-04-20"
                   for stamp, _, _ in values):
                raise ValueError("source_not_predraft")
            dt = [(b[0] - a[0]).total_seconds() for a, b in zip(values, values[1:])]
            if any(abs(step - 0.1) > 0.015 for step in dt):
                raise ValueError("duplicate_or_irregular_10hz_timestamps")
            t0 = values[0][0]
            frames = [Frame((stamp - t0).total_seconds(), x, y) for stamp, x, y in values]
            when = values[-1][0].date().isoformat()
            attempts.append(Attempt(aid, f"{year}:{eid}", rows[0]["drill_name"], frames, when))
            dates[aid].append(when)
        except ValueError as exc:
            audit["source_rejections"][str(exc)] += 1
    return attempts, {aid: max(when) for aid, when in dates.items()}


def _snap_rows(root, keys_by_year, audit):
    """One sequential scan per season, retaining only requested ball-snap rows."""
    result, counts = {}, Counter()
    for year in (2023, 2024, 2025):
        keys = keys_by_year.get(year, set())
        if not keys:
            continue
        path = root / f"game_tracking_{year}.csv"
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            required = ("event", "game_id", "play_id", "nfl_id", "x", "y", "s")
            if not set(required).issubset(header):
                raise ValueError(f"{path.name}: missing ball-snap columns")
            ix = {name: header.index(name) for name in required}
            for row in reader:
                if row[ix["event"]] != "ball_snap":
                    continue
                aid = exact_id(row[ix["nfl_id"]], "nfl_id", allow_empty=True)
                if aid is None:
                    continue
                key = (exact_id(row[ix["game_id"]], "game_id"),
                       exact_id(row[ix["play_id"]], "play_id"), aid)
                if key not in keys:
                    continue
                counts[key] += 1
                result[key] = tuple(_number(row[ix[name]]) for name in ("x", "y", "s"))
    requested = set().union(*keys_by_year.values()) if keys_by_year else set()
    audit["missing_snap_records"] = len(requested - set(counts))
    audit["nonunique_snap_records"] = sum(count != 1 for count in counts.values())
    return {key: result[key] for key, count in counts.items() if count == 1}


def _snap_context(row, snap):
    x, y, speed = snap
    yardline = _number(row.get("yardline_number"))
    direction = row.get("play_direction", "").strip().lower()
    if any(value is None for value in (x, y, speed, yardline)) or direction not in ("left", "right"):
        raise ValueError("invalid_snap_geometry")
    if not 0 <= yardline <= 50 or speed < 0:
        raise ValueError("invalid_snap_geometry")
    side, possession = row.get("yardline_side", ""), row.get("possession_team", "")
    if not side or not possession:
        raise ValueError("missing_yardline_side")
    yards = yardline if side == possession else 100 - yardline
    right = direction == "right"
    los = 10 + yards if right else 110 - yards
    return {"snap_depth": (x - los) * (1 if right else -1),
            "snap_width": abs(y - 80 / 3), "snap_speed": speed}


def load_official_directory(root, minimum_plays=30, verify_known_hashes=False,
                            include_snap_context=True, positions=FRONT_POSITIONS,
                            drills=FRONT_DRILLS, minimum_frames=16):
    """Return a real ``Dataset`` from the nine official CSVs.

    ``minimum_plays`` is reapplied after unique-snap and geometry exclusions.
    The default defensive-front cohort uses pre-draft ``combine_position``.
    NGS scores are exposed with explicitly unverified availability chronology;
    the latest valid tracked Combine date is a declared availability proxy for
    the fifteen measurements, not a claim about their exact release timestamps.
    ``include_snap_context=False`` defines a different, audited outcome context.
    """
    if minimum_plays < 1 or minimum_frames < 2:
        raise ValueError("minimum_plays must be positive and minimum_frames at least two")
    root = Path(root)
    manifest = official_manifest(root, verify_known_hashes)
    players = _unique(_rows(root / "players.csv", ("nfl_id", "draft_year")),
                      lambda row: exact_id(row["nfl_id"], "nfl_id"), "players.csv")
    combine = _unique(_rows(root / "combine_results.csv", ("nfl_id", "draft_year", "combine_position")),
                      lambda row: (exact_id(row["nfl_id"], "nfl_id"),
                                   int(exact_id(row["draft_year"], "draft_year"))), "combine_results.csv")
    games = _unique(_rows(root / "games.csv", ("game_id", "season", "season_type")),
                    lambda row: exact_id(row["game_id"], "game_id"), "games.csv")
    audit = {
        "source_rejections": Counter(), "play_rejections": Counter(),
        "unmatched_tracking_player_ids": set(), "unmatched_play_player_ids": set(),
        "unmatched_game_ids": set(), "positions": list(positions), "drills": list(drills),
    }
    attempts, measurement_dates = _load_attempts(root, combine, players, set(drills),
                                                 set(positions), minimum_frames, audit)
    athletes = {}
    for aid, when in measurement_dates.items():
        year = int(exact_id(players[aid]["draft_year"], "draft_year"))
        source = combine[(aid, year)]
        measurements = {target: value for col, target in MEASUREMENT_COLUMNS.items()
                        if (value := _number(source.get(col))) is not None}
        athletes[aid] = Athlete(aid, source["combine_position"].strip().upper(), year,
                                measurements, {name: when for name in measurements})
    selected, seen_keys = {}, set()
    required = ("game_id", "play_id", "nfl_id", "player_get_off", "play_nullified_by_penalty")
    for row in _rows(root / "player_play.csv", required):
        aid = exact_id(row["nfl_id"], "nfl_id", allow_empty=True)
        if aid is None:
            audit["play_rejections"]["missing_player_id"] += 1
            continue
        if aid not in players:
            audit["unmatched_play_player_ids"].add(aid)
            continue
        if aid not in athletes:
            continue
        gid, pid = exact_id(row["game_id"], "game_id"), exact_id(row["play_id"], "play_id")
        key = (gid, pid, aid)
        if key in seen_keys:
            raise ValueError(f"player_play.csv: duplicate identity {key!r}")
        seen_keys.add(key)
        if gid not in games:
            audit["unmatched_game_ids"].add(gid)
            continue
        game = games[gid]
        season = int(exact_id(game["season"], "season"))
        if season != athletes[aid].draft_year:
            audit["play_rejections"]["not_rookie_season"] += 1
            continue
        if game["season_type"].strip() != "REG":
            audit["play_rejections"]["not_regular_season"] += 1
            continue
        if row["play_nullified_by_penalty"].strip() != "N":
            audit["play_rejections"]["nullified_or_unknown_penalty"] += 1
            continue
        outcome = _number(row["player_get_off"])
        if outcome is None or outcome < 0:
            audit["play_rejections"]["nonfinite_or_negative_get_off"] += 1
            continue
        selected[key] = (row, season, outcome)
    counts = Counter(key[2] for key in selected)
    selected = {key: value for key, value in selected.items() if counts[key[2]] >= minimum_plays}
    audit["records_before_snap_exclusions"] = len(selected)
    snaps = {}
    if include_snap_context:
        keys_by_year = defaultdict(set)
        for key, (_, year, _) in selected.items():
            keys_by_year[year].add(key)
        snaps = _snap_rows(root, keys_by_year, audit)
    plays = []
    for key, (row, year, outcome) in sorted(selected.items()):
        context = {name: value for name in NUMERIC_CONTEXT if (value := _number(row.get(name))) is not None}
        context.update({name: row[name] for name in CATEGORICAL_CONTEXT if row.get(name, "").strip()})
        if include_snap_context:
            if key not in snaps:
                continue
            try:
                context.update(_snap_context(row, snaps[key]))
            except ValueError as exc:
                audit["play_rejections"][str(exc)] += 1
                continue
        # NFL position, outcome descendants and career totals are never supplied
        # to the Athlete record or to its predictor measurements.
        plays.append(Play(key[2], year, f"{key[0]}:{key[1]}", outcome, context))
    counts = Counter(play.athlete_id for play in plays)
    plays = [play for play in plays if counts[play.athlete_id] >= minimum_plays]
    audit["eligible_players"] = len({play.athlete_id for play in plays})
    audit["eligible_records"] = len(plays)
    audit["tracked_players_without_eligible_outcome"] = len(set(athletes) - {play.athlete_id for play in plays})
    audit["accepted_attempts"] = len(attempts)
    audit["players_by_draft_year"] = dict(Counter(str(athlete.draft_year) for athlete in athletes.values()))
    for name in ("unmatched_tracking_player_ids", "unmatched_play_player_ids", "unmatched_game_ids"):
        audit[name + "_count"] = len(audit[name])
        audit[name] = sorted(audit[name])[:20]
    audit["source_rejections"] = dict(audit["source_rejections"])
    audit["play_rejections"] = dict(audit["play_rejections"])
    manifest["official_adapter"] = {
        "version": "official-bdb2027-v2", "competition": "nfl-big-data-bowl-2027",
        "synthetic": False, "audit": audit,
        "tracking_units": {"time": "seconds since first actual timestamp in attempt",
                           "x": "yards", "y": "yards", "sample_rate_hz": 10},
        "timestamp_basis": "Timezone-naive source clocks preserved for relative differences/calendar dates; no timezone inferred; mixed naive/aware attempt clocks rejected",
        "measurement_columns": MEASUREMENT_COLUMNS,
        "measurement_availability": "Inferred proxy: latest accepted tracked Combine date per athlete; exact test publication dates absent",
        "ngs_availability": "Unverified chronology; inclusion requires an explicit pre-draft interpretation and a no-NGS sensitivity",
        "selection_position": "combine_results.combine_position; NFL position not used",
        "private_data": "Do not publish raw competition data or individual derived rows with source archives",
        "include_snap_context": include_snap_context,
    }
    definition = {
        "name": "player_get_off", "units": "seconds", "lower_is_better": True,
        "meaning": "Supplied time from ball snap to player crossing the line of scrimmage; not pure reaction time",
        "eligible_play": "Rookie REG, non-nullified, finite nonnegative charted get-off, accepted pre-draft Combine tracking" +
                         (", unique finite ball-snap geometry" if include_snap_context else ""),
        "minimum_plays": minimum_plays,
        "participation_scope": "Conditional on observed eligible NFL records; absent participation is missing, not zero",
    }
    return Dataset(athletes, attempts, plays, manifest, definition, synthetic=False)
