#!/usr/bin/env python3
"""Skip repeated HTTP 403 probes until cooldown; still allow 10-minute status job."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

ACCESS_DENIED = {401,403,429}

def decide(last: dict | None, now: datetime, cooldown_minutes: int=60, force: bool=False) -> dict:
    if force:
        return {"probe": True,"reason": "manual_run","retry_after_minutes": 0}
    if not last or not isinstance(last.get("results"), list) or not last["results"]:
        return {"probe": True,"reason":"no_prior_result","retry_after_minutes":0}
    results=[x for x in last["results"] if x.get("mode") in ("matches","search")]
    if not results:
        return {"probe": True,"reason":"no_previous_api_status","retry_after_minutes":0}
    codes=[x.get("status") for x in results]
    if not all(x in ACCESS_DENIED for x in codes):
        return {"probe":True,"reason":"not_all_denied","retry_after_minutes":0}
    try:
        stamp=datetime.fromisoformat(last["utc_time"].replace("Z","+00:00"))
        if stamp.tzinfo is None:
            raise ValueError("missing timezone")
    except (ValueError, TypeError, KeyError):
        return {"probe":True,"reason":"invalid_timestamp","retry_after_minutes":0}
    age=max(0.0, (now.astimezone(timezone.utc)-stamp.astimezone(timezone.utc)).total_seconds()/60)
    delay=max(0, round(cooldown_minutes-age+0.499))
    return {"probe":delay==0,"reason":"denied_cooldown" if delay else "cooldown_elapsed", "retry_after_minutes":delay}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--last", default="data/latest.json")
    p.add_argument("--cooldown-minutes",type=int,default=60)
    p.add_argument("--force",action="store_true")
    args=p.parse_args()
    path=Path(args.last)
    try:
        last=json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except (OSError, json.JSONDecodeError):
        last=None
    result=decide(last,datetime.now(timezone.utc),args.cooldown_minutes,args.force)
    print(json.dumps(result,ensure_ascii=False))
    import os
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"],"a",encoding="utf-8") as out:
            out.write(f"probe={'true' if result['probe'] else 'false'}\n")
            out.write(f"reason={result['reason']}\n")
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as out:
            out.write(f"### Erişim testi planı\n\n{result['reason']} — "
                      f"{'istek yapılacak' if result['probe'] else '403 nedeniyle yeni istek yapılmayacak'}"
                      f"; kalan bekleme: {result['retry_after_minutes']} dakika.\n\n")
if __name__=="__main__":
    main()
