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

from publish_espn_last5 import verify as verify_publish

class PublishGuardTests(unittest.TestCase):
    def sample(self):
        dates=["2026-10-18T13:00:00Z","2026-10-10T14:00:00Z",
               "2026-09-20T13:00:00Z","2026-09-12T14:00:00Z",
               "2026-09-05T11:30:00Z"]
        matches=[{"event_id":str(401879263+i),"date":date,"player_id":"357719",
                  "played":True,"starter":True,"shots_verified":True,
                  "total_shots":shots,"shots_on_target":0}
                 for i,(date,shots) in enumerate(zip(dates,[7,2,0,5,1]))]
        return {"league":"eng.1","team_id":"349","player_id":"357719",
                "five_appearances_found":True,"all_five_shots_verified":True,
                "last_five_appearances":matches}
    def test_unchanged_report_not_rewritten(self):
        new=self.sample()
        self.assertFalse(verify_publish(new,new))
    def test_valid_change_published(self):
        new=self.sample()
        old=self.sample()
        new["last_five_appearances"][0]["total_shots"]=8
        self.assertTrue(verify_publish(new,old))
    def test_zero_is_verified_zero(self):
        new=self.sample()
        old=self.sample()
        new["last_five_appearances"][0]["total_shots"]=0
        self.assertTrue(verify_publish(new,old))
    def test_null_is_not_zero(self):
        new=self.sample()
        new["last_five_appearances"][0]["total_shots"]=None
        with self.assertRaises(ValueError):
            verify_publish(new,self.sample())
    def test_incomplete_report_rejected(self):
        new=self.sample()
        new["all_five_shots_verified"]=False
        with self.assertRaises(ValueError):
            verify_publish(new,self.sample())
    def test_wrong_player_rejected(self):
        new=self.sample()
        new["player_id"]="202332"
        with self.assertRaises(ValueError):
            verify_publish(new,self.sample())
    def test_older_report_rejected(self):
        new=self.sample()
        old=self.sample()
        old["last_five_appearances"][0]["date"]="2026-10-19T13:00:00Z"
        with self.assertRaises(ValueError):
            verify_publish(new,old)
    def test_on_target_cannot_exceed_total(self):
        new=self.sample()
        new["last_five_appearances"][2]["shots_on_target"]=1
        with self.assertRaises(ValueError):
            verify_publish(new,self.sample())

if __name__=="__main__": unittest.main()
