"""Offline regression tests for hosted ESPN Harry Winks report synchronization."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sync_winks_report import normalize


def fixture():
    dates = [
        "2026-10-19T18:45:00+00:00",
        "2026-10-11T18:45:00+00:00",
        "2026-09-19T13:00:00+00:00",
        "2026-09-12T18:45:00+00:00",
        "2026-09-07T16:30:00+00:00",
    ]
    series = [0, 1, 1, 0, 1]
    matches = [
        {
            "event_id": str(401874700 + i),
            "date": date,
            "played": True,
            "player": "Harry Winks",
            "team": "Cagliari",
            "starter": True,
            "total_shots": shots,
            "shots_on_target": 0,
        }
        for i, (date, shots) in enumerate(zip(dates, series))
    ]
    hosted = {
        "league": "ita.1",
        "team_id": "2925",
        "player_id": "202332",
        "five_found": True,
        "five_verified": True,
        "last_five_appearances": matches,
    }
    previous = {"five_shots": {"matches": []}}
    return hosted, previous


class SyncWinksTests(unittest.TestCase):
    def test_zero_shots_remains_verified_zero(self):
        hosted, previous = fixture()
        result = normalize(hosted, previous)
        self.assertEqual(result["five_shots"]["sequence"], [0, 1, 1, 0, 1])
        self.assertTrue(result["five_shots"]["verified"])

    def test_unknown_is_never_zero(self):
        hosted, previous = fixture()
        hosted["last_five_appearances"][0]["total_shots"] = None
        with self.assertRaises(ValueError):
            normalize(hosted, previous)

    def test_shots_on_target_is_separate_and_bounded(self):
        hosted, previous = fixture()
        hosted["last_five_appearances"][0]["shots_on_target"] = 1
        with self.assertRaises(ValueError):
            normalize(hosted, previous)

    def test_wrong_player_rejected(self):
        hosted, previous = fixture()
        hosted["player_id"] = "999999"
        with self.assertRaises(ValueError):
            normalize(hosted, previous)

    def test_incomplete_report_rejected(self):
        hosted, previous = fixture()
        hosted["five_verified"] = False
        with self.assertRaises(ValueError):
            normalize(hosted, previous)

    def test_duplicate_event_rejected(self):
        hosted, previous = fixture()
        hosted["last_five_appearances"][1]["event_id"] = hosted["last_five_appearances"][0]["event_id"]
        with self.assertRaises(ValueError):
            normalize(hosted, previous)

    def test_older_report_rejected(self):
        hosted, previous = fixture()
        previous["five_shots"]["matches"] = [{"date": "2026-10-20T18:45:00+00:00"}]
        with self.assertRaises(ValueError):
            normalize(hosted, previous)


if __name__ == "__main__":
    unittest.main()
