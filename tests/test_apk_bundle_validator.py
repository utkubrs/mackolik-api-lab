import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from apk_bundle_validator import REQUIRED, validate_bundle


def create_bundle(path, bad_digest=False, extra=None):
    pieces = {name: (b"PK\x03\x04" + name.encode()) for name in REQUIRED}
    manifest = {
        "packageName": "com.kokteyl.mackolik",
        "versionName": "8.5.4",
        "versionCode": 8540,
        "apks": [
            {"file": name, "bytes": len(content),
             "sha256": "0" * 64 if bad_digest and name == "base.apk"
             else hashlib.sha256(content).hexdigest()}
            for name, content in pieces.items()
        ],
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as out:
        out.writestr("manifest.json", json.dumps(manifest))
        for name, content in pieces.items():
            out.writestr(name, content)
        if extra:
            out.writestr(extra, b"test")


class ApkValidationTests(unittest.TestCase):
    def test_valid_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bundle.zip"
            create_bundle(path)
            result = validate_bundle(path)
            self.assertTrue(result["validated"])
            self.assertEqual(len(result["split_files"]), 4)
    def test_tampered_split_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bundle.zip"
            create_bundle(path, bad_digest=True)
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                validate_bundle(path)
    def test_zip_slip_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bundle.zip"
            create_bundle(path, extra="../outside.apk")
            with self.assertRaises(ValueError):
                validate_bundle(path)
    def test_unexpected_member_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bundle.zip"
            create_bundle(path, extra="suspicious.txt")
            with self.assertRaises(ValueError):
                validate_bundle(path)

if __name__ == "__main__":
    unittest.main()
