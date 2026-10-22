#!/usr/bin/env python3
"""Synchronize verified Harry Winks shots from the hosted ESPN PHP JSON.

No network calls. Unknown/null shots are never converted to zero.
"""
import argparse
import datetime as dt
import json
from pathlib import Path


def normalize(hosted, previous):
    if not isinstance(hosted, dict) or not isinstance(previous, dict):
        raise ValueError("reports must be objects")
    if (str(hosted.get("player_id")) != "202332"
        or str(hosted.get("team_id")) != "2925"
        or hosted.get("league") != "ita.1"
        or hosted.get("five_found") is not True
        or hosted.get("five_verified") is not True):
        raise ValueError("identity or five-game verification failed")
    raw = hosted.get("last_five_appearances")
    if not isinstance(raw, list) or len(raw) != 5:
        raise ValueError("exactly five appearances required")
    ids, dates, matches = set(), [], []
    for m in raw:
        if not isinstance(m, dict) or m.get("played") is not True or m.get("player") != "Harry Winks":
            raise ValueError("unverified appearance")
        event = str(m.get("event_id", ""))
        if not event.isascii() or not event.isdecimal() or len(event) < 5 or event in ids:
            raise ValueError("invalid or duplicate event")
        ids.add(event)
        try:
            date = dt.datetime.fromisoformat(m["date"].replace("Z", "+00:00"))
            if date.tzinfo is None:
                raise ValueError("missing timezone")
        except (KeyError, AttributeError, TypeError, ValueError) as exc:
            raise ValueError("invalid date") from exc
        dates.append(date)
        shots, on_target = m.get("total_shots"), m.get("shots_on_target")
        if type(shots) is not int or shots < 0:
            raise ValueError("totalShots unknown or invalid")
        if on_target is not None and (type(on_target) is not int or not 0 <= on_target <= shots):
            raise ValueError("shotsOnTarget invalid")
        matches.append({"event_id": event, "date": m["date"], "name": m["player"],
                        "played": True, "player_id": "202332", "team": m.get("team"),
                        "starter": m.get("starter") is True, "total_shots": shots,
                        "shots_on_target": on_target, "shots_verified": True})
    if dates != sorted(dates, reverse=True):
        raise ValueError("events not newest first")
    prior = previous.get("five_shots", {}).get("matches", [])
    if prior:
        try:
            previous_date = dt.datetime.fromisoformat(prior[0]["date"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ValueError("invalid previous report") from exc
        if dates[0] < previous_date:
            raise ValueError("hosted report older than saved evidence")
    if prior == matches:
        return None
    updated = dict(previous)
    five = dict(updated.get("five_shots", {}))
    five.update({"player_id": "202332", "sequence": [m["total_shots"] for m in matches],
                 "complete": True, "verified": True, "matches": matches})
    updated["five_shots"] = five
    updated["source_url"] = ("https://duvar.applerehberi.com/mackolik-api-lab/"
                             "espn_last5.php?league=ita.1&team_id=2925&player_id=202332&format=json")
    updated["http_status"] = 200  # caller enforces HTTP 200
    updated["verified_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    return updated


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    target = Path(args.report)
    updated = normalize(json.loads(Path(args.input).read_text(encoding="utf-8")),
                        json.loads(target.read_text(encoding="utf-8")))
    if updated is None:
        print("Harry Winks: unchanged, verified")
    else:
        target.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("Harry Winks: updated:", updated["five_shots"]["sequence"])
