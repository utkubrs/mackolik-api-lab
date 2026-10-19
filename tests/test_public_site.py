import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from public_site import inspect

class PublicSiteTests(unittest.TestCase):
    def test_title_not_match_stats(self):
        result=inspect(b"<title>Harry Winks | Mackolik</title>",200,"text/html; charset=utf-8")
        self.assertTrue(result["harry_winks_confirmed"])
        self.assertFalse(result["last_5_shots_confirmed"])
    def test_error_html(self):
        result=inspect(b"<title>Access Denied</title>",403,"text/html")
        self.assertIsNone(result["title"])
        self.assertFalse(result["harry_winks_confirmed"])
    def test_json_is_not_html(self):
        result=inspect(b'{"name":"Harry Winks"}',200,"application/json")
        self.assertFalse(result["harry_winks_confirmed"])
if __name__ == "__main__":
    unittest.main()
