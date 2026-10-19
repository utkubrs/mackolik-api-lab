#!/usr/bin/env python3
"""Validate the user's original signed split-APK ZIP before emulator installation.

This tool never patches APKs or handles application credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

EXPECTED_PACKAGE = "com.kokteyl.mackolik"
EXPECTED_VERSION = "8.5.4"
EXPECTED_VERSION_CODE = 8540
REQUIRED = {
    "base.apk",
    "split_config.arm64_v8a.apk",
    "split_config.tr.apk",
    "split_config.xxhdpi.apk",
}
ALLOWED = REQUIRED | {"manifest.json"}
MAX_TOTAL = 340 * 1024 * 1024
MAX_SINGLE = 260 * 1024 * 1024


def validate_bundle(path: str | Path) -> dict:
    file_path = Path(path)
    with zipfile.ZipFile(file_path) as archive:
        items = archive.infolist()
        names = [v.filename for v in items]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP member paths")
        if set(names) != ALLOWED:
            raise ValueError(f"Unexpected/missing ZIP entries: {sorted(set(names) ^ ALLOWED)}")
        total = 0
        for entry in items:
            name = PurePosixPath(entry.filename)
            if entry.is_dir() or name.is_absolute() or ".." in name.parts or entry.file_size > MAX_SINGLE:
                raise ValueError(f"Unsafe ZIP entry: {entry.filename}")
            total += entry.file_size
        if total > MAX_TOTAL:
            raise ValueError("Unexpected APK bundle size")
        meta = json.loads(archive.read("manifest.json"))
        if not isinstance(meta, dict):
            raise ValueError("Invalid manifest structure")
        if (meta.get("packageName") != EXPECTED_PACKAGE or
                meta.get("versionName") != EXPECTED_VERSION or
                meta.get("versionCode") != EXPECTED_VERSION_CODE):
            raise ValueError("Unexpected application package or version")
        data = meta.get("apks")
        if not isinstance(data, list) or len(data) != len(REQUIRED):
            raise ValueError("Invalid split APK manifest")
        by_name = {}
        for part in data:
            if not isinstance(part, dict) or not isinstance(part.get("file"), str):
                raise ValueError("Invalid APK manifest entry")
            if part["file"] in by_name:
                raise ValueError("Duplicate APK record")
            by_name[part["file"]] = part
        if set(by_name) != REQUIRED:
            raise ValueError("Mismatch between manifest and ZIP APKs")
        verified = []
        for name in sorted(REQUIRED):
            entry = archive.getinfo(name)
            declared = by_name[name]
            if declared.get("bytes") != entry.file_size:
                raise ValueError(f"APK size mismatch: {name}")
            digest = hashlib.sha256()
            with archive.open(name) as stream:
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
            if declared.get("sha256") != digest.hexdigest():
                raise ValueError(f"APK digest mismatch: {name}")
            verified.append({"file": name, "size_bytes": entry.file_size, "sha256": digest.hexdigest()})
    return {
        "validated": True,
        "package": EXPECTED_PACKAGE,
        "version": EXPECTED_VERSION,
        "version_code": EXPECTED_VERSION_CODE,
        "split_files": verified,
        "note": "Bundle checksums and metadata verified; Android installation and API access are not verified.",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("zip_file")
    p.add_argument("--out", default="out/apk_bundle_check.json")
    args = p.parse_args()
    try:
        result = validate_bundle(args.zip_file)
    except (OSError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print(f"APK bundle validation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"APK bundle verified: {result['package']} v{result['version']} ({len(result['split_files'])} splits)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
