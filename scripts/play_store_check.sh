#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
PACKAGE="com.kokteyl.mackolik"
echo "Checking genuine Google Play system image on clean Android emulator."
adb wait-for-device
adb shell getprop ro.build.version.release | tr -d '\r' > out/android_release.txt
adb shell pm path com.android.vending > out/play_store_package.txt || :
adb shell pm path "$PACKAGE" > out/mackolik_installed.txt || :
# Only opens official Google Play app listing. No automated account login.
adb shell am start -a android.intent.action.VIEW -d \
  "market://details?id=$PACKAGE" > out/play_store_open.txt 2>&1 || :
sleep 12
adb shell dumpsys window windows 2>/dev/null | grep -E \
 'mCurrentFocus|mFocusedApp|Window #0' | head -8 > out/focus.txt || :
adb exec-out screencap -p > out/play_store.png
python3 - <<'PY'
import json
from pathlib import Path
from datetime import datetime, timezone
out=Path("out")
def get(name):
    p=out/name
    return p.read_text(errors="replace").strip() if p.exists() else ""
result={
  "timestamp_utc":datetime.now(timezone.utc).isoformat(),
  "android_release":get("android_release.txt"),
  "google_play_package_available": "package:" in get("play_store_package.txt"),
  "mackolik_installed": "package:" in get("mackolik_installed.txt"),
  "market_intent_result":get("play_store_open.txt")[:300],
  "focused_window":get("focus.txt")[:400],
  "screenshot_present": (out/"play_store.png").exists() and (out/"play_store.png").stat().st_size > 0,
  "note":"Only tests opening official Play Store listing. A listing is NOT an installed app or API success."
}
(out/"play_store_evidence.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+chr(10))
print(json.dumps(result,indent=2,ensure_ascii=False))
PY
