#!/usr/bin/env python3
"""Inspect verified ESPN soccer match JSON schema. Save schema only, not whole response."""
import json
import re
import urllib.request
import datetime as dt
from pathlib import Path

EVENT_ID="401879263" # Real ID confirmed from ESPN scoreboard live 2026-10-19
URL=f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/summary?event={EVENT_ID}"

def node_sample(node,depth=0):
    if depth>3:return type(node).__name__
    if isinstance(node,dict):
        return {k:node_sample(v,depth+1) for k,v in list(node.items())[:20]}
    if isinstance(node,list):
        return {"list_length":len(node),"first":node_sample(node[0],depth+1) if node else None}
    return node if isinstance(node,(int,float,bool)) else str(node)[:65]

def find_shot_fields(node,path="$",depth=0,output=None):
    output=[] if output is None else output
    if depth>13 or len(output)>=90:return output
    if isinstance(node,dict):
        for key,value in node.items():
            match=bool(re.search(r"shot|attempt|starting|starter|lineup",key,re.I))
            if not match and isinstance(value,str):
                match=bool(re.search(r"^total shots$|^shots on target$|^shots$|^shot attempts$",value,re.I))
            if match:
                output.append({"path":path+"."+str(key),"value":node_sample(value,2)})
            find_shot_fields(value,path+"."+str(key),depth+1,output)
            if len(output)>=90:break
    elif isinstance(node,list):
        for i,value in enumerate(node[:6]):
            find_shot_fields(value,path+f"[{i}]",depth+1,output)
    return output

def examine(data):
    if not isinstance(data,dict):return {"error":"not a JSON object"}
    blocks={}
    for key in ("rosters","boxscore","leaders","lastFiveGames","keyEvents","header","commentary"):
        blocks[key]=node_sample(data.get(key))
    return {"event_id":EVENT_ID,
            "top_level_keys":list(data),
            "blocks":blocks,
            "shot_and_starting_paths":find_shot_fields(data)}
def main():
    req=urllib.request.Request(URL,headers={"Accept":"application/json","User-Agent":"MackolikAPILab-ESPNStatInspection/1.0"})
    with urllib.request.urlopen(req,timeout=20) as res:
        status=res.status
        payload=json.load(res)
    evidence=examine(payload)
    evidence["http_status"]=status
    evidence["checked_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
    out=Path("out/espn_schema.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n")
    print("HTTP",status,"top-level fields",len(evidence["top_level_keys"]),"matching paths",len(evidence["shot_and_starting_paths"]))
    print(json.dumps(evidence["shot_and_starting_paths"][:15],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
