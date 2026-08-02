# Project Marathon

A registration reminder tool for marathon, trail running, and related events in China.

## Goal

- Collect event schedules, registration opening times, registration deadlines, registration platforms, and related details.
- Automatically classify event status: registration upcoming, opens today, registration open, closes today, registration closed, or race finished.
- Extend the tool with calendar, email, WeCom, or WeChat reminders in later iterations.

## Current Minimal Version

```powershell
python scripts/fetch_sources.py --date 2026-08-02
python scripts/status.py --date 2026-08-02
```

`fetch_sources.py` collects publicly listed open-registration events and writes them to `data/events.json`.
`status.py` reads `data/events.json` by default, falling back to `data/events.sample.json` when the generated data file is unavailable.

By default, `status.py` displays priority events only: A-class events, events in selected tier-one or tier-two cities, and events marked as gold, platinum, or championship events. Use `--all` to inspect every collected event.

## Data Fields

| Field | Description |
| --- | --- |
| `name` | Event name |
| `race_date` | Race date and time in ISO 8601 format |
| `province` | Province or region |
| `city` | City |
| `category` | Certification level or event category |
| `registration_start` | Registration opening time in ISO 8601 format; may be empty |
| `registration_end` | Registration deadline in ISO 8601 format; may be empty |
| `source_name` | Name of the information source |
| `source_url` | Link to the information source |
| `registration_platform` | Registration platform, such as an official website, Shuxin, or Mala Mala |
| `app_only` | Whether registration is available only in an app |
| `verified` | Whether the record has been cross-checked against an official announcement |
| `last_checked_at` | Last checked time |
| `notes` | Additional notes |

## Candidate Data Sources

- NowRun event calendar: https://www.nowrun.cn/
- China Marathon event database: https://chinamarathon.com/
- Official event accounts, websites, and official partner registration platforms

Registration information should always be confirmed through official channels. Aggregator sites are useful for discovery, while official announcements should be treated as the final source of truth.
