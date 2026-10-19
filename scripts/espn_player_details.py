#!/usr/bin/env python3
import json
import urllib.request
from pathlib import Path
URL="https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/summary?event=401879263"
req=urllib.request.Request(URL,headers={"Accept":"application/json","User-Agent":"MackolikAPILab-PlayerStatProbe/1.0"})
with urllib.request.urlopen(req,timeout=15) as response:
    code=response.status
    data=json.load(response)
result={"http_status":code,"verified_actual_match":code==200,"teams":[],"leaders":[]}
for roster in data.get("rosters",[]):
    team=roster.get("team",{}).get("displayName")
    records=roster.get("roster",[])
    players=[]
    for person in records:
        athlete=person.get("athlete",{})
        players.append({
            "name":athlete.get("displayName") or athlete.get("fullName"),
            "id":athlete.get("id"),"starter":person.get("starter"),
            "position":person.get("position",{}).get("abbreviation"),
            "stats":person.get("stats",[])
        })
    result["teams"].append({"team":team,"formation":roster.get("formation"),"players_count":len(records),
                            "starters_count":sum(x.get("starter") is True for x in records),
                            "sample_players":players[:6],
                            "stats_of_players_with_nonempty_stats":next((p for p in players if p["stats"]),None)})
for teamleader in data.get("leaders",[])[:2]:
    result["leaders"].append({
        "team":teamleader.get("team",{}).get("displayName"),
        "category_labels":[x.get("displayName") for x in teamleader.get("leaders",[])],
        "total_shots_leader":next((x for x in teamleader.get("leaders",[]) if x.get("displayName")=="Total Shots"),None)
    })
path=Path("out/espn_player_details.json")
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"http_status":code,"teams":[{"team":t["team"],"players_count":t["players_count"],"starters_count":t["starters_count"],"first_stat":t["stats_of_players_with_nonempty_stats"]} for t in result["teams"]]},ensure_ascii=False,indent=2))
