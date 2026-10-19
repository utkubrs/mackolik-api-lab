import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).parents[1]/"scripts"))
from emulator_compat import analyze_abi

class EmulatorAbiTests(unittest.TestCase):
    def test_x86_is_not_arm64(self):
        self.assertFalse(analyze_abi("x86_64,x86")["compatible"])
    def test_arm64_is_compatible(self):
        self.assertTrue(analyze_abi("arm64-v8a,armeabi-v7a")["compatible"])
    def test_empty(self):
        self.assertFalse(analyze_abi("")["compatible"])

if __name__ == "__main__":
    unittest.main()
