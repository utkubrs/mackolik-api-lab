#!/usr/bin/env python3
"""Check public player profile availability; never infer per-match shots from HTML."""
import datetime as dt
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import ssl
import time
import urllib.error
import urllib.request

URL = "https://www.mackolik.com/futbolcu/h-winks/5qfa3h4gut5jlnfkexq5m1djp"

class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.collect = False
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.collect = True
    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.collect = False
    def handle_data(self, text):
        if self.collect:
            self.parts.append(text)

def inspect(body, status, content_type):
    result = {"html": "text/html" in content_type.lower(), "title": None,
              "harry_winks_confirmed": False, "last_5_shots_confirmed": False}
    if status != 200 or not result["html"]:
        return result
    parser = TitleParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    title = html.unescape(" ".join(parser.parts)).strip()[:180]
    result["title"] = title
    result["harry_winks_confirmed"] = "harry winks" in title.lower()
    return result

def main():
    request = urllib.request.Request(URL, headers={
        "Accept": "text/html", "User-Agent": "MackolikAPILab-PublicSiteCheck/1.0"
    })
    started = time.monotonic()
    status = 0
    content_type = ""
    error = None
    body = b""
    try:
        with urllib.request.urlopen(request, timeout=15, context=ssl.create_default_context()) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            body = response.read(250001)
    except urllib.error.HTTPError as exc:
        status = exc.code
        content_type = exc.headers.get("Content-Type", "")
        body = exc.read(1024)
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        error = f"{type(exc).__name__}: {str(exc)[:160]}"
    result = {"utc_time": dt.datetime.now(dt.timezone.utc).isoformat(), "url": URL,
              "http_status": status, "content_type": content_type,
              "bytes": len(body), "truncated": len(body)>250000,
              "elapsed_ms": round(1000*(time.monotonic()-started)),
              "error": error, "evidence": inspect(body[:250000],status,content_type),
              "note": "Public profile availability only; last five match shot totals remain unverified."}
    out=Path("out/public_site.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
