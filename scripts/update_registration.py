import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "data" / "events.json"
REGISTRATIONS_PATH = ROOT / "data" / "registrations.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(items, path):
    with path.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
        f.write("\n")


def update_registrations(events, registrations, action, event_name, checked_at=None):
    event_name = event_name.strip()
    if not event_name:
        raise ValueError("Event name cannot be empty")

    if action == "remove":
        updated = [item for item in registrations if item.get("name") != event_name]
        if len(updated) == len(registrations):
            raise ValueError(f"Registered event not found: {event_name}")
        return updated

    matches = [event for event in events if event.get("name") == event_name]
    if not matches:
        raise ValueError(f"Current event not found: {event_name}")
    if len(matches) > 1:
        dates = ", ".join((event.get("race_date") or "unknown")[:10] for event in matches)
        raise ValueError(f"Event name is ambiguous ({dates}): {event_name}")

    event = matches[0]
    key = (event_name, event.get("race_date"))
    if any((item.get("name"), item.get("race_date")) == key for item in registrations):
        return registrations

    registered_event = dict(event)
    registered_event.update(
        {
            "source_name": "用户已报名",
            "verified": True,
            "last_checked_at": checked_at or datetime.now(TZ).isoformat(timespec="seconds"),
            "notes": "用户通过 GitHub Actions 确认已报名；公开赛事信息需以官方公告复核。",
        }
    )
    return [*registrations, registered_event]


def main():
    parser = argparse.ArgumentParser(description="Add or remove a registered race.")
    parser.add_argument("--action", required=True, choices=("add", "remove"))
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--events", type=Path, default=EVENTS_PATH)
    parser.add_argument("--registrations", type=Path, default=REGISTRATIONS_PATH)
    args = parser.parse_args()

    registrations = load_json(args.registrations)
    updated = update_registrations(
        load_json(args.events), registrations, args.action, args.event_name
    )
    if updated == registrations:
        print(f"No change: {args.event_name}")
        return

    save_json(updated, args.registrations)
    print(f"{args.action}: {args.event_name} -> {args.registrations}")


if __name__ == "__main__":
    main()
