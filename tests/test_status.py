import unittest
from datetime import date

from scripts.status import event_status


class EventStatusTests(unittest.TestCase):
    def test_future_registration_is_upcoming(self):
        event = {
            "race_date": "2027-03-07T00:00:00+08:00",
            "registration_start": "2026-08-14T11:00:00+08:00",
            "registration_end": "2026-08-28T17:00:00+08:00",
        }
        self.assertEqual(event_status(event, date(2026, 8, 3)), "upcoming")

    def test_explicit_open_status_without_dates(self):
        event = {
            "race_date": "2026-12-13T00:00:00+08:00",
            "registration_start": None,
            "registration_end": None,
            "registration_status": "open",
        }
        self.assertEqual(event_status(event, date(2026, 8, 3)), "open")


if __name__ == "__main__":
    unittest.main()
