# Project Marathon

中国马拉松、越野跑等赛事报名提醒工具。

## 任务目标

- 收集赛事日程、报名开始时间、报名截止时间、报名渠道等信息。
- 自动判断赛事状态：准备报名、今天开始报名、正在报名、今天截止、已截止、已比赛。
- 后续可扩展到日历、邮件、企业微信/微信等提醒方式。

## 当前最小版本

```powershell
python scripts/fetch_sources.py --date 2026-08-02
python scripts/status.py --date 2026-08-02
```

`fetch_sources.py` 会从公开网页采集报名中赛事并写入 `data/events.json`。
`status.py` 默认优先读取 `data/events.json`，如果不存在则读取 `data/events.sample.json`。

## 数据字段

| 字段 | 含义 |
| --- | --- |
| `name` | 赛事名称 |
| `race_date` | 比赛日期时间，ISO 8601 格式 |
| `province` | 省份/地区 |
| `city` | 城市 |
| `category` | 认证级别或赛事类型 |
| `registration_start` | 报名开始时间，ISO 8601 格式，可为空 |
| `registration_end` | 报名截止时间，ISO 8601 格式，可为空 |
| `source_name` | 信息来源名称 |
| `source_url` | 信息来源链接 |
| `registration_platform` | 报名平台，如官网、数字心动、马拉马拉 |
| `app_only` | 是否只能在 App 内报名 |
| `verified` | 是否已经用官方公告复核 |
| `last_checked_at` | 最后检查时间 |
| `notes` | 备注 |

## 候选数据源

- 闹跑赛事日历：https://www.nowrun.cn/
- 中国马拉松赛事库：https://chinamarathon.com/
- 赛事官方公众号、官网或官方合作报名平台。

报名信息应以官方渠道为准，聚合站适合作为发现入口，官方公告适合作为最终校验来源。
