import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from espn_last5 import parse_player,schedule_events
class ESPNLast5Tests(unittest.TestCase):
    def test_total_shots_not_on_target(self):
        j={"rosters":[{"team":{"displayName":"Test"},
            "roster":[{"athlete":{"id":"123","displayName":"Player"},"starter":True,
            "stats":[{"name":"appearances","value":1},{"name":"totalShots","value":3},{"name":"shotsOnTarget","value":1}]}]}]}
        r=parse_player(j,"123")
        self.assertEqual(r["total_shots"],3)
        self.assertEqual(r["shots_on_target"],1)
        self.assertTrue(r["played"])
    def test_did_not_play_is_not_zero(self):
        j={"rosters":[{"roster":[{"athlete":{"id":"123"},"starter":False,"stats":[{"name":"appearances","value":0}]}]}]}
        r=parse_player(j,"123")
        self.assertFalse(r["played"])
        self.assertNotIn("total_shots",r)
    def test_missing_stats_is_not_zero(self):
        j={"rosters":[{"roster":[{"athlete":{"id":"123"},"starter":True,"stats":[{"name":"appearances","value":1}]}]}]}
        self.assertIsNone(parse_player(j,"123")["total_shots"])
    def test_recent_finished_events(self):
        events={"events":[{"id":"123456","date":"2026-10-18T15:00:00Z","status":{"type":{"completed":True}}},
                          {"id":"123457","date":"2026-10-20T15:00:00Z","status":{"type":{"completed":False}}}]}
        self.assertEqual([x["event_id"] for x in schedule_events(events)],["123456"])
if __name__=="__main__": unittest.main()
