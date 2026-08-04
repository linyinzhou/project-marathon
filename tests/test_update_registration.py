import unittest

from scripts.update_registration import update_registrations


class UpdateRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.event = {
            "name": "2026 Test Marathon",
            "race_date": "2026-10-18T07:30:00+08:00",
            "province": "Test",
            "source_name": "Public source",
            "verified": False,
        }

    def test_add_copies_current_event_and_marks_it_registered(self):
        updated = update_registrations(
            [self.event], [], "add", self.event["name"], "2026-08-04T12:00:00+08:00"
        )
        self.assertEqual(len(updated), 1)
        self.assertEqual(updated[0]["race_date"], self.event["race_date"])
        self.assertEqual(updated[0]["source_name"], "用户已报名")
        self.assertTrue(updated[0]["verified"])

    def test_add_is_idempotent(self):
        registrations = [dict(self.event)]
        self.assertIs(
            update_registrations([self.event], registrations, "add", self.event["name"]),
            registrations,
        )

    def test_remove_does_not_require_current_event(self):
        updated = update_registrations([], [self.event], "remove", self.event["name"])
        self.assertEqual(updated, [])

    def test_unknown_event_fails(self):
        with self.assertRaisesRegex(ValueError, "Current event not found"):
            update_registrations([], [], "add", "Unknown")


if __name__ == "__main__":
    unittest.main()
