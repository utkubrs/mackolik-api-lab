#!/usr/bin/env python3
"""Düşük hacimli, yetkisiz kimlik doğrulama taklidi yapmayan Maçkolik bağlantı teşhisi."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

HOST = "https://api.mackolikfeeds.com"
MODES = ("smoke", "matches", "search", "player", "player_matches", "match", "player_stats", "team", "active_squad")
ID_RE = re.compile(r"^[A-Za-z0-9-]{1,64}$")
DATE_RE = re.compile(r"^20\d{2}-\d{2}-\d{2}$")
SENSITIVE = re.compile(r"(?:^|[_-])(authorization|auth|access[_-]?token|refresh[_-]?token|token|password|passwd|secret|cookie|session|api[_-]?key|client[_-]?secret|email|phone|device[_-]?id)(?:$|[_-])", re.I)
SHOTS_TOTAL = {"total shots", "shots total", "shots", "shot total", "total shot", "toplam sut", "sut", "sutlar", "sut sayisi", "toplam sut sayisi"}
SHOTS_EXCLUDE = ("on target", "off target", "blocked", "accuracy", "isabet", "engellen", "aut", "kaleyi bulan", "harita")
logger = logging.getLogger("mackolik-lab")


def normalize_text(value: str) -> str:
    replacements = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return re.sub(r"\s+", " ", re.sub(r"([a-z])([A-Z])", r"\1 \2", value).replace("_", " ").replace("-", " ").translate(replacements).lower()).strip()


def parse_total_shots(data: Any) -> dict[str, Any]:
    """Sadece olası toplam şut; bilinmeyen sayı asla sıfır yapılmaz."""
    matches: list[dict[str, Any]] = []
    def scan(node: Any, depth: int = 0) -> None:
        if depth > 14 or len(matches) > 100:
            return
        if isinstance(node, dict):
            if isinstance(node.get("name"), str) and "value" in node:
                label = normalize_text(node["name"])
                if label in SHOTS_TOTAL and not any(ex in label for ex in SHOTS_EXCLUDE):
                    raw = node["value"]
                    if isinstance(raw, (int, float)) and not isinstance(raw, bool) and raw >= 0 and int(raw) == raw:
                        matches.append({"name": node["name"], "value": int(raw)})
                    elif isinstance(raw, str) and re.fullmatch(r"\d+", raw.strip()):
                        matches.append({"name": node["name"], "value": int(raw.strip())})
            for v in node.values():
                scan(v, depth + 1)
        elif isinstance(node, list):
            for v in node[:100]:
                scan(v, depth + 1)
    scan(data)
    distinct = set(m["value"] for m in matches)
    return {"total_shots": next(iter(distinct)) if len(distinct) == 1 else None,
            "state": "candidate" if len(distinct) == 1 else ("ambiguous" if len(distinct) > 1 else "not_found"),
            "matches": matches[:10],
            "note": "Candidate only. Verify field semantics against a real player-stat response; null is not zero."}


def scrub(node: Any, depth: int = 0) -> Any:
    """Yanıt örnekleri sınırlı ve hassas anahtarları maskelenmiş."""
    if depth > 13:
        return "[DEPTH_LIMIT]"
    if isinstance(node, dict):
        result = {}
        for index, (key, value) in enumerate(node.items()):
            if index >= 120:
                result["_truncated_keys"] = len(node) - index
                break
            key = str(key)
            result[key] = "[REDACTED]" if SENSITIVE.search(key) else scrub(value, depth + 1)
        return result
    if isinstance(node, list):
        values = [scrub(v, depth + 1) for v in node[:100]]
        if len(node) > 100:
            values.append({"_truncated_items": len(node) - 100})
        return values
    if isinstance(node, str):
        return node[:2000] + ("...[TRUNCATED]" if len(node) > 2000 else "")
    return node if isinstance(node, (int, float, bool)) or node is None else str(node)[:100]


def schema_paths(node: Any, prefix: str = "$", max_paths: int = 100) -> list[str]:
    paths: list[str] = []
    def visit(value: Any, path: str, depth: int) -> None:
        if len(paths) >= max_paths or depth > 5:
            return
        if isinstance(value, dict):
            for k, v in list(value.items())[:35]:
                if SENSITIVE.search(str(k)):
                    continue
                p = f"{path}.{k}"
                paths.append(p + f" [{type(v).__name__}]")
                visit(v, p, depth + 1)
        elif isinstance(value, list) and value:
            visit(value[0], path + "[0]", depth + 1)
    visit(node, prefix, 0)
    return paths


def endpoints(args: argparse.Namespace) -> list[tuple[str, str, dict[str, str]]]:
    common = {"language": "tr", "country": "tr"}
    date = args.date or datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d")
    if not DATE_RE.fullmatch(date):
        raise ValueError("Date must be YYYY-MM-DD")
    matches = ("matches", "/api/matches/", {**common, "date": date, "tz": "Europe/Istanbul"})
    search = ("search", "/soccer/api/search/", {**common, "search": args.search_term})
    if args.mode == "smoke":
        return [matches, search]
    if args.mode == "matches":
        return [matches]
    if args.mode == "search":
        if not 2 <= len(args.search_term) <= 80:
            raise ValueError("search_term length must be 2..80")
        return [search]
    for attr in ("player_id", "match_id", "team_id"):
        value = getattr(args, attr)
        if value and not ID_RE.fullmatch(value):
            raise ValueError(f"Invalid {attr}; only letters, numbers and dashes are allowed")
    if args.mode in ("player", "player_matches", "player_stats") and not args.player_id:
        raise ValueError("player_id is required")
    if args.mode in ("match", "player_stats") and not args.match_id:
        raise ValueError("match_id is required")
    if args.mode in ("team", "active_squad") and not args.team_id:
        raise ValueError("team_id is required")
    if args.mode == "player":
        return [("player", "/api/player/", {**common, "player_id": args.player_id})]
    if args.mode == "player_matches":
        query = {**common, "player_id": args.player_id}
        if args.team_id:
            query["team_id"] = args.team_id
        if args.season_id:
            query["season_id"] = args.season_id
        return [("player_matches", "/api/player/matches", query)]
    if args.mode == "match":
        return [("match", "/api/match/", {**common, "match_id": args.match_id})]
    if args.mode == "player_stats":
        return [("player_stats", f"/statistics-service/match/{args.match_id}/player/{args.player_id}/stats", {"language": "tr"})]
    if args.mode == "team":
        return [("team", "/api/team/", {**common, "team_id": args.team_id})]
    if args.mode == "active_squad":
        return [("active_squad", f"/team-service/soccer/team/{args.team_id}/active-squad", {"language": "tr"})]
    raise ValueError(f"Unknown mode: {args.mode}")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: Any, msg: Any, headers: Any, newurl: Any) -> None:
        return None


def request_one(mode: str, path: str, query: dict[str, str], timeout: float) -> dict[str, Any]:
    url = HOST + path + "?" + urllib.parse.urlencode(query)
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "MackolikApiLab/0.1 (non-commercial diagnostics)"})
    opener = urllib.request.build_opener(NoRedirect)
    headers: dict[str, str] = {}
    status = 0
    raw = b""
    error: str | None = None
    started = time.perf_counter()
    logger.info("PROBE_START mode=%s method=GET url=%s timeout=%ss", mode, url, timeout)
    try:
        try:
            response = opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            status = response.status
            headers = {k.lower(): v for k, v in response.headers.items()}
            raw = response.read(524289)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        error = f"{type(exc).__name__}: {str(exc)[:240]}"
    elapsed = round((time.perf_counter() - started) * 1000)
    safe_headers = {k: headers[k] for k in ("content-type", "cache-control", "retry-after", "x-request-id", "cf-ray", "content-length", "server", "via") if k in headers}
    logger.info("PROBE_RESULT mode=%s status=%s duration_ms=%s received_bytes=%s content_type=%s error=%s", mode, status, elapsed, len(raw), headers.get("content-type", ""), error)
    logger.info("RESPONSE_HEADERS_SAFE %s", json.dumps(safe_headers, ensure_ascii=False))
    try:
        body = json.loads(raw.decode("utf-8-sig")) if raw else None
        parsed = body is not None
    except (UnicodeError, json.JSONDecodeError):
        body, parsed = None, False
    paths = schema_paths(body) if parsed else []
    sample = scrub(body) if parsed else None
    shot = parse_total_shots(body) if parsed and mode == "player_stats" else None
    if parsed:
        logger.debug("JSON_SCHEMA %s", json.dumps(paths, ensure_ascii=False))
    elif raw:
        logger.warning("NON_JSON_BODY prefix_sha256=%s (body intentionally not logged)", hashlib.sha256(raw[:1024]).hexdigest())
    if shot:
        logger.info("TOTAL_SHOTS_CANDIDATE %s", json.dumps(shot, ensure_ascii=False))
    non_json_excerpt = None
    if raw and not parsed and any(t in headers.get("content-type", "").lower() for t in ("text/html", "text/plain")):
        import html
        non_json_excerpt = html.unescape(re.sub(r"<[^>]*>", " ", raw[:1200].decode("utf-8", errors="replace")))
        non_json_excerpt = re.sub(r"\\s+", " ", non_json_excerpt).strip()[:500]
        non_json_excerpt = re.sub(r"(?i)(token|password|api[_-]?key|secret)(\\s*[=:]\\s*)([^\\s]+)", r"\\1\\2[REDACTED]", non_json_excerpt)
        logger.warning("HTTP_ERROR_TEXT_EXCERPT %s", non_json_excerpt)
    if len(raw) >= 524289:
        logger.warning("BODY_TRUNCATED at 512 KiB")
    return {"mode": mode, "url": url, "method": "GET", "http_status": status,
            "outcome": "ok_json" if 200 <= status < 300 and parsed else ("network_error" if error else "http_or_schema_error"),
            "duration_ms": elapsed, "received_bytes": len(raw), "body_truncated": len(raw) >= 524289,
            "safe_headers": safe_headers, "error": error, "is_json": parsed, "schema_paths": paths,
            "total_shots_candidate": shot, "response_sample_redacted": sample,
            "non_json_sha256": hashlib.sha256(raw).hexdigest() if raw and not parsed else None,
            "non_json_excerpt": non_json_excerpt}


def markdown_report(run: dict[str, Any]) -> str:
    lines = ["# Maçkolik API laboratuvarı", "", "Statik APK yolları: canlı şema ve kullanım hakları henüz doğrulanmadı.", "",
             "Test UTC: " + run["utc_time"], "Mod: " + run["mode"], "", "| İstek | HTTP | Sonuç | Süre | JSON |", "|---|---:|---|---:|---|"]
    for item in run["results"]:
        lines.append(f"| {item['mode']} | {item['http_status'] or '—'} | {item['outcome']} | {item['duration_ms']} ms | {'Evet' if item['is_json'] else 'Hayır'} |")
    lines.extend(["", "## Ayrıntılar"])
    for item in run["results"]:
        lines.extend(["", "### " + item["mode"], "- HTTP: " + str(item["http_status"]), "- URL yolu: " + urllib.parse.urlsplit(item["url"]).path,
                      "- Yanıt boyutu: " + str(item["received_bytes"]) + " bayt", "- Süre: " + str(item["duration_ms"]) + " ms",
                      "- Hata: " + str(item["error"] or "yok"), "- JSON alanı: " + str(len(item["schema_paths"]))])
        if item["schema_paths"]:
            lines.append("- İlk alanlar: " + ", ".join(item["schema_paths"][:12]))
        if item["total_shots_candidate"]:
            lines.append("- Şut adayı: " + str(item["total_shots_candidate"]["total_shots"]) + " (doğrulanmadı)")
    lines.extend(["", "401/403/429 yanıtları erişim kısıtlaması olabilir; aşılmaya çalışılmaz. Ayrıntılar Actions Artifact içindeki diagnostics.json dosyasında."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Maçkolik GET/JSON teşhis aracı")
    parser.add_argument("--mode", default="smoke", choices=MODES)
    parser.add_argument("--search-term", default="Harry Winks")
    parser.add_argument("--player-id", default="")
    parser.add_argument("--match-id", default="")
    parser.add_argument("--team-id", default="")
    parser.add_argument("--season-id", default="")
    parser.add_argument("--date", default="")
    parser.add_argument("--out", default="out")
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--fail-on-http", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s UTC %(levelname)-7s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
    logging.Formatter.converter = time.gmtime
    if not 2 <= len(args.search_term) <= 80 or args.timeout <= 0 or args.timeout > 30:
        parser.error("Invalid search term or timeout")
    try:
        jobs = endpoints(args)
    except ValueError as exc:
        parser.error(str(exc))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    run = {"utc_time": datetime.now(ZoneInfo("UTC")).isoformat(), "version": "0.1", "mode": args.mode,
           "notice": "APK yol var; canlı erişim/izin/şema doğrulanmadı.", "results": []}
    for mode, path, query in jobs:
        run["results"].append(request_one(mode, path, query, args.timeout))
        if len(jobs) > 1 and mode != jobs[-1][0]:
            time.sleep(1)
    (out / "diagnostics.json").write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    report = markdown_report(run)
    (out / "summary.md").write_text(report, encoding="utf-8")
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
            handle.write(report)
    print(report)
    return 2 if args.fail_on_http and any(r["outcome"] != "ok_json" for r in run["results"]) else 0


if __name__ == "__main__":
    sys.exit(main())
