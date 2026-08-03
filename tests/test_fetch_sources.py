import unittest
from datetime import date

from scripts.fetch_sources import (
    parse_osaka_marathon,
    parse_run_in_japan,
    parse_tokyo_marathon,
)


class JapanSourceParserTests(unittest.TestCase):
    def test_tokyo_general_entry_period(self):
        page = """
        <h1>TOKYO MARATHON 2027</h1><a>March 7, 2027</a>
        <h3>General Entry</h3>
        <p>(Including People with Disabilities)</p><h4>Entry Period</h4>
        <p>From 11:00 a.m. on August 14(Fri.) until 5:00 p.m. on August 28(Fri.), 2026.</p>
        """
        event = parse_tokyo_marathon(page, date(2026, 8, 3))[0]
        self.assertEqual(event["race_date"], "2027-03-07T00:00:00+08:00")
        self.assertEqual(event["registration_start"], "2026-08-14T11:00:00+08:00")
        self.assertEqual(event["registration_end"], "2026-08-28T17:00:00+08:00")

    def test_osaka_general_entry_period(self):
        page = """
        <h1>Osaka Marathon 2027</h1>
        <dt>Date &amp; Time</dt><dd>Sunday, February 28, 2027 9:15 AM</dd>
        <p>General runners</p>
        <p>From Tuesday, July 28, 2026 at 10:00 AM to Friday, August 28, 2026 at 5:00 PM</p>
        """
        event = parse_osaka_marathon(page, date(2026, 8, 3))[0]
        self.assertEqual(event["race_date"], "2027-02-28T09:15:00+08:00")
        self.assertEqual(event["registration_start"], "2026-07-28T10:00:00+08:00")
        self.assertEqual(event["registration_end"], "2026-08-28T17:00:00+08:00")

    def test_run_in_japan_keeps_priority_races_only(self):
        page = """
        <span class="uppercase tracking-[0.18em]">December 2026</span>
        <div class="tabular-nums font-medium text-neutral-500">13</div>
        <a class="group block rounded-md" href="/en/races/mt_fuji_2026">
          <span class="block font-semibold text-neutral-800 truncate">15th Mt. Fuji Marathon</span>
          <span class="truncate">Full · 山梨</span>
          <span data-testid="entry-availability-badge" data-status="date_window_open">Open</span>
        </a>
        <div class="tabular-nums font-medium text-neutral-500">20</div>
        <a class="group block rounded-md" href="/en/races/small_race_2026">
          <span class="block font-semibold text-neutral-800 truncate">Small Local Run</span>
          <span class="truncate">Other · 東京</span>
        </a>
        """
        events = parse_run_in_japan(page, date(2026, 8, 3))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["name"], "15th Mt. Fuji Marathon")
        self.assertEqual(events[0]["race_date"], "2026-12-13T00:00:00+08:00")
        self.assertEqual(events[0]["registration_status"], "open")


if __name__ == "__main__":
    unittest.main()
