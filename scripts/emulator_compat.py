#!/usr/bin/env python3
"""Checks whether the Android emulator can run all native libraries in an APK split set."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

APK_ABI = "arm64-v8a"
def analyze_abi(emulator_abis: str, apk_abis: list[str] | None = None) -> dict:
    actual = [x.strip() for x in emulator_abis.split(",") if x.strip()]
    target = apk_abis or [APK_ABI]
    matching = sorted(set(actual) & set(target))
    return {
        "emulator_abis": actual,
        "uploaded_apk_native_abis": target,
        "compatible": bool(matching),
        "compatible_abis": matching,
        "note": ("ABI compatibility check only. Does not guarantee app login/API success."
                 if matching else "Incompatible native library ABI: this emulated Android cannot install the uploaded ARM64-only split in normal mode.")
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abi-list", required=True)
    parser.add_argument("--out", default="out/emulator_compat.json")
    args=parser.parse_args()
    result=analyze_abi(args.abi_list)
    path=Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
