import unittest
from datetime import date

from scripts.fetch_sources import (
    add_first_seen_at,
    collect_letour,
    parse_chongli_168,
    parse_osaka_marathon,
    parse_run_in_japan,
    parse_tokyo_marathon,
    parse_utmb_china,
)


class JapanSourceParserTests(unittest.TestCase):
    def test_first_seen_time_is_preserved_for_existing_events(self):
        events = [{"name": "Race", "race_date": "2026-10-01T00:00:00+08:00", "last_checked_at": "new"}]
        existing = [{"name": "Race", "race_date": "2026-10-01T08:00:00+08:00", "first_seen_at": "original"}]
        self.assertEqual(add_first_seen_at(events, existing)[0]["first_seen_at"], "original")

    def test_first_seen_time_uses_initial_check_for_new_events(self):
        events = [{"name": "New Race", "race_date": "2026-10-01T00:00:00+08:00", "last_checked_at": "initial"}]
        self.assertEqual(add_first_seen_at(events, [])[0]["first_seen_at"], "initial")

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

    def test_letour_discovers_current_trail_events(self):
        index = '<a href="/events?mid=42">2026测试100越野赛</a>'
        detail = "$CONFIG.title = '2026测试100越野赛'; 浙江 10/24 - 10/25 我要报名"
        events = collect_letour(index, date(2026, 8, 3), lambda _url: detail)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["race_date"], "2026-10-24T00:00:00+08:00")
        self.assertEqual(events[0]["registration_status"], "open")
        self.assertEqual(events[0]["discipline"], "trail")

    def test_letour_ignores_age_date_and_invitation_channel_title(self):
        index = '<a href="/events?mid=43">2026贡嘎100冰川极限挑战赛</a>'
        detail = """
        $CONFIG.title = '【大众抽签】2026贡嘎100冰川极限挑战赛';
        参赛选手须在2008年9月26日以前出生。
        出发时间：2026年9月26日 0:00。报名已截止。
        """
        event = collect_letour(index, date(2026, 8, 3), lambda _url: detail)[0]
        self.assertEqual(event["name"], "2026贡嘎100冰川极限挑战赛")
        self.assertEqual(event["race_date"], "2026-09-26T00:00:00+08:00")

    def test_utmb_filters_china_from_structured_events(self):
        page = """
        {"continent":"Asia","country":"China","dateBegin":"2026-09-11","title":"Great Wall by UTMB","placeName":"Dajingmen","url":"https://example.cn","status":{"open":true,"status":"registration_open"}}
        {"continent":"Asia","country":"Japan","dateBegin":"2026-10-01","title":"Japan Trail","status":{"open":true,"status":"registration_open"}}
        """
        events = parse_utmb_china(page, date(2026, 8, 3))
        self.assertEqual([event["name"] for event in events], ["Great Wall by UTMB"])
        self.assertEqual(events[0]["registration_status"], "open")

    def test_chongli_reads_name_and_date_from_official_payload(self):
        payload = '{"data":{"content":"<b>耐克ACG 2026崇礼168超级越野赛</b><p>2026年7月10日-12日</p>"}}'
        event = parse_chongli_168(payload, date(2026, 8, 3))[0]
        self.assertEqual(event["race_date"], "2026-07-10T00:00:00+08:00")
        self.assertEqual(event["registration_status"], "closed")


if __name__ == "__main__":
    unittest.main()
