import argparse
import html
import json
import re
import sys
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path


TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_PATH = ROOT / "data" / "events.json"
NOWRUN_URL = "https://www.nowrun.cn/"


def strip_tags(value):
    value = re.sub(r"<!--.*?-->", "", value, flags=re.S)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def fetch_text(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; project-marathon/0.1; +https://www.nowrun.cn/)",
            "Accept-Language": "zh-CN,zh;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, "replace")


def parse_race_datetime(value):
    match = re.search(r"(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{2})", value)
    if not match:
        return None
    year, month, day, hour, minute = map(int, match.groups())
    return datetime(year, month, day, hour, minute, tzinfo=TZ).isoformat()


def parse_deadline(value, base_date):
    value = value.strip()

    match = re.search(r"今日\s*(\d{1,2}):(\d{2})\s*截止", value)
    if match:
        hour, minute = map(int, match.groups())
        return datetime.combine(base_date, time(hour, minute), tzinfo=TZ).isoformat()

    match = re.search(r"明日\s*(\d{1,2}):(\d{2})\s*截止", value)
    if match:
        hour, minute = map(int, match.groups())
        return datetime.combine(base_date + timedelta(days=1), time(hour, minute), tzinfo=TZ).isoformat()

    match = re.search(r"(\d+)\s*天后截止", value)
    if match:
        days = int(match.group(1))
        return datetime.combine(base_date + timedelta(days=days), time(23, 59), tzinfo=TZ).isoformat()

    match = re.search(r"(\d{4})[.-](\d{1,2})[.-](\d{1,2})(?:\s+(\d{1,2}):(\d{2}))?\s*截止", value)
    if match:
        year, month, day, hour, minute = match.groups()
        return datetime(
            int(year),
            int(month),
            int(day),
            int(hour or 23),
            int(minute or 59),
            tzinfo=TZ,
        ).isoformat()

    return None


def parse_nowrun_open_events(page_html, base_date):
    card_pattern = re.compile(
        r"<h3[^>]*>(?P<name>.*?)</h3>.*?"
        r'<span class="truncate">(?P<race_date>\d{4}\.\d{1,2}\.\d{1,2}\s+\d{1,2}:\d{2})</span>.*?'
        r'<span class="truncate">(?P<province>[^<]+)</span>.*?'
        r'<div class="inline-flex[^>]*>(?P<category>.*?)</div>.*?'
        r'<span class="[^"]*text-orange-300[^"]*">(?P<deadline>.*?)</span>',
        flags=re.S,
    )

    events = []
    checked_at = datetime.now(TZ).isoformat(timespec="seconds")
    for match in card_pattern.finditer(page_html):
        deadline_text = strip_tags(match.group("deadline"))
        event = {
            "name": strip_tags(match.group("name")),
            "race_date": parse_race_datetime(strip_tags(match.group("race_date"))),
            "province": strip_tags(match.group("province")),
            "city": "",
            "category": strip_tags(match.group("category")),
            "registration_start": None,
            "registration_end": parse_deadline(deadline_text, base_date),
            "registration_platform": "",
            "source_name": "闹跑",
            "source_url": NOWRUN_URL,
            "app_only": False,
            "verified": False,
            "last_checked_at": checked_at,
            "notes": f"公开首页报名中卡片：{deadline_text}。需以赛事官方公告复核。",
        }
        if event["name"] and event["race_date"]:
            events.append(event)

    return dedupe_events(events)


def dedupe_events(events):
    seen = set()
    deduped = []
    for event in events:
        key = (event.get("name"), event.get("race_date"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    return deduped


def save_events(events, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser(description="采集公开马拉松/越野赛事报名信息。")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="输出 JSON 文件路径")
    parser.add_argument("--date", default=date.today().isoformat(), help="用于解析“今日/几天后”的基准日期")
    args = parser.parse_args()

    base_date = date.fromisoformat(args.date)
    page_html = fetch_text(NOWRUN_URL)
    events = parse_nowrun_open_events(page_html, base_date)
    save_events(events, args.output)

    print(f"已采集 {len(events)} 场报名中赛事 -> {args.output}")
    for event in events[:10]:
        print(f"- {event['name']} | {event['province']} | {event['race_date']} | 截止 {event['registration_end']}")
    if len(events) > 10:
        print(f"... 还有 {len(events) - 10} 场")


if __name__ == "__main__":
    main()
