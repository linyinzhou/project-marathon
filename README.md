# Project Marathon

A registration reminder tool for marathon, trail running, and related events in China.

## Goal

- Collect event schedules, registration opening times, registration deadlines, registration platforms, and related details.
- Automatically classify event status: registration upcoming, registration open, closes today, registration closed, or race finished.
- Extend the tool with calendar, email, WeCom, or WeChat reminders in later iterations.

## Current Minimal Version

```powershell
python scripts/fetch_sources.py --date 2026-08-02
python scripts/status.py --date 2026-08-02
```

`fetch_sources.py` collects publicly listed open-registration events and writes them to `data/events.json`.
`status.py` reads `data/events.json` by default, falling back to `data/events.sample.json` when the generated data file is unavailable.

By default, `status.py` displays priority events only: A-class events, events in selected tier-one or tier-two cities, and gold-label, platinum-label, or label events. Use `--all` to inspect every collected event.

The dashboard keeps the main status filters scoped to Chinese road races. The Upcoming filter shows races whose registration starts within the next seven days; they move to Registration Open when the opening date arrives. Open-registration races are ordered by when they were first discovered, with the newest listings first. Selected Japanese races appear in a separate Overseas Events view.

Major Chinese trail races appear in a separate Trail Races view. It displays only the official registration status and race date, sorted chronologically, and hides races held more than six months ago. Event names, dates, and statuses are discovered from the configured organizer websites rather than maintained as a hard-coded race list.

## Automatic Updates

The `Update marathon events` GitHub Actions workflow runs every day at approximately 06:15 China Standard Time. It collects the current event list, rejects empty results, and commits valid changes to `data/events.json`. The dashboard reads that file when the page opens, so newly committed data appears without a separate site deployment.

## Registered Events

`data/registrations.json` stores persistent snapshots of events the user has entered. The dashboard merges these records with the current public event list, marks them as registered, and shows the number of days until or since race day. Keeping a snapshot ensures a registered event remains visible after registration closes or the source listing disappears.

To update registered races without editing files locally:

1. Open the repository's **Actions** tab.
2. Select **Update registered race**.
3. Choose **Run workflow**.
4. Select `add` or `remove` and enter the exact event name shown on the dashboard.

The workflow updates `data/registrations.json` and pushes the change automatically. Adding a race requires it to exist in the latest `data/events.json`; removing a race continues to work after it disappears from the current event feed.

## Data Fields

| Field | Description |
| --- | --- |
| `name` | Event name |
| `race_date` | Race date and time in ISO 8601 format |
| `province` | Province or region |
| `city` | City |
| `country` | Country or region, such as China or Japan |
| `category` | Certification level or event category |
| `discipline` | Event discipline; `trail` identifies trail races |
| `registration_start` | Registration opening time in ISO 8601 format; may be empty |
| `registration_end` | Registration deadline in ISO 8601 format; may be empty |
| `registration_status` | Explicit source status, used when a source reports an open window without exact dates |
| `source_name` | Name of the information source |
| `source_group` | Stable source identifier used to retain the previous successful result after a transient source failure |
| `source_url` | Link to the information source |
| `registration_platform` | Registration platform, such as an official website, Shuxin, or Mala Mala |
| `app_only` | Whether registration is available only in an app |
| `verified` | Whether the record has been cross-checked against an official announcement |
| `last_checked_at` | Last checked time |
| `first_seen_at` | Time the event was first discovered; used to show newly published open-registration events first |
| `notes` | Additional notes |

## Candidate Data Sources

- NowRun event calendar: https://www.nowrun.cn/
- Run in Japan race calendar: https://runinjapan.com/en/calendar
- Tokyo Marathon official website: https://www.marathon.tokyo/en/participants/
- Osaka Marathon official website: https://www.osaka-marathon.com/
- Letour Sports official event list: http://www.letoursport.com/
- Tsaigu official event list: https://tsaigu.com/
- UTMB World Series official calendar: https://utmb.world/en/utmb-world-series-events
- Chongli 168 official website: http://www.chongli-ultra.cn/
- China Marathon event database: https://chinamarathon.com/
- Official event accounts, websites, and official partner registration platforms

Registration information should always be confirmed through official channels. Aggregator sites are useful for discovery, while official announcements should be treated as the final source of truth.
