#!/usr/bin/env python3
"""ESPN: match-by-match totalShots for last five genuine player appearances."""
from __future__ import annotations
import datetime as dt
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE="https://site.api.espn.com/apis/site/v2/sports/soccer/"
LEAGUE=os.getenv("ESPN_LEAGUE","eng.1")
TEAM_ID=os.getenv("ESPN_TEAM_ID","349")
PLAYER_ID=os.getenv("ESPN_PLAYER_ID","357719")
CAP=16

def api(url):
    if not url.startswith(BASE):
        raise ValueError("only ESPN soccer site API allowed")
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"MackolikAPILab-ESPNFiveMatches/1.0"})
    with urllib.request.urlopen(req,timeout=16) as r:
        if r.status!=200:raise ValueError("ESPN not HTTP 200")
        data=json.load(r)
    if not isinstance(data,dict):raise ValueError("ESPN response not JSON object")
    return data

def stat(player,name):
    fields=player.get("stats",[])
    if not isinstance(fields,list):return None
    for entry in fields:
        if isinstance(entry,dict) and entry.get("name")==name:
            val=entry.get("value")
            if isinstance(val,(int,float)) and not isinstance(val,bool) and val>=0 and float(val).is_integer():
                return int(val)
    return None

def parse_player(summary,player_id):
    rosters=summary.get("rosters",[])
    if not isinstance(rosters,list):return {"played":False,"reason":"rosters missing"}
    for team in rosters:
        if not isinstance(team,dict):continue
        for p in team.get("roster",[]):
            if not isinstance(p,dict) or not isinstance(p.get("athlete"),dict):continue
            a=p["athlete"]
            if str(a.get("id"))!=str(player_id):continue
            appearances=stat(p,"appearances")
            if appearances is None:
                return {"played":False,"reason":"appearances statistic missing","name":a.get("displayName")}
            if appearances<1:
                return {"played":False,"reason":"bench or did not play","name":a.get("displayName")}
            return {"played":True,"name":a.get("displayName"),"player_id":str(player_id),
                    "team":team.get("team",{}).get("displayName"),
                    "starter":p.get("starter") is True,
                    "total_shots":stat(p,"totalShots"),
                    "shots_on_target":stat(p,"shotsOnTarget"),
                    "shots_verified":stat(p,"totalShots") is not None}
    return {"played":False,"reason":"player absent from roster"}

def schedule_events(data,until=None):
    raw=data.get("events",[])
    if not isinstance(raw,list):return []
    until=until or dt.datetime.now(dt.timezone.utc)
    valid=[]
    for e in raw:
        if not isinstance(e,dict):continue
        idv=str(e.get("id",""))
        if not re.fullmatch(r"\d{5,12}",idv):continue
        d=e.get("date","")
        try: moment=dt.datetime.fromisoformat(d.replace("Z","+00:00"))
        except (ValueError,AttributeError):continue
        if moment>until:continue
        status=e.get("status",{})
        status_type=status.get("type",{}) if isinstance(status,dict) else {}
        done=bool(status_type.get("completed")) if isinstance(status_type,dict) else False
        if not done:
            comp=e.get("competitions",[])
            if comp and isinstance(comp[0],dict):
                t=comp[0].get("status",{}).get("type",{})
                done=bool(t.get("completed")) if isinstance(t,dict) else False
        if done:valid.append({"event_id":idv,"date":moment.isoformat(),"name":e.get("name","")})
    valid.sort(key=lambda x:x["date"],reverse=True)
    return valid

def run():
    if not re.fullmatch(r"[a-z]{3}\.\d{1,2}",LEAGUE) or not TEAM_ID.isdigit() or not PLAYER_ID.isdigit():
        raise ValueError("invalid fixed league/team/player values")
    prefix=BASE+LEAGUE+"/"
    schedule=api(prefix+"teams/"+TEAM_ID+"/schedule")
    events=schedule_events(schedule)
    results=[]
    checked=[]
    for e in events[:CAP]:
        summary=api(prefix+"summary?event="+e["event_id"])
        detail=parse_player(summary,PLAYER_ID)
        checked.append({"event_id":e["event_id"],"played":detail.get("played"),"reason":detail.get("reason")})
        if detail.get("played"):
            results.append({**e,**detail})
        print(e["event_id"],detail.get("name"),"played",detail.get("played"),"total shots",detail.get("total_shots"),flush=True)
        if len(results)>=5:break
        time.sleep(0.5)
    output={"utc_time":dt.datetime.now(dt.timezone.utc).isoformat(),"league":LEAGUE,
            "team_id":TEAM_ID,"player_id":PLAYER_ID,"number_of_finished_events_found":len(events),
            "searched_events":len(checked),"last_five_appearances":results,
            "total_shots_sequence":[x["total_shots"] for x in results],
            "five_appearances_found":len(results)==5,
            "all_five_shots_verified":len(results)==5 and all(x["shots_verified"] for x in results),
            "note":"Reverse chronological; league-specific. totalShots != shotsOnTarget. Null means missing, not zero."}
    return output
if __name__=="__main__":
    result=run()
    dest=Path("out/espn_last5.json");dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"last_five_appearances":result["five_appearances_found"],
                      "all_five_shots_verified":result["all_five_shots_verified"],
                      "sequence":result["total_shots_sequence"]},ensure_ascii=False))
