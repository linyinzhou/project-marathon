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

By default, `status.py` displays priority events only: A-class events, events in selected tier-one or tier-two cities, and gold-label, platinum-label, or label events. Use `--all` to inspect every collected event.

The dashboard keeps the existing status filters scoped to Chinese races and presents selected Japanese races in a separate Overseas Events view with race and registration dates.

## Automatic Updates

The `Update marathon events` GitHub Actions workflow runs every day at approximately 06:15 China Standard Time. It collects the current event list, rejects empty results, and commits valid changes to `data/events.json`. The dashboard reads that file when the page opens, so newly committed data appears without a separate site deployment.

## Registered Events

`data/registrations.json` stores persistent snapshots of events the user has entered. The dashboard merges these records with the current public event list, marks them as registered, and shows the number of days until or since race day. Keeping a snapshot ensures a registered event remains visible after registration closes or the source listing disappears.

## Data Fields

| Field | Description |
| --- | --- |
| `name` | Event name |
| `race_date` | Race date and time in ISO 8601 format |
| `province` | Province or region |
| `city` | City |
| `country` | Country or region, such as China or Japan |
| `category` | Certification level or event category |
| `registration_start` | Registration opening time in ISO 8601 format; may be empty |
| `registration_end` | Registration deadline in ISO 8601 format; may be empty |
| `registration_status` | Explicit source status, used when a source reports an open window without exact dates |
| `source_name` | Name of the information source |
| `source_url` | Link to the information source |
| `registration_platform` | Registration platform, such as an official website, Shuxin, or Mala Mala |
| `app_only` | Whether registration is available only in an app |
| `verified` | Whether the record has been cross-checked against an official announcement |
| `last_checked_at` | Last checked time |
| `notes` | Additional notes |

## Candidate Data Sources

- NowRun event calendar: https://www.nowrun.cn/
- Run in Japan race calendar: https://runinjapan.com/en/calendar
- Tokyo Marathon official website: https://www.marathon.tokyo/en/participants/
- Osaka Marathon official website: https://www.osaka-marathon.com/
- China Marathon event database: https://chinamarathon.com/
- Official event accounts, websites, and official partner registration platforms

Registration information should always be confirmed through official channels. Aggregator sites are useful for discovery, while official announcements should be treated as the final source of truth.
