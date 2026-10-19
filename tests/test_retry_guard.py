import sys
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone
sys.path.insert(0,str(Path(__file__).parents[1]/"scripts"))
from retry_guard import decide

NOW=datetime(2026,10,19,16,40,tzinfo=timezone.utc)
def record(minutes_ago=5,status=403):
    return {"utc_time":(NOW-timedelta(minutes=minutes_ago)).isoformat(),
            "results":[{"mode":"matches","status":status},{"mode":"search","status":status}]}
class GuardTests(unittest.TestCase):
    def test_403_throttle(self):
        a=decide(record(), NOW)
        self.assertFalse(a["probe"])
        self.assertEqual(a["reason"],"denied_cooldown")
    def test_retry_after_cooldown(self):
        self.assertTrue(decide(record(65), NOW)["probe"])
    def test_manual(self):
        self.assertTrue(decide(record(), NOW, force=True)["probe"])
    def test_success_retries(self):
        self.assertTrue(decide(record(1,200), NOW)["probe"])
    def test_missing(self):
        self.assertTrue(decide(None,NOW)["probe"])

if __name__ == "__main__":
    unittest.main()
