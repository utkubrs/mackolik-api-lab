#!/usr/bin/env bash
set -euo pipefail
# Normal app install + launch only. No anti-bot impersonation or token interception.
mkdir -p out
if [[ -z "${MACKOLIK_APK_URL:-}" ]]; then
  echo "::error::MACKOLIK_APK_URL GitHub Actions secret not set; original APK cannot be installed by GitHub runner."
  exit 2
fi
if [[ -z "${MACKOLIK_APK_SHA256:-}" ]]; then
  echo "::error::MACKOLIK_APK_SHA256 must be provided for APK integrity check."
  exit 2
fi
echo "Downloading private APK bundle over HTTPS (URL not logged)"
curl --proto '=https' --tlsv1.2 -fSL --max-time 240 --retry 1 --silent --show-error \
   --output "${RUNNER_TEMP:-/tmp}/mackolik-split.zip" "$MACKOLIK_APK_URL"
printf '%s  %s\n' "$MACKOLIK_APK_SHA256" "${RUNNER_TEMP:-/tmp}/mackolik-split.zip" | sha256sum -c -
python3 - <<'PY'
import zipfile,os
from pathlib import Path
source=Path(os.environ.get('RUNNER_TEMP','/tmp'))/'mackolik-split.zip'
out=Path(os.environ.get('RUNNER_TEMP','/tmp'))/'mackolik-apks'
out.mkdir(exist_ok=True)
allowed={'base.apk','split_config.arm64_v8a.apk','split_config.tr.apk','split_config.xxhdpi.apk'}
with zipfile.ZipFile(source) as archive:
    names=set(archive.namelist())
    if not allowed.issubset(names):
        raise RuntimeError(f'Missing APK splits: {sorted(allowed - names)}')
    for name in sorted(allowed):
        target=out/name
        with archive.open(name) as inp, target.open('wb') as dest:
            import shutil
            shutil.copyfileobj(inp,dest,1024*1024)
print('APK split file structure verified; no files published to git')
PY
WORK="${RUNNER_TEMP:-/tmp}/mackolik-apks"
echo "Installing original signed split APK set into Android emulator"
adb install-multiple -r -g "$WORK/base.apk" "$WORK/split_config.arm64_v8a.apk" "$WORK/split_config.tr.apk" "$WORK/split_config.xxhdpi.apk"
adb shell pm path com.kokteyl.mackolik | tee out/installed_package_paths.txt
echo "Launching standard app activity with Android package manager"
adb shell monkey -p com.kokteyl.mackolik -c android.intent.category.LAUNCHER 1
sleep 20
adb exec-out screencap -p > out/launch.png
adb shell dumpsys activity activities | grep -E 'mResumedActivity|mTopResumedActivity' | head -5 > out/activity.txt || :
echo "Original APK launch attempted; UI screenshot captured."
