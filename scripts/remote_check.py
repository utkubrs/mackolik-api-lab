#!/usr/bin/env python3
"""GitHub testine sabit hedefli PHP sunucu sonucunu ekler."""
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from probe import markdown_report

URL="https://duvar.applerehberi.com/mackolik-api-lab/remote_probe.php"

def remote_check():
    path=Path("out/diagnostics.json")
    if not path.exists():return
    run=json.loads(path.read_text(encoding="utf8"))
    try:
        req=urllib.request.Request(URL,headers={"Accept":"application/json","User-Agent":"MackolikApiLab/0.2"})
        with urllib.request.urlopen(req,timeout=40) as response:
            if response.status!=200:raise ValueError("PHP HTTP "+str(response.status))
            payload=json.loads(response.read(65536))
        if payload.get("source")!="duvar-host-php":raise ValueError("Unexpected PHP response")
        for row in payload.get("results",[])[:2]:
            if row.get("test") not in ("matches","search"):continue
            status=int(row.get("http_status") or 0)
            is_json=row.get("is_json") is True
            err=str(row.get("error") or row.get("error_text_excerpt") or "")[:180]
            sample={
              "mode":"remote_"+row["test"],"http_status":status,
              "outcome":"ok_json" if status==200 and is_json else "http_or_schema_error",
              "duration_ms":int(row.get("duration_ms") or 0),
              "received_bytes":int(row.get("bytes") or 0),
              "is_json":is_json,
              "schema_paths":["$."+str(k) for k in row.get("json_top_keys",[])[:30]],
              "error":err or None,"total_shots_candidate":None
            }
            run["results"].append(sample)
            print("REMOTE %s HTTP=%s JSON=%s error=%s"%(row["test"],status,is_json,err))
    except (OSError,ValueError,urllib.error.URLError) as exc:
        run["results"].append({
          "mode":"remote_probe","http_status":0,"outcome":"network_error",
          "duration_ms":0,"received_bytes":0,"is_json":False,
          "schema_paths":[],"error":str(exc)[:180],"total_shots_candidate":None
        })
        print("REMOTE ERROR "+str(exc)[:180])
    path.write_text(json.dumps(run,indent=2,ensure_ascii=False),encoding="utf8")
    summary=markdown_report(run)
    Path("out/summary.md").write_text(summary,encoding="utf8")
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf8") as fp:
            fp.write("\n## Türkiye sunucusu üzerinden bağımsız test\n"+summary)
if __name__=="__main__":remote_check()
