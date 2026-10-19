#!/usr/bin/env python3
"""Discover Harry Winks via ESPN's current Cagliari roster; then verify five Serie A shots."""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

URL="https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/teams/2925/roster"
def candidates(node,depth=0):
    result=[]
    if depth>12:return result
    if isinstance(node,dict):
        names=[node.get("displayName"),node.get("fullName"),node.get("name")]
        if any(isinstance(n,str) and n.lower().strip()=="harry winks" for n in names):
            result.append({"id":str(node.get("id","")),"name":"Harry Winks"})
        for v in node.values():
            result.extend(candidates(v,depth+1))
    elif isinstance(node,list):
        for v in node[:300]:result.extend(candidates(v,depth+1))
    return result
def main():
    req=urllib.request.Request(URL,headers={"Accept":"application/json","User-Agent":"MackolikAPILab-PlayerIdentity/1.0"})
    with urllib.request.urlopen(req,timeout=15) as r:
        status=r.status
        data=json.load(r)
    found=[x for x in candidates(data) if x["id"].isdigit()]
    found=found[:3]
    report={"roster_url":URL,"http_status":status,"candidate_player_ids":found,"five_shots":None}
    if found:
        env=os.environ.copy()
        env.update({"ESPN_LEAGUE":"ita.1","ESPN_TEAM_ID":"2925","ESPN_PLAYER_ID":found[0]["id"]})
        p=subprocess.run([sys.executable,"scripts/espn_last5.py"],env=env,capture_output=True,text=True,timeout=150)
        report["child_exit_code"]=p.returncode
        if p.returncode==0:
            x=json.loads(Path("out/espn_last5.json").read_text())
            report["five_shots"]={"player_id":found[0]["id"],
                   "sequence":x.get("total_shots_sequence"),"complete":x.get("five_appearances_found"),
                   "verified":x.get("all_five_shots_verified"),"matches":x.get("last_five_appearances")}
        else:
            report["error"]="Last-five retrieval failed (see Actions logs for bounded diagnostics)"
    out=Path("out/harry_winks.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
