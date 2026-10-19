import argparse
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from probe import endpoints, normalize_text, parse_total_shots, schema_paths, scrub

class ProbeTests(unittest.TestCase):
    def test_shots_distinction(self):
        fixture = json.loads((Path(__file__).parent / "fixtures" / "player_stats.json").read_text())
        self.assertEqual(parse_total_shots(fixture)["total_shots"], 2)
        self.assertEqual(parse_total_shots({"stats": [{"name": "Shots on target", "value": 1}]})["state"], "not_found")
        self.assertIsNone(parse_total_shots({"stats": []})["total_shots"])
        self.assertEqual(parse_total_shots({"stats": [{"name": "Toplam Şut", "value": "0"}]})["total_shots"], 0)
        self.assertEqual(parse_total_shots({"stats": [{"name": "Shots", "value": 1}, {"name": "Shots", "value": 4}]})["state"], "ambiguous")
    def test_scrubbing(self):
        output = scrub({"access_token": "SECRET", "user": {"email": "private@example.com"}, "players": [1,2]})
        self.assertEqual(output["access_token"], "[REDACTED]")
        self.assertEqual(output["user"]["email"], "[REDACTED]")
        self.assertEqual(output["players"], [1,2])
    def test_modes(self):
        args = argparse.Namespace(mode="smoke", date="2026-10-19", search_term="Harry Winks", player_id="", match_id="", team_id="", season_id="")
        self.assertEqual(len(endpoints(args)),2)
        self.assertEqual(endpoints(args)[0][1],"/api/matches/")
        args.mode="player_stats"; args.player_id="999"; args.match_id="333"
        self.assertIn("/match/333/player/999/stats",endpoints(args)[0][1])
        args.player_id="../../etc"
        with self.assertRaises(ValueError): endpoints(args)
    def test_unicode(self):
        self.assertEqual(normalize_text("Toplam Şut"), "toplam sut")
        self.assertIn("$.stats", schema_paths({"stats":[{"name":"Total Shots"}]})[0])
if __name__ == "__main__":
    unittest.main()
