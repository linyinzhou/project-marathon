import argparse
import html
import json
import re
import subprocess
import sys
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path


TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_PATH = ROOT / "data" / "events.json"
NOWRUN_URL = "https://www.nowrun.cn/"
RUN_IN_JAPAN_URL = "https://runinjapan.com/en/calendar?tab=register"
TOKYO_MARATHON_URL = "https://www.marathon.tokyo/en/participants/"
OSAKA_MARATHON_URL = "https://www.osaka-marathon.com/2027/en/runner/entry/admission/"
LETOUR_URL = "http://www.letoursport.com/"
TSAIGU_URL = "https://tsaigu.com/"
UTMB_EVENTS_URL = "https://utmb.world/en/utmb-world-series-events"
CHONGLI_168_URL = (
    "https://sport.luojiweiye.com/api/H5/website/nav_info"
    "?id=968&type=1&website_id=9"
)
ENGLISH_MONTHS = {
    month: index
    for index, month in enumerate(
        (
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ),
        start=1,
    )
}
MONTH_PATTERN = "|".join(ENGLISH_MONTHS)
RUN_IN_JAPAN_PRIORITY_KEYWORDS = (
    "Tokyo Marathon",
    "Osaka Marathon",
    "Hokkaido Marathon",
    "Kyoto Marathon",
    "Kobe Marathon",
    "Fukuoka Marathon",
    "Kanazawa Marathon",
    "Nagoya Women's Marathon",
    "Yokohama Marathon",
    "Mt. Fuji Marathon",
    "Mount Fuji Marathon",
    "Shonan International Marathon",
)


def strip_tags(value):
    value = re.sub(r"<!--.*?-->", "", value, flags=re.S)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def normalize_text(value):
    return re.sub(r"\s+", " ", strip_tags(value)).strip()


def fetch_text(url):
    timeout = 120 if url == UTMB_EVENTS_URL else 30
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; project-marathon/0.1; +https://www.nowrun.cn/)",
            "Accept-Language": "zh-CN,zh;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, "replace")
    except Exception as urllib_error:
        result = subprocess.run(
            [
                "curl",
                "--fail",
                "--location",
                "--silent",
                "--show-error",
                "--max-time",
                str(timeout),
                "--header",
                "Accept-Language: en,zh-CN;q=0.9",
                "--user-agent",
                "Mozilla/5.0 (compatible; project-marathon/0.1)",
                url,
            ],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            error = result.stderr.decode("utf-8", "replace").strip()
            raise RuntimeError(f"urllib: {urllib_error}; curl: {error}") from urllib_error
        return result.stdout.decode("utf-8", "replace")


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
            "country": "中国",
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


def english_datetime(month, day, year, hour=0, minute=0, meridiem=None):
    hour = int(hour)
    if meridiem:
        normalized = meridiem.lower().replace(".", "")
        if normalized == "pm" and hour != 12:
            hour += 12
        elif normalized == "am" and hour == 12:
            hour = 0
    return datetime(
        int(year), ENGLISH_MONTHS[month], int(day), hour, int(minute), tzinfo=TZ
    ).isoformat()


def parse_tokyo_marathon(page_html, _base_date):
    text = normalize_text(page_html)
    year_match = re.search(r"TOKYO MARATHON\s+(20\d{2})", text, flags=re.I)
    if not year_match:
        raise ValueError("Tokyo Marathon year not found")
    race_year = year_match.group(1)
    race_match = re.search(rf"({MONTH_PATTERN})\s+(\d{{1,2}}),\s*{race_year}", text)
    period_match = re.search(
        rf"General Entry\s*\(Including.*?\)\s*Entry Period.*?"
        rf"From\s+(\d{{1,2}}):(\d{{2}})\s*([ap]\.m\.)"
        rf"\s+on\s+({MONTH_PATTERN})\s+(\d{{1,2}}).*?until\s+"
        rf"(\d{{1,2}}):(\d{{2}})\s*([ap]\.m\.)\s+on\s+"
        rf"({MONTH_PATTERN})\s+(\d{{1,2}}).*?,\s*(20\d{{2}})",
        text,
        flags=re.I,
    )
    if not race_match or not period_match:
        raise ValueError("Tokyo Marathon race date or general entry period not found")

    (
        start_hour,
        start_minute,
        start_meridiem,
        start_month,
        start_day,
        end_hour,
        end_minute,
        end_meridiem,
        end_month,
        end_day,
        entry_year,
    ) = period_match.groups()
    return [
        {
            "name": f"Tokyo Marathon {race_year}",
            "race_date": english_datetime(race_match.group(1), race_match.group(2), race_year),
            "race_time_known": False,
            "province": "Tokyo",
            "city": "Tokyo",
            "country": "日本",
            "category": "日本重点赛事",
            "registration_start": english_datetime(
                start_month, start_day, entry_year, start_hour, start_minute, start_meridiem
            ),
            "registration_end": english_datetime(
                end_month, end_day, entry_year, end_hour, end_minute, end_meridiem
            ),
            "registration_platform": "Tokyo Marathon official website",
            "source_name": "Tokyo Marathon official website",
            "source_url": TOKYO_MARATHON_URL,
            "app_only": False,
            "verified": True,
            "last_checked_at": datetime.now(TZ).isoformat(timespec="seconds"),
            "notes": "General entry window from the official Tokyo Marathon website.",
        }
    ]


def parse_osaka_marathon(page_html, _base_date):
    text = normalize_text(page_html)
    year_match = re.search(r"Osaka Marathon\s+(20\d{2})", text, flags=re.I)
    race_match = re.search(
        rf"Date\s*&\s*Time.*?({MONTH_PATTERN})\s+(\d{{1,2}}),\s*(20\d{{2}}).*?"
        rf"(\d{{1,2}}):(\d{{2}})\s*([AP]M)",
        text,
        flags=re.I,
    )
    period_match = re.search(
        rf"General runners.*?From\s+\w+,\s+({MONTH_PATTERN})\s+(\d{{1,2}}),\s*(20\d{{2}})"
        rf"\s+at\s+(\d{{1,2}}):(\d{{2}})\s*([AP]M)\s+to\s+\w+,\s+"
        rf"({MONTH_PATTERN})\s+(\d{{1,2}}),\s*(20\d{{2}})\s+at\s+"
        rf"(\d{{1,2}}):(\d{{2}})\s*([AP]M)",
        text,
        flags=re.I,
    )
    if not year_match or not race_match or not period_match:
        raise ValueError("Osaka Marathon race date or general entry period not found")

    (
        start_month,
        start_day,
        start_year,
        start_hour,
        start_minute,
        start_meridiem,
        end_month,
        end_day,
        end_year,
        end_hour,
        end_minute,
        end_meridiem,
    ) = period_match.groups()
    return [
        {
            "name": f"Osaka Marathon {year_match.group(1)}",
            "race_date": english_datetime(*race_match.groups()),
            "province": "Osaka",
            "city": "Osaka",
            "country": "日本",
            "category": "日本重点赛事",
            "registration_start": english_datetime(
                start_month, start_day, start_year, start_hour, start_minute, start_meridiem
            ),
            "registration_end": english_datetime(
                end_month, end_day, end_year, end_hour, end_minute, end_meridiem
            ),
            "registration_platform": "RUNNET / JTB Sports Station",
            "source_name": "Osaka Marathon official website",
            "source_url": OSAKA_MARATHON_URL,
            "app_only": False,
            "verified": True,
            "last_checked_at": datetime.now(TZ).isoformat(timespec="seconds"),
            "notes": "General runner entry window from the official Osaka Marathon website.",
        }
    ]


class RunInJapanCalendarParser(HTMLParser):
    def __init__(self, base_date):
        super().__init__(convert_charrefs=True)
        self.base_date = base_date
        self.depth = 0
        self.month = None
        self.year = None
        self.day = None
        self.capture = {}
        self.anchor = None
        self.events = []

    def handle_starttag(self, tag, attrs):
        self.depth += 1
        attributes = dict(attrs)
        classes = attributes.get("class", "")
        if tag == "span" and "uppercase tracking-[0.18em]" in classes:
            self.capture["month"] = [self.depth, []]
        elif tag == "div" and "tabular-nums font-medium text-neutral-500" in classes:
            self.capture["day"] = [self.depth, []]
        elif (
            tag == "a"
            and attributes.get("href", "").startswith("/en/races/")
            and "group block rounded-md" in classes
        ):
            self.anchor = {
                "depth": self.depth,
                "href": attributes["href"],
                "name": "",
                "location": "",
                "text": [],
                "status": "",
            }
        elif self.anchor and tag == "span" and "block font-semibold text-neutral-800" in classes:
            self.capture["name"] = [self.depth, []]
        elif self.anchor and tag == "span" and classes == "truncate" and not self.anchor["location"]:
            self.capture["location"] = [self.depth, []]
        if self.anchor and attributes.get("data-testid") == "entry-availability-badge":
            self.anchor["status"] = attributes.get("data-status", "")

    def handle_data(self, data):
        for capture in self.capture.values():
            capture[1].append(data)
        if self.anchor:
            self.anchor["text"].append(data)

    def handle_endtag(self, tag):
        for key, capture in list(self.capture.items()):
            if capture[0] == self.depth:
                value = normalize_text("".join(capture[1]))
                if key == "month":
                    match = re.fullmatch(rf"({MONTH_PATTERN})\s+(20\d{{2}})", value)
                    if match:
                        self.month = ENGLISH_MONTHS[match.group(1)]
                        self.year = int(match.group(2))
                elif key == "day" and value.isdigit():
                    self.day = int(value)
                elif self.anchor:
                    self.anchor[key] = value
                del self.capture[key]

        if self.anchor and self.anchor["depth"] == self.depth and tag == "a":
            self._finish_anchor()
            self.anchor = None
        self.depth -= 1

    def _finish_anchor(self):
        if not all((self.month, self.year, self.day, self.anchor["name"])):
            return
        if not any(keyword.casefold() in self.anchor["name"].casefold() for keyword in RUN_IN_JAPAN_PRIORITY_KEYWORDS):
            return

        location = self.anchor["location"].replace("<!-- -->", "")
        parts = [part.strip() for part in location.split("·")]
        category = parts[0] if parts else ""
        province = parts[-1] if len(parts) > 1 else ""
        all_text = normalize_text(" ".join(self.anchor["text"]))
        days_left = re.search(r"(\d+)\s+days?\s+left", all_text, flags=re.I)
        registration_end = None
        if days_left:
            registration_end = datetime.combine(
                self.base_date + timedelta(days=int(days_left.group(1))),
                time(23, 59),
                tzinfo=TZ,
            ).isoformat()

        self.events.append(
            {
                "name": self.anchor["name"],
                "race_date": datetime(
                    self.year, self.month, self.day, tzinfo=TZ
                ).isoformat(),
                "race_time_known": False,
                "province": province,
                "city": "",
                "country": "日本",
                "category": "日本重点赛事",
                "registration_start": None,
                "registration_end": registration_end,
                "registration_status": "open",
                "registration_platform": "Run in Japan linked entry channel",
                "source_name": "Run in Japan",
                "source_url": f"https://runinjapan.com{self.anchor['href']}",
                "app_only": False,
                "verified": False,
                "last_checked_at": datetime.now(TZ).isoformat(timespec="seconds"),
                "notes": f"Run in Japan listing ({category or 'race'}; {self.anchor['status'] or 'entry status unverified'}). Confirm with the official race website.",
            }
        )


def parse_run_in_japan(page_html, base_date):
    parser = RunInJapanCalendarParser(base_date)
    parser.feed(page_html)
    return dedupe_events(parser.events)


def trail_event(name, race_date, registration_status, source_name, source_url, **extra):
    return {
        "name": name,
        "race_date": race_date,
        "race_time_known": False,
        "province": extra.get("province", ""),
        "city": extra.get("city", ""),
        "country": "中国",
        "category": "越野赛",
        "discipline": "trail",
        "registration_start": None,
        "registration_end": None,
        "registration_status": registration_status,
        "registration_platform": source_name,
        "source_name": source_name,
        "source_group": extra.get("source_group", source_name),
        "source_url": source_url,
        "app_only": False,
        "verified": True,
        "last_checked_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "notes": extra.get("notes", "Registration status and race date from the official website."),
    }


def parse_official_date(value):
    match = re.search(r"(20\d{2})[年./-](\d{1,2})[月./-](\d{1,2})", value)
    if not match:
        return None
    return datetime(*map(int, match.groups()), tzinfo=TZ).isoformat()


def registration_status_from_text(text, race_date, base_date):
    if race_date and parse_dt_date(race_date) < base_date:
        return "closed"
    labels = {
        "报名已截止": "closed",
        "我要报名": "open",
        "报名未开始": "upcoming",
        "即将开始": "upcoming",
        "敬请期待": "upcoming",
    }
    hits = [(text.find(label), status) for label, status in labels.items() if label in text]
    return min(hits)[1] if hits else "unknown"


def parse_dt_date(value):
    return datetime.fromisoformat(value).astimezone(TZ).date()


def parse_organizer_event(page_html, base_date, name, source_name, source_url, source_group):
    text = normalize_text(page_html)
    configured_title = re.search(r"\$CONFIG\.title\s*=\s*['\"]([^'\"]+)", page_html)
    if configured_title:
        page_title = html.unescape(configured_title.group(1)).strip()
        if not page_title.startswith("【"):
            name = page_title
    year_match = re.search(r"(20\d{2})", name)
    date_match = re.search(
        r"(?<!\d)(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])\s*[-至—]\s*"
        r"(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])(?!\d)",
        text,
    )
    if not year_match or not date_match:
        date_match = re.search(
            r"出发时间\s*[:：]?\s*(20\d{2})年(\d{1,2})月(\d{1,2})日", text
        )
        if not date_match:
            raise ValueError(f"race date not found for {name}")
        year, month, day = map(int, date_match.groups())
    else:
        year = int(year_match.group(1))
        month, day = map(int, date_match.groups()[:2])
    race_date = datetime(year, month, day, tzinfo=TZ).isoformat()
    status = registration_status_from_text(text, race_date, base_date)
    return trail_event(
        name, race_date, status, source_name, source_url, source_group=source_group
    )


def organizer_links(page_html, base_url, keywords):
    links = []
    pattern = re.compile(
        r"<a\b[^>]*href=['\"](?P<href>/events\?mid=\d+)['\"][^>]*>(?P<body>.*?)</a>",
        flags=re.I | re.S,
    )
    for match in pattern.finditer(page_html):
        name = normalize_text(match.group("body"))
        if name and any(keyword in name for keyword in keywords):
            links.append((name, base_url.rstrip("/") + match.group("href")))
    return list(dict.fromkeys(links))


def collect_letour(page_html, base_date, fetcher=fetch_text):
    links = organizer_links(page_html, LETOUR_URL, ("越野", "跑山", "100"))
    events = []
    for name, url in links:
        if not re.search(r"20\d{2}", name):
            continue
        try:
            events.append(parse_organizer_event(
                fetcher(url), base_date, name, "朗途体育官网", url, "朗途体育官网"
            ))
        except (RuntimeError, ValueError):
            continue
    return dedupe_events(events)


def collect_tsaigu(page_html, base_date, fetcher=fetch_text):
    links = organizer_links(page_html, TSAIGU_URL, ("柴古", "越野", "蜀道"))
    events = []
    for name, url in links:
        try:
            events.append(parse_organizer_event(
                fetcher(url), base_date, name, "柴古唐斯官网", url, "柴古唐斯官网"
            ))
        except (RuntimeError, ValueError):
            continue
    return dedupe_events(events)


def parse_utmb_china(page_html, _base_date):
    decoder = json.JSONDecoder()
    events = []
    cursor = 0
    while True:
        start = page_html.find('{"continent":', cursor)
        if start < 0:
            break
        cursor = start + 1
        try:
            item, consumed = decoder.raw_decode(page_html[start:])
            cursor = start + consumed
        except json.JSONDecodeError:
            continue
        if item.get("country") not in ("China", "Hong Kong, China"):
            continue
        source_status = (item.get("status") or {}).get("status", "")
        race_date = parse_official_date(item.get("dateBegin", ""))
        if race_date and parse_dt_date(race_date) < _base_date:
            status = "closed"
        elif source_status == "registration_open":
            status = "open"
        elif source_status == "available_soon":
            status = "upcoming"
        elif source_status:
            status = "closed"
        else:
            status = "unknown"
        if item.get("title") and race_date:
            events.append(trail_event(
                item["title"], race_date, status, "UTMB World Series官网",
                item.get("url") or UTMB_EVENTS_URL, source_group="UTMB World Series官网",
                city=item.get("placeName", ""),
            ))
    return dedupe_events(events)


def parse_chongli_168(payload, base_date):
    data = json.loads(payload).get("data") or {}
    text = normalize_text(data.get("content", ""))
    name_match = re.search(r"((?:[^\s]+\s*)?20\d{2}崇礼168[^\s]*越野赛)", text)
    date_match = re.search(r"(20\d{2})年(\d{1,2})月(\d{1,2})日\s*[-至—]\s*(\d{1,2})日", text)
    if not name_match or not date_match:
        raise ValueError("Chongli 168 name or race date not found")
    year, month, day = map(int, date_match.groups()[:3])
    race_date = datetime(year, month, day, tzinfo=TZ).isoformat()
    status = registration_status_from_text(text, race_date, base_date)
    return [trail_event(
        name_match.group(1), race_date, status, "崇礼168官网", CHONGLI_168_URL,
        source_group="崇礼168官网", province="河北", city="张家口",
    )]


def dedupe_events(events):
    seen = set()
    deduped = []
    for event in events:
        key = ((event.get("name") or "").casefold(), (event.get("race_date") or "")[:10])
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


def load_existing_events(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="采集公开马拉松/越野赛事报名信息。")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="输出 JSON 文件路径")
    parser.add_argument("--date", default=date.today().isoformat(), help="用于解析“今日/几天后”的基准日期")
    args = parser.parse_args()

    base_date = date.fromisoformat(args.date)
    sources = (
        ("闹跑", NOWRUN_URL, parse_nowrun_open_events, "闹跑"),
        ("东京马拉松官网", TOKYO_MARATHON_URL, parse_tokyo_marathon, "Tokyo Marathon official website"),
        ("大阪马拉松官网", OSAKA_MARATHON_URL, parse_osaka_marathon, "Osaka Marathon official website"),
        ("Run in Japan", RUN_IN_JAPAN_URL, parse_run_in_japan, "Run in Japan"),
        ("朗途体育官网", LETOUR_URL, collect_letour, "朗途体育官网"),
        ("柴古唐斯官网", TSAIGU_URL, collect_tsaigu, "柴古唐斯官网"),
        ("UTMB World Series官网", UTMB_EVENTS_URL, parse_utmb_china, "UTMB World Series官网"),
        ("崇礼168官网", CHONGLI_168_URL, parse_chongli_168, "崇礼168官网"),
    )
    existing_events = load_existing_events(args.output)
    events = []
    missing_sources = []
    for source_name, url, parser_function, persisted_source_name in sources:
        try:
            source_events = parser_function(fetch_text(url), base_date)
            if not source_events:
                raise ValueError("未解析到赛事")
            events.extend(source_events)
            print(f"{source_name}: {len(source_events)} 场")
        except Exception as exc:
            retained = [
                event
                for event in existing_events
                if event.get("source_group", event.get("source_name")) == persisted_source_name
            ]
            if retained:
                events.extend(retained)
                print(
                    f"警告：{source_name}采集失败，保留上次 {len(retained)} 场数据：{exc}",
                    file=sys.stderr,
                )
            else:
                missing_sources.append(f"{source_name}: {exc}")

    if missing_sources:
        raise RuntimeError("来源采集失败且没有历史数据：" + "; ".join(missing_sources))

    events = dedupe_events(events)
    if not events:
        raise RuntimeError("所有赛事来源均未返回有效数据")
    save_events(events, args.output)

    print(f"已采集 {len(events)} 场报名中赛事 -> {args.output}")
    for event in events[:10]:
        print(f"- {event['name']} | {event['province']} | {event['race_date']} | 截止 {event['registration_end']}")
    if len(events) > 10:
        print(f"... 还有 {len(events) - 10} 场")


if __name__ == "__main__":
    main()
