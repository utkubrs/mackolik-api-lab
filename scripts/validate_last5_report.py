#!/usr/bin/env python3
"""Validate real ESPN totalShots reports before replacing the last known good JSON."""
from __future__ import annotations
import datetime as dt
import json
import sys
from pathlib import Path

def require(ok, message):
    if not ok:
        raise ValueError(message)

def as_date(value):
    require(isinstance(value, str), "match date missing")
    date = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(date.tzinfo is not None, "match date must have timezone")
    require(date <= dt.datetime.now(dt.timezone.utc), "future match date")
    return date

def validate_matches(matches, expected_player_id):
    require(isinstance(matches, list) and len(matches) == 5, "exactly five played matches required")
    ids, dates, shots = set(), [], []
    for match in matches:
        require(isinstance(match, dict), "invalid match")
        eid = str(match.get("event_id", ""))
        require(eid.isdigit() and eid not in ids, "invalid or duplicate event ID")
        ids.add(eid)
        require(str(match.get("player_id")) == str(expected_player_id), "player ID mismatch")
        require(match.get("played") is True, "player did not play")
        value = match.get("total_shots")
        require(type(value) is int and value >= 0, "totalShots missing or invalid (null is not zero)")
        require(match.get("shots_verified") is True, "totalShots not verified")
        on_target = match.get("shots_on_target")
        require(on_target is None or (type(on_target) is int and 0 <= on_target <= value),
                "shotsOnTarget invalid")
        dates.append(as_date(match.get("date")))
        shots.append(value)
    require(all(a > b for a, b in zip(dates, dates[1:])), "matches not newest-first")
    return shots, dates[0]

def validate_report(mode, report, previous=None):
    require(isinstance(report, dict), "report is not JSON object")
    if mode == "espn":
        require(report.get("five_appearances_found") is True, "five appearances not confirmed")
        require(report.get("all_five_shots_verified") is True, "five shot values not verified")
        player_id = report.get("player_id")
        matches = report.get("last_five_appearances")
        series = report.get("total_shots_sequence")
        identity = (str(report.get("league")), str(report.get("team_id")), str(player_id))
        old_identity = ((str(previous.get("league")), str(previous.get("team_id")), str(previous.get("player_id")))
                        if isinstance(previous, dict) else None)
        old_matches = previous.get("last_five_appearances") if isinstance(previous, dict) else None
    elif mode == "winks":
        require(report.get("http_status") == 200, "roster was not HTTP 200")
        require(report.get("child_exit_code") == 0, "last-five child script failed")
        require(any(str(p.get("id")) == "202332" for p in report.get("candidate_player_ids", [])
                    if isinstance(p, dict)), "Harry Winks identity not verified")
        payload = report.get("five_shots")
        require(isinstance(payload, dict) and payload.get("complete") is True and
                payload.get("verified") is True, "five Harry Winks shots not verified")
        player_id = payload.get("player_id")
        require(str(player_id) == "202332", "wrong Harry Winks player ID")
        matches, series = payload.get("matches"), payload.get("sequence")
        identity = ("ita.1", "2925", str(player_id))
        old_identity = ("ita.1", "2925", "202332")
        old_payload = previous.get("five_shots") if isinstance(previous, dict) else None
        old_matches = old_payload.get("matches") if isinstance(old_payload, dict) else None
    else:
        raise ValueError("unknown report type")
    shots, newest = validate_matches(matches, player_id)
    require(series == shots, "shot sequence disagrees with match records")
    if old_identity == identity and isinstance(old_matches, list) and old_matches:
        old_newest = as_date(old_matches[0].get("date"))
        require(newest >= old_newest, "new report is older than existing verified report")
    return shots

def main():
    require(len(sys.argv) == 4, "usage: validate_last5_report.py espn|winks NEW.json OLD.json")
    mode, candidate, old_path = sys.argv[1:]
    report = json.loads(Path(candidate).read_text(encoding="utf-8"))
    previous = json.loads(Path(old_path).read_text(encoding="utf-8")) if Path(old_path).exists() else None
    shots = validate_report(mode, report, previous)
    print(f"VERIFIED {mode}: {shots}; null was never converted to zero")

if __name__ == "__main__":
    main()
