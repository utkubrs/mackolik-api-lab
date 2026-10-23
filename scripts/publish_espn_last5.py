#!/usr/bin/env python3
"""Publish only complete, verified, non-regressing ESPN Rayan last-five reports.

No network access; source fetch remains in espn_last5.py. Missing != zero.
"""
import datetime as dt
import json
import sys
from pathlib import Path

IDENTITY = ("eng.1", "349", "357719")


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("invalid match date")
    try:
        date = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid match date") from exc
    if date.tzinfo is None:
        raise ValueError("match date missing timezone")
    return date


def verify(new, old):
    if not isinstance(new, dict) or not isinstance(old, dict):
        raise ValueError("report must be JSON object")
    if tuple(str(new.get(k)) for k in ("league", "team_id", "player_id")) != IDENTITY:
        raise ValueError("report identity differs from canonical Rayan")
    if new.get("five_appearances_found") is not True or new.get("all_five_shots_verified") is not True:
        raise ValueError("five fully verified appearances required")
    matches = new.get("last_five_appearances")
    if not isinstance(matches, list) or len(matches) != 5:
        raise ValueError("expected exactly five appearances")
    ids, dates = set(), []
    for match in matches:
        if not isinstance(match, dict) or match.get("played") is not True or match.get("shots_verified") is not True:
            raise ValueError("unverified appearance")
        if str(match.get("player_id")) != IDENTITY[2]:
            raise ValueError("incorrect player in appearance")
        event = str(match.get("event_id", ""))
        if not (event.isascii() and event.isdecimal() and 5 <= len(event) <= 12) or event in ids:
            raise ValueError("invalid or duplicate event ID")
        ids.add(event)
        dates.append(timestamp(match.get("date")))
        shots = match.get("total_shots")
        on_target = match.get("shots_on_target")
        if type(shots) is not int or shots < 0:
            raise ValueError("totalShots missing or invalid; null is not zero")
        if on_target is not None and (type(on_target) is not int or not 0 <= on_target <= shots):
            raise ValueError("shotsOnTarget invalid")
    if dates != sorted(dates, reverse=True):
        raise ValueError("appearances not newest first")
    old_matches = old.get("last_five_appearances", [])
    if old_matches and dates[0] < timestamp(old_matches[0].get("date")):
        raise ValueError("refusing to replace newer report with older one")
    fields = ("event_id", "date", "player_id", "played", "starter",
              "total_shots", "shots_on_target", "shots_verified")
    def signature(rows):
        return [tuple(row.get(k) for k in fields) for row in rows]
    return signature(matches) != signature(old_matches)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: publish_espn_last5.py NEW_JSON SAVED_JSON")
    incoming, saved = map(Path, sys.argv[1:])
    new = json.loads(incoming.read_text(encoding="utf-8"))
    old = json.loads(saved.read_text(encoding="utf-8"))
    if verify(new, old):
        saved.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Rayan: published verified last-five changes")
    else:
        print("Rayan: unchanged; retained previously verified report")


if __name__ == "__main__":
    main()
