import argparse
import json
import sys
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path


TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "data" / "events.json"
SAMPLE_EVENTS_PATH = ROOT / "data" / "events.sample.json"
DEFAULT_EVENTS_PATH = EVENTS_PATH if EVENTS_PATH.exists() else SAMPLE_EVENTS_PATH


STATUS_ORDER = [
    "today_start",
    "today_end",
    "open",
    "upcoming",
    "closed",
    "race_finished",
    "unknown",
]

STATUS_LABELS = {
    "today_start": "今天开始报名",
    "today_end": "今天截止报名",
    "open": "正在报名",
    "upcoming": "准备报名",
    "closed": "报名已截止",
    "race_finished": "比赛已结束",
    "unknown": "状态未知",
}

TIER_ONE_CITIES = ("北京", "上海", "广州", "深圳")
TIER_TWO_CITIES = (
    "成都", "重庆", "杭州", "武汉", "西安", "天津", "苏州", "南京", "长沙", "郑州",
    "东莞", "青岛", "沈阳", "宁波", "昆明", "合肥", "佛山", "福州", "厦门", "济南", "大连",
)
PREMIUM_EVENT_KEYWORDS = {
    "白金标赛事": ("白金标", "白金"),
    "金标赛事": ("金牌", "金标"),
    "标牌赛事": ("标牌",),
}


def parse_dt(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=TZ)
    return parsed.astimezone(TZ)


def day_bounds(target_date):
    start = datetime.combine(target_date, time.min, tzinfo=TZ)
    end = datetime.combine(target_date, time.max, tzinfo=TZ)
    return start, end


def event_status(event, target_date):
    now_start, now_end = day_bounds(target_date)
    race_date = parse_dt(event.get("race_date"))
    reg_start = parse_dt(event.get("registration_start"))
    reg_end = parse_dt(event.get("registration_end"))

    if race_date and race_date < now_start:
        return "race_finished"
    if reg_start and now_start <= reg_start <= now_end:
        return "today_start"
    if reg_end and now_start <= reg_end <= now_end:
        return "today_end"
    if reg_start and reg_start > now_end:
        return "upcoming"
    if reg_end and reg_end < now_start:
        return "closed"
    if reg_end and reg_end > now_end:
        return "open"
    return "unknown"


def load_events(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def format_date(value):
    parsed = parse_dt(value)
    if not parsed:
        return "-"
    return parsed.strftime("%Y-%m-%d %H:%M")


def priority_reasons(event):
    reasons = []
    if event.get("category") == "A类":
        reasons.append("A类")

    search_text = " ".join(
        str(event.get(field) or "") for field in ("name", "province", "city", "category", "notes")
    )
    if any(city in search_text for city in TIER_ONE_CITIES):
        reasons.append("一线城市")
    elif any(city in search_text for city in TIER_TWO_CITIES):
        reasons.append("二线城市")

    for label, keywords in PREMIUM_EVENT_KEYWORDS.items():
        if any(keyword in search_text for keyword in keywords):
            reasons.append(label)
    return reasons


def print_grouped(events, target_date, include_all=False):
    grouped = defaultdict(list)
    for event in events:
        reasons = priority_reasons(event)
        if not include_all and not reasons:
            continue
        event["display_reasons"] = reasons
        grouped[event_status(event, target_date)].append(event)

    scope = "全部赛事" if include_all else "重点赛事"
    print(f"赛事报名状态快照：{target_date.isoformat()}（{scope}）")
    for status in STATUS_ORDER:
        items = grouped.get(status, [])
        if not items:
            continue
        print()
        print(f"## {STATUS_LABELS[status]}（{len(items)}）")
        for event in sorted(items, key=lambda item: item.get("registration_end") or item.get("race_date") or ""):
            location = " ".join(filter(None, [event.get("province"), event.get("city")]))
            print(
                f"- {event['name']} | {location or '-'} | 比赛 {format_date(event.get('race_date'))} "
                f"| 报名 {format_date(event.get('registration_start'))} -> {format_date(event.get('registration_end'))}"
            )
            if event["display_reasons"]:
                print(f"  入选：{'、'.join(event['display_reasons'])}")
            if event.get("source_url"):
                print(f"  来源：{event.get('source_name', '-')}: {event['source_url']}")
            if event.get("notes"):
                print(f"  备注：{event['notes']}")


def main():
    parser = argparse.ArgumentParser(description="按日期计算马拉松/越野赛事报名状态。")
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS_PATH, help="赛事 JSON 文件路径")
    parser.add_argument("--date", default=date.today().isoformat(), help="目标日期，格式 YYYY-MM-DD")
    parser.add_argument("--all", action="store_true", help="显示所有赛事，不进行重点赛事筛选")
    args = parser.parse_args()

    target_date = date.fromisoformat(args.date)
    events = load_events(args.events)
    print_grouped(events, target_date, include_all=args.all)


if __name__ == "__main__":
    main()
