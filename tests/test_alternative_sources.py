import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from alternative_sources import count_shots,completed_match_id,espn_event_id

class AlternativeSourceTests(unittest.TestCase):
    def test_count_total_shots(self):
        j={"shots":{"h":[{"player":"A"},{"player":"A"},{"player":"B"}],"a":[{"player":"C"}]}}
        x=count_shots(j)
        self.assertTrue(x["verified"])
        self.assertEqual(x["total_shot_events"],4)
        self.assertEqual(x["sample_players"][0]["total_shots"],2)
    def test_missing_is_not_zero(self):
        x=count_shots({"shots":{}})
        self.assertFalse(x["verified"])
        self.assertNotIn("total_shot_events",x)
    def test_match_must_be_completed(self):
        j={"dates":[{"id":"101","isResult":True},{"id":"102","isResult":False}]}
        self.assertEqual(completed_match_id(j),"101")
        self.assertIsNone(completed_match_id({"dates":[]}))
    def test_espn_event_id(self):
        self.assertEqual(espn_event_id({"events":[{"id":"401765300"}]}),"401765300")
        self.assertIsNone(espn_event_id({"events":[{"id":"../../admin"}]}))
if __name__=="__main__":
    unittest.main()
