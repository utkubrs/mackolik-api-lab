#!/usr/bin/env python3
"""Test public football data feeds without guessing player-shot values."""
import datetime as dt
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

MAX_BODY=1500000
ESPN="https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/"
UNDERSTAT="https://understat.com/"
def get(label,url,understat=False):
    headers={"Accept":"application/json","User-Agent":"MackolikAPILab-OpenDataDiagnostic/1.0"}
    if understat:
        headers.update({"X-Requested-With":"XMLHttpRequest","Referer":UNDERSTAT})
    req=urllib.request.Request(url,headers=headers)
    started=time.monotonic(); code=0; typ=""; error=None; body=b""
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            code=r.status; typ=r.headers.get("Content-Type",""); body=r.read(MAX_BODY+1)
    except urllib.error.HTTPError as e:
        code=e.code;typ=e.headers.get("Content-Type","");body=e.read(1024)
    except (OSError,TimeoutError) as e:
        error=type(e).__name__+": "+str(e)[:120]
    data=None
    if body and len(body)<=MAX_BODY:
        try: data=json.loads(body.decode("utf-8-sig"))
        except (UnicodeError,ValueError): pass
    status={"source":label,"http_status":code,"is_json":data is not None,
            "bytes":len(body),"duration_ms":int(1000*(time.monotonic()-started)),
            "keys":list(data)[:25] if isinstance(data,dict) else [],
            "error":error,"url":url}
    return status,data

def count_shots(data):
    """Each home/away event is a total shot, including off-target, blocked and goals."""
    if not isinstance(data,dict) or not isinstance(data.get("shots"),dict):
        return {"verified":False,"reason":"shots object absent"}
    x=data["shots"]
    if not isinstance(x.get("h"),list) or not isinstance(x.get("a"),list):
        return {"verified":False,"reason":"home/away shot event arrays absent"}
    events=x["h"]+x["a"]
    if not all(isinstance(e,dict) and isinstance(e.get("player"),str) for e in events):
        return {"verified":False,"reason":"invalid event list"}
    totals=Counter(e["player"] for e in events)
    return {"verified":True,"total_shot_events":len(events),
            "sample_players":[{"name":k,"total_shots":v} for k,v in totals.most_common(7)],
            "note":"Players absent from shot events may have zero shots, or may not have played. Must verify lineup before asserting zero."}

def completed_match_id(data):
    if not isinstance(data,dict) or not isinstance(data.get("dates"),list): return None
    for x in reversed(data["dates"]):
        if isinstance(x,dict) and x.get("isResult") is True and re.fullmatch(r"\d{1,10}",str(x.get("id",""))):
            return str(x["id"])
    return None

def espn_event_id(data):
    if not isinstance(data,dict) or not isinstance(data.get("events"),list): return None
    for x in data["events"][:30]:
        if isinstance(x,dict) and re.fullmatch(r"\d{5,12}",str(x.get("id",""))): return str(x["id"])
    return None

def run():
    results=[]
    today=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=1)).strftime("%Y%m%d")
    cases=[("espn_scoreboard",ESPN+"scoreboard?dates="+today,False),
           ("understat_league",UNDERSTAT+"getLeagueData/EPL/2026",True)]
    report={"utc_time":dt.datetime.now(dt.timezone.utc).isoformat(),
            "source":"public-data feasibility experiment",
            "results":results,"shot_events_verified":False,"last_five_player_shots_verified":False,
            "lineups_verified":False}
    for label,url,under in cases:
        item,data=get(label,url,under);results.append(item)
        print(label,"HTTP",item["http_status"],"JSON",item["is_json"],flush=True)
        if item["http_status"]!=200 or not item["is_json"]:continue
        if label=="espn_scoreboard":
            item["event_count"]=len(data["events"]) if isinstance(data,dict) and isinstance(data.get("events"),list) else None
            mid=espn_event_id(data)
            if mid:
                info,payload=get("espn_summary",ESPN+"summary?event="+mid)
                if isinstance(payload,dict):
                    info["has_boxscore"]="boxscore" in payload
                    b=payload.get("boxscore")
                    info["boxscore_keys"]=list(b)[:20] if isinstance(b,dict) else []
                results.append(info)
                print("espn_summary","HTTP",info["http_status"],"JSON",info["is_json"],flush=True)
        if label=="understat_league":
            item["player_count"]=len(data["players"]) if isinstance(data,dict) and isinstance(data.get("players"),list) else None
            mid=completed_match_id(data)
            if mid:
                info,payload=get("understat_shot_events",UNDERSTAT+"getMatchData/"+mid,True)
                info["match_id"]=mid
                info["shot_count"]=count_shots(payload)
                report["shot_events_verified"]=info["http_status"]==200 and info["shot_count"]["verified"]
                results.append(info)
                print("understat_shot_events","HTTP",info["http_status"],"verified",report["shot_events_verified"],flush=True)
    return report
if __name__=="__main__":
    report=run()
    path=Path("out/alternative_sources.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as out:
            out.write("## Alternatif futbol kaynakları — gerçek test\n\n| Kaynak | HTTP | JSON |\n|---|---:|---|\n")
            for x in report["results"]:
                out.write(f"| {x['source']} | {x['http_status']} | {'Evet' if x['is_json'] else 'Hayır'} |\n")
            out.write(f"\nÖrnek maçta şut olayları: {report['shot_events_verified']}; son 5 oyuncu maçı: doğrulanmadı.\n")
