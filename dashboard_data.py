from __future__ import annotations

import base64
import concurrent.futures
import hashlib
import json
import secrets
import socket
import struct
import subprocess
import time as time_module
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "Asia/Shanghai"
KNOWN_STAGE_KEYS = {
    "简历初筛": "resume_screening",
    "Resume screening": "resume_screening",
    "简历评估": "resume_evaluation",
    "Resume evaluation": "resume_evaluation",
    "初面邀约": "initial_invite",
    "专业一面": "interview_1",
    "Interview": "interview_1",
    "专业二面": "interview_2",
    "HR面": "hr_interview",
    "Offer沟通": "offer",
    "Offer": "offer",
    "待入职": "pending_onboard",
    "To be onboarded": "pending_onboard",
    "已入职": "onboarded",
    "Onboarded": "onboarded",
}
STAGE_KEY_LABELS = {
    "resume_screening": "进入「简历初筛」阶段",
    "resume_evaluation": "进入「简历评估」阶段",
    "initial_invite": "进入「初面邀约」阶段",
    "interview_1": "进入「专业一面」阶段",
    "interview_2": "进入「专业二面」阶段",
    "hr_interview": "进入「HR面」阶段",
    "offer": "进入「Offer沟通」阶段",
    "pending_onboard": "进入「待入职」阶段",
    "onboarded": "进入「已入职」阶段",
}
STAGE_ORDER = [
    "resume_screening",
    "resume_evaluation",
    "initial_invite",
    "interview_1",
    "interview_2",
    "hr_interview",
    "offer",
    "pending_onboard",
    "onboarded",
]
SUMMARY_STAGE_FIELDS = {
    "resume_screening": "stageName_7483922292361365798",
    "assigned_evaluation": "appEvaluationCount",
    "initial_invite": "stageName_7487173396766968091",
    "interview_1": "stageName_7483922292361398566",
    "conduct_interview_1": "interviewRound1Enter",
    "interview_2": "stageName_7484986929462872370",
    "hr_interview": "stageName_7484987042608285962",
    "onboarded": "stageName_7483922292361447718",
}
HR_STATUS_ORDER = {
    "accept": 1,
    "pending": 2,
    "decline": 3,
    "reject": 4,
}

OVERVIEW_WIDGET_KEY = "7573581011003378631"
SPECIAL_WIDGET_KEY = "7621814275148876744"
OVERVIEW_MEASURES = [
    {"data": None, "key": "appJobName", "rawKey": "appJobName"},
    {"data": None, "key": "jobChargeUser", "rawKey": "jobChargeUser"},
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": [
                "7483922292361464102",
                "7485040846077905215",
                "7483922292361480486",
                "7484988241876896009",
                "7484988149308803338",
            ],
            "rankMap": {
                "7483922292361464102": 0,
                "7483922292361480486": 0,
                "7484988149308803338": 0,
                "7484988241876896009": 0,
                "7485040846077905215": 0,
            },
            "stageId": None,
            "stageIdStr": "7483922292361365798",
            "stageType": 1,
        },
        "key": "stageName_7483922292361365798",
        "rawKey": "stageName",
    },
    {"data": None, "key": "appEvaluationCount", "rawKey": "appEvaluationCount"},
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": [
                "7483922292361464102",
                "7485040846077905215",
                "7483922292361480486",
                "7484988241876896009",
            ],
            "rankMap": {
                "7483922292361464102": 2,
                "7483922292361480486": 2,
                "7484988241876896009": 2,
                "7485040846077905215": 2,
            },
            "stageId": None,
            "stageIdStr": "7487173396766968091",
            "stageType": 8,
        },
        "key": "stageName_7487173396766968091",
        "rawKey": "stageName",
    },
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": [
                "7483922292361464102",
                "7485040846077905215",
                "7483922292361480486",
                "7484988241876896009",
                "7484988149308803338",
            ],
            "rankMap": {
                "7483922292361464102": 3,
                "7483922292361480486": 3,
                "7484988149308803338": 2,
                "7484988241876896009": 4,
                "7485040846077905215": 3,
            },
            "stageId": None,
            "stageIdStr": "7483922292361398566",
            "stageType": 4,
        },
        "key": "stageName_7483922292361398566",
        "rawKey": "stageName",
    },
    {"data": None, "key": "interviewRound1Enter", "rawKey": "interviewRound1Enter"},
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": [
                "7483922292361464102",
                "7485040846077905215",
                "7483922292361480486",
            ],
            "rankMap": {
                "7483922292361464102": 4,
                "7483922292361480486": 4,
                "7485040846077905215": 4,
            },
            "stageId": None,
            "stageIdStr": "7484986929462872370",
            "stageType": 4,
        },
        "key": "stageName_7484986929462872370",
        "rawKey": "stageName",
    },
    {"data": None, "key": "interviewRound2Enter", "rawKey": "interviewRound2Enter"},
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": ["7483922292361464102"],
            "rankMap": {"7483922292361464102": 5},
            "stageId": None,
            "stageIdStr": "7484987318274214180",
            "stageType": 4,
        },
        "key": "stageName_7484987318274214180",
        "rawKey": "stageName",
    },
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": [
                "7483922292361464102",
                "7485040846077905215",
                "7483922292361480486",
                "7484988241876896009",
                "7484988149308803338",
            ],
            "rankMap": {
                "7483922292361464102": 6,
                "7483922292361480486": 5,
                "7484988149308803338": 3,
                "7484988241876896009": 5,
                "7485040846077905215": 5,
            },
            "stageId": None,
            "stageIdStr": "7484987042608285962",
            "stageType": 4,
        },
        "key": "stageName_7484987042608285962",
        "rawKey": "stageName",
    },
    {"data": None, "key": "interviewRound1PassRate", "rawKey": "interviewRound1PassRate"},
    {"data": None, "key": "interviewRound2PassRate", "rawKey": "interviewRound2PassRate"},
    {"data": None, "key": "interviewRound3Enter", "rawKey": "interviewRound3Enter"},
    {"data": None, "key": "interviewRound3PassRate", "rawKey": "interviewRound3PassRate"},
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": [
                "7483922292361464102",
                "7485040846077905215",
                "7483922292361480486",
                "7484988241876896009",
                "7484988149308803338",
            ],
            "rankMap": {
                "7483922292361464102": 7,
                "7483922292361480486": 6,
                "7484988149308803338": 4,
                "7484988241876896009": 6,
                "7485040846077905215": 6,
            },
            "stageId": None,
            "stageIdStr": "7483922292361414950",
            "stageType": 5,
        },
        "key": "stageName_7483922292361414950",
        "rawKey": "stageName",
    },
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": [
                "7483922292361464102",
                "7485040846077905215",
                "7483922292361480486",
                "7484988241876896009",
                "7484988149308803338",
            ],
            "rankMap": {
                "7483922292361464102": 9,
                "7483922292361480486": 8,
                "7484988149308803338": 6,
                "7484988241876896009": 8,
                "7485040846077905215": 8,
            },
            "stageId": None,
            "stageIdStr": "7483922292361447718",
            "stageType": 7,
        },
        "key": "stageName_7483922292361447718",
        "rawKey": "stageName",
    },
    {"data": None, "key": "interviewRound1Pass", "rawKey": "interviewRound1Pass"},
    {"data": None, "key": "interviewRound2Pass", "rawKey": "interviewRound2Pass"},
    {"data": None, "key": "interviewRound3Pass", "rawKey": "interviewRound3Pass"},
    {"data": None, "key": "appOfferCount", "rawKey": "appOfferCount"},
    {"data": None, "key": "offerPassCount", "rawKey": "offerPassCount"},
    {"data": None, "key": "appOfferSend", "rawKey": "appOfferSend"},
    {"data": None, "key": "appOfferAccept", "rawKey": "appOfferAccept"},
    {"data": None, "key": "jobID", "rawKey": "jobID"},
    {"data": None, "key": "jobVirtual", "rawKey": "jobVirtual"},
]
SPECIAL_MEASURES = [
    {"data": None, "key": "appWeekName", "rawKey": "appWeekName"},
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": [
                "7483922292361464102",
                "7485040846077905215",
                "7483922292361480486",
                "7484988241876896009",
                "7484988149308803338",
            ],
            "rankMap": {
                "7483922292361464102": 0,
                "7483922292361480486": 0,
                "7484988149308803338": 0,
                "7484988241876896009": 0,
                "7485040846077905215": 0,
            },
            "stageId": None,
            "stageIdStr": "7483922292361365798",
            "stageType": 1,
        },
        "key": "stageName_7483922292361365798",
        "rawKey": "stageName",
    },
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": [
                "7483922292361464102",
                "7485040846077905215",
                "7483922292361480486",
                "7484988241876896009",
                "7484988149308803338",
            ],
            "rankMap": {
                "7483922292361464102": 1,
                "7483922292361480486": 1,
                "7484988149308803338": 1,
                "7484988241876896009": 1,
                "7485040846077905215": 1,
            },
            "stageId": None,
            "stageIdStr": "7483922292361382182",
            "stageType": 2,
        },
        "key": "stageName_7483922292361382182",
        "rawKey": "stageName",
    },
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": [
                "7483922292361464102",
                "7485040846077905215",
                "7483922292361480486",
                "7484988241876896009",
            ],
            "rankMap": {
                "7483922292361464102": 2,
                "7483922292361480486": 2,
                "7484988241876896009": 2,
                "7485040846077905215": 2,
            },
            "stageId": None,
            "stageIdStr": "7487173396766968091",
            "stageType": 8,
        },
        "key": "stageName_7487173396766968091",
        "rawKey": "stageName",
    },
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": [
                "7483922292361464102",
                "7485040846077905215",
                "7483922292361480486",
                "7484988241876896009",
                "7484988149308803338",
            ],
            "rankMap": {
                "7483922292361464102": 3,
                "7483922292361480486": 3,
                "7484988149308803338": 2,
                "7484988241876896009": 4,
                "7485040846077905215": 3,
            },
            "stageId": None,
            "stageIdStr": "7483922292361398566",
            "stageType": 4,
        },
        "key": "stageName_7483922292361398566",
        "rawKey": "stageName",
    },
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": [
                "7483922292361464102",
                "7485040846077905215",
                "7483922292361480486",
            ],
            "rankMap": {
                "7483922292361464102": 4,
                "7483922292361480486": 4,
                "7485040846077905215": 4,
            },
            "stageId": None,
            "stageIdStr": "7484986929462872370",
            "stageType": 4,
        },
        "key": "stageName_7484986929462872370",
        "rawKey": "stageName",
    },
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": [
                "7483922292361464102",
                "7485040846077905215",
                "7483922292361480486",
                "7484988241876896009",
                "7484988149308803338",
            ],
            "rankMap": {
                "7483922292361464102": 6,
                "7483922292361480486": 5,
                "7484988149308803338": 3,
                "7484988241876896009": 5,
                "7485040846077905215": 5,
            },
            "stageId": None,
            "stageIdStr": "7484987042608285962",
            "stageType": 4,
        },
        "key": "stageName_7484987042608285962",
        "rawKey": "stageName",
    },
    {
        "data": {
            "customizedFieldType": None,
            "objectId": None,
            "objectScene": None,
            "optionsMeta": None,
            "processIds": [
                "7483922292361464102",
                "7485040846077905215",
                "7483922292361480486",
                "7484988241876896009",
                "7484988149308803338",
            ],
            "rankMap": {
                "7483922292361464102": 9,
                "7483922292361480486": 8,
                "7484988149308803338": 6,
                "7484988241876896009": 8,
                "7485040846077905215": 8,
            },
            "stageId": None,
            "stageIdStr": "7483922292361447718",
            "stageType": 7,
        },
        "key": "stageName_7483922292361447718",
        "rawKey": "stageName",
    },
    {"data": None, "key": "appHideWeek", "rawKey": "appHideWeek"},
]


def load_config(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def filter_jobs_by_title(
    jobs: list[dict[str, Any]],
    included_titles: list[str],
) -> list[dict[str, Any]]:
    wanted = set(included_titles)
    return [job for job in jobs if job.get("title") in wanted]


def build_target_summary(goal: int, current: int) -> dict[str, int]:
    return {
        "goal": int(goal),
        "current": int(current),
        "gap": max(int(goal) - int(current), 0),
    }


def build_week_ranges(
    start_date: str,
    end_date: str,
    tz_name: str = DEFAULT_TIMEZONE,
) -> list[dict[str, Any]]:
    tz = ZoneInfo(tz_name)
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    ranges: list[dict[str, Any]] = []
    current = start

    while current <= end:
        days_until_sunday = 6 - current.weekday()
        segment_end = min(current + timedelta(days=days_until_sunday), end)
        ranges.append(
            {
                "start": current.isoformat(),
                "end": segment_end.isoformat(),
                "label": f"{current.strftime('%m-%d')} – {segment_end.strftime('%m-%d')}",
                "start_ms": to_epoch_ms(current.isoformat(), tz_name, False),
                "end_ms": to_epoch_ms(segment_end.isoformat(), tz_name, True),
            }
        )
        current = segment_end + timedelta(days=1)

    return ranges


def iter_iso_dates(start_date: str, end_date: str) -> list[str]:
    current = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    values: list[str] = []
    while current <= end:
        values.append(current.isoformat())
        current += timedelta(days=1)
    return values


def to_epoch_ms(
    value: str,
    tz_name: str = DEFAULT_TIMEZONE,
    end_of_day: bool = False,
) -> int:
    tz = ZoneInfo(tz_name)
    local_date = date.fromisoformat(value)
    local_time = time.max if end_of_day else time.min
    return int(datetime.combine(local_date, local_time, tzinfo=tz).timestamp() * 1000)


def in_window(timestamp_ms: int | str | None, start_ms: int, end_ms: int) -> bool:
    if not timestamp_ms:
        return False
    value = int(timestamp_ms)
    return start_ms <= value <= end_ms


def build_stage_catalog(processes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    stage_catalog: dict[str, dict[str, Any]] = {}
    for process in processes:
        for stage in process.get("stage_list", []):
            name = stage.get("zh_name") or stage.get("en_name")
            if name not in KNOWN_STAGE_KEYS:
                continue
            key = KNOWN_STAGE_KEYS[name]
            stage_catalog[stage["id"]] = {
                "id": stage["id"],
                "key": key,
                "label": STAGE_KEY_LABELS[key],
                "type": stage.get("type"),
                "zh_name": stage.get("zh_name"),
                "en_name": stage.get("en_name"),
            }
    return stage_catalog


def summarize_stage_entries(
    applications: list[dict[str, Any]],
    stage_catalog: dict[str, dict[str, Any]],
    start_date: str,
    end_date: str,
    tz_name: str = DEFAULT_TIMEZONE,
) -> dict[str, Any]:
    start_ms = to_epoch_ms(start_date, tz_name, False)
    end_ms = to_epoch_ms(end_date, tz_name, True)
    weekly_ranges = build_week_ranges(start_date, end_date, tz_name)
    totals: Counter[str] = Counter()
    buckets = [{"label": item["label"], "counts": Counter()} for item in weekly_ranges]

    for application in applications:
        stage_time_list = application.get("stage_time_list", [])
        seen_screening = False
        for item in stage_time_list:
            stage_id = item.get("stage_id")
            meta = stage_catalog.get(stage_id)
            if not meta:
                continue
            key = meta["key"]
            enter_time = item.get("enter_time")
            if not in_window(enter_time, start_ms, end_ms):
                if key == "resume_screening":
                    seen_screening = True
                continue

            totals[key] += 1
            bucket = resolve_bucket(int(enter_time), weekly_ranges)
            if bucket is not None:
                buckets[bucket]["counts"][key] += 1
            if key == "resume_screening":
                seen_screening = True

        if not seen_screening and in_window(application.get("create_time"), start_ms, end_ms):
            totals["resume_screening"] += 1
            bucket = resolve_bucket(int(application["create_time"]), weekly_ranges)
            if bucket is not None:
                buckets[bucket]["counts"]["resume_screening"] += 1

    ordered_totals = {key: totals.get(key, 0) for key in STAGE_ORDER}
    ordered_buckets = []
    for bucket in buckets:
        ordered_buckets.append(
            {
                "label": bucket["label"],
                "counts": {key: bucket["counts"].get(key, 0) for key in STAGE_ORDER},
            }
        )

    return {
        "totals": ordered_totals,
        "weekly": ordered_buckets,
    }


def build_daily_stage_entries(
    applications: list[dict[str, Any]],
    stage_catalog: dict[str, dict[str, Any]],
    tz_name: str = DEFAULT_TIMEZONE,
) -> dict[str, dict[str, int]]:
    daily: dict[str, Counter[str]] = {}

    def bump(day_key: str, stage_key: str) -> None:
        bucket = daily.setdefault(day_key, Counter())
        bucket[stage_key] += 1

    for application in applications:
        stage_time_list = application.get("stage_time_list", [])
        seen_screening = False
        for item in stage_time_list:
            stage_id = item.get("stage_id")
            meta = stage_catalog.get(stage_id)
            if not meta or not item.get("enter_time"):
                continue
            stage_key = meta["key"]
            day_key = to_local_date_key(int(item["enter_time"]), tz_name)
            bump(day_key, stage_key)
            if stage_key == "resume_screening":
                seen_screening = True

        if not seen_screening and application.get("create_time"):
            bump(
                to_local_date_key(int(application["create_time"]), tz_name),
                "resume_screening",
            )

    return {
        day_key: {stage_key: counts.get(stage_key, 0) for stage_key in STAGE_ORDER}
        for day_key, counts in sorted(daily.items())
    }


def build_authoritative_daily_stage_entries(
    overview_rows_by_date: dict[str, dict[str, Any]]
) -> dict[str, dict[str, int]]:
    entries: dict[str, dict[str, int]] = {}
    for day_key, report_data in overview_rows_by_date.items():
        sum_row = report_data.get("sumRow", {})
        entries[day_key] = {
            stage_key: int(sum_row.get(field_key, 0))
            for stage_key, field_key in SUMMARY_STAGE_FIELDS.items()
        }
    return entries


def summarize_authoritative_range(
    daily_entries: dict[str, dict[str, int]],
    start_date: str,
    end_date: str,
) -> tuple[list[dict[str, Any]] | None, list[str]]:
    required_dates = iter_iso_dates(start_date, end_date)
    missing_dates = [day_key for day_key in required_dates if day_key not in daily_entries]
    if missing_dates:
        return None, missing_dates

    counts = {stage_key: 0 for stage_key in SUMMARY_STAGE_FIELDS}
    for day_key in required_dates:
        row = daily_entries[day_key]
        for stage_key in counts:
            counts[stage_key] += row.get(stage_key, 0)

    return [
        {
            "key": "resume_screening",
            "label": "进入「简历初筛」阶段",
            "count": counts["resume_screening"],
        },
        {
            "key": "assigned_evaluation",
            "label": "安排评估",
            "count": counts["assigned_evaluation"],
        },
        {
            "key": "initial_invite",
            "label": "进入「初面邀约」阶段",
            "count": counts["initial_invite"],
        },
        {
            "key": "interview_1",
            "label": "进入「专业一面」阶段",
            "count": counts["interview_1"],
        },
        {
            "key": "conduct_interview_1",
            "label": "进行 1 面",
            "count": counts["conduct_interview_1"],
        },
        {
            "key": "interview_2",
            "label": "进入「专业二面」阶段",
            "count": counts["interview_2"],
        },
        {
            "key": "hr_interview",
            "label": "进入「HR面」阶段",
            "count": counts["hr_interview"],
        },
        {
            "key": "onboarded",
            "label": "进入「已入职」阶段",
            "count": counts["onboarded"],
        },
    ], []


def build_authoritative_weekly_series(
    daily_entries: dict[str, dict[str, int]],
    start_date: str,
    end_date: str,
) -> tuple[list[str] | None, list[dict[str, Any]] | None, list[str]]:
    required_dates = iter_iso_dates(start_date, end_date)
    missing_dates = [day_key for day_key in required_dates if day_key not in daily_entries]
    if missing_dates:
        return None, None, missing_dates

    ranges = build_week_ranges(start_date, end_date)
    labels = [item["label"] for item in ranges]
    series = []
    for stage_key in SUMMARY_STAGE_FIELDS:
        counts = []
        for date_range in ranges:
            total = 0
            for day_key in iter_iso_dates(date_range["start"], date_range["end"]):
                total += daily_entries[day_key].get(stage_key, 0)
            counts.append(total)
        series.append(
            {
                "key": stage_key,
                "label": STAGE_KEY_LABELS.get(stage_key, stage_key),
                "counts": counts,
            }
        )
    return labels, series, []


def resolve_bucket(timestamp_ms: int, weekly_ranges: list[dict[str, Any]]) -> int | None:
    for index, bucket in enumerate(weekly_ranges):
        if bucket["start_ms"] <= timestamp_ms <= bucket["end_ms"]:
            return index
    return None


def to_local_date_key(timestamp_ms: int, tz_name: str = DEFAULT_TIMEZONE) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=ZoneInfo(tz_name)).strftime("%Y-%m-%d")


def derive_pipeline_candidates(
    applications: list[dict[str, Any]],
    stage_catalog: dict[str, dict[str, Any]],
    talent_names: dict[str, str],
) -> dict[str, list[dict[str, Any]]]:
    candidates = {"interview_1": [], "interview_2": []}
    for application in applications:
        if application.get("active_status") != 1:
            continue
        reached = reached_stage_keys(application, stage_catalog)
        if "hr_interview" in reached:
            continue
        talent_id = application.get("talent_id")
        if talent_id not in talent_names:
            continue
        payload = {
            "name": talent_names[talent_id],
            "talent_id": talent_id,
            "application_id": application.get("id"),
        }
        current_stage_id = application.get("stage", {}).get("id")
        current_key = stage_catalog.get(current_stage_id, {}).get("key")
        if current_key == "interview_2" or "interview_2" in reached:
            payload["dateIso"] = format_iso_stage_date(
                find_stage_enter_time(application, stage_catalog, "interview_2"),
                stage_catalog,
            )
            candidates["interview_2"].append(payload)
        elif current_key == "interview_1" or "interview_1" in reached:
            payload["dateIso"] = format_iso_stage_date(
                find_stage_enter_time(application, stage_catalog, "interview_1"),
                stage_catalog,
            )
            candidates["interview_1"].append(payload)
    return candidates


def derive_hr_candidates(
    applications: list[dict[str, Any]],
    stage_catalog: dict[str, dict[str, Any]],
    talent_names: dict[str, str],
    start_date: str | None = None,
    end_date: str | None = None,
    tz_name: str = DEFAULT_TIMEZONE,
) -> dict[str, Any]:
    start_ms = to_epoch_ms(start_date, tz_name, False) if start_date else None
    end_ms = to_epoch_ms(end_date, tz_name, True) if end_date else None
    candidates = []
    for application in applications:
        reached = reached_stage_keys(application, stage_catalog)
        if "hr_interview" not in reached:
            continue

        talent_id = application.get("talent_id")
        name = talent_names.get(talent_id)
        if not name:
            continue

        current_stage_id = application.get("stage", {}).get("id")
        current_key = stage_catalog.get(current_stage_id, {}).get("key")
        status, label, role = map_hr_status(
            application.get("active_status", 0),
            application.get("termination_type", 0),
            current_key,
        )
        hr_enter_time = find_stage_enter_time(application, stage_catalog, "hr_interview")
        if start_ms is not None and end_ms is not None and not in_window(hr_enter_time, start_ms, end_ms):
            continue
        candidates.append(
            {
                "name": name,
                "talent_id": talent_id,
                "application_id": application.get("id"),
                "status": status,
                "label": label,
                "role": role,
                "date": format_mm_dd(hr_enter_time),
                "dateIso": format_iso_stage_date(hr_enter_time, stage_catalog),
            }
        )

    candidates.sort(
        key=lambda item: (
            HR_STATUS_ORDER.get(item["status"], 99),
            item["date"] or "",
            item["name"],
        )
    )
    return {"total": len(candidates), "candidates": candidates}


def reached_stage_keys(
    application: dict[str, Any],
    stage_catalog: dict[str, dict[str, Any]],
) -> set[str]:
    keys = set()
    for item in application.get("stage_time_list", []):
        meta = stage_catalog.get(item.get("stage_id"))
        if meta:
            keys.add(meta["key"])
    current_stage = application.get("stage", {}).get("id")
    meta = stage_catalog.get(current_stage)
    if meta:
        keys.add(meta["key"])
    return keys


def find_stage_enter_time(
    application: dict[str, Any],
    stage_catalog: dict[str, dict[str, Any]],
    wanted_key: str,
) -> int | None:
    for item in application.get("stage_time_list", []):
        meta = stage_catalog.get(item.get("stage_id"))
        if meta and meta["key"] == wanted_key and item.get("enter_time"):
            return int(item["enter_time"])
    return None


def map_hr_status(
    active_status: int,
    termination_type: int,
    current_stage_key: str | None,
) -> tuple[str, str, str]:
    if active_status == 1:
        if current_stage_key == "onboarded":
            return ("accept", "已入职", "已入职")
        if current_stage_key == "pending_onboard":
            return ("accept", "待入职", "待入职")
        if current_stage_key == "offer":
            return ("pending", "Offer 沟通中", "Offer 沟通")
        return ("pending", "进行中", "HR 面进行中")

    if termination_type == 22:
        return ("decline", "候选人放弃", "候选人放弃")
    if termination_type == 1:
        return ("reject", "已淘汰", "HR 面淘汰")
    return ("decline", "已终止", "已终止")


def format_mm_dd(timestamp_ms: int | None, tz_name: str = DEFAULT_TIMEZONE) -> str:
    if not timestamp_ms:
        return ""
    tz = ZoneInfo(tz_name)
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=tz).strftime("%m-%d")


def format_iso_stage_date(timestamp_ms: int | None, stage_catalog: dict[str, dict[str, Any]] | None = None, tz_name: str = DEFAULT_TIMEZONE) -> str:
    if not timestamp_ms:
        return ""
    tz = ZoneInfo(tz_name)
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=tz).strftime("%Y-%m-%d")


def parse_devtools_active_port(content: str) -> tuple[int, str]:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError("DevToolsActivePort 内容不完整")

    port = int(lines[0])
    ws_path = lines[1]
    if not ws_path.startswith("/"):
        ws_path = f"/{ws_path}"
    return port, ws_path


class ChromeDevToolsClient:
    def __init__(self) -> None:
        self._socket: socket.socket | None = None
        self._recv_buffer = b""
        self._next_id = 0
        self._sessions: dict[str, str] = {}

    def close(self) -> None:
        if self._socket is None:
            return
        try:
            self._socket.close()
        finally:
            self._socket = None
            self._recv_buffer = b""
            self._sessions.clear()

    def get_targets(self) -> list[dict[str, Any]]:
        response = self.send_command("Target.getTargets")
        return response.get("result", {}).get("targetInfos", [])

    def create_target(self, url: str, background: bool = True) -> str:
        response = self.send_command(
            "Target.createTarget",
            {"url": url, "background": background},
        )
        return response["result"]["targetId"]

    def ensure_session(self, target_id: str) -> str:
        if target_id in self._sessions:
            return self._sessions[target_id]

        response = self.send_command(
            "Target.attachToTarget",
            {"targetId": target_id, "flatten": True},
        )
        session_id = response["result"]["sessionId"]
        self._sessions[target_id] = session_id
        return session_id

    def evaluate(
        self,
        session_id: str,
        expression: str,
        await_promise: bool = True,
        return_by_value: bool = True,
    ) -> dict[str, Any]:
        return self.send_command(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": await_promise,
                "returnByValue": return_by_value,
            },
            session_id=session_id,
        )

    def send_command(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        session_id: str | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        self._ensure_connected()

        self._next_id += 1
        request_id = self._next_id
        payload: dict[str, Any] = {
            "id": request_id,
            "method": method,
            "params": params or {},
        }
        if session_id:
            payload["sessionId"] = session_id
        self._send_frame(json.dumps(payload).encode("utf-8"))

        deadline = time_module.monotonic() + timeout
        while time_module.monotonic() < deadline:
            remaining = max(deadline - time_module.monotonic(), 0.1)
            message = self._read_message(remaining)
            if message.get("id") == request_id:
                if message.get("error"):
                    raise RuntimeError(f"CDP 命令失败 {method}: {message['error']}")
                return message
            self._handle_event(message)

        raise TimeoutError(f"CDP 命令超时: {method}")

    def _handle_event(self, message: dict[str, Any]) -> None:
        if message.get("method") == "Target.attachedToTarget":
            params = message.get("params", {})
            target_info = params.get("targetInfo", {})
            target_id = target_info.get("targetId")
            session_id = params.get("sessionId")
            if target_id and session_id:
                self._sessions[target_id] = session_id
        elif message.get("method") == "Target.detachedFromTarget":
            params = message.get("params", {})
            detached_session = params.get("sessionId")
            stale_targets = [
                target_id
                for target_id, session_id in self._sessions.items()
                if session_id == detached_session
            ]
            for target_id in stale_targets:
                self._sessions.pop(target_id, None)

    def _ensure_connected(self) -> None:
        if self._socket is not None:
            return

        port, ws_path = self._discover_browser_endpoint()
        websocket_key = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
        accept_key = base64.b64encode(
            hashlib.sha1(
                (websocket_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode(
                    "ascii"
                )
            ).digest()
        ).decode("ascii")

        sock = socket.create_connection(("127.0.0.1", port), timeout=10)
        request = (
            f"GET {ws_path} HTTP/1.1\r\n"
            f"Host: 127.0.0.1:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {websocket_key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        ).encode("ascii")
        sock.sendall(request)

        response = b""
        while b"\r\n\r\n" not in response:
            chunk = sock.recv(4096)
            if not chunk:
                sock.close()
                raise RuntimeError("Chrome 调试连接在握手阶段被关闭")
            response += chunk

        header_block, self._recv_buffer = response.split(b"\r\n\r\n", 1)
        header_text = header_block.decode("utf-8", errors="replace")
        status_line = header_text.splitlines()[0]
        if "101" not in status_line:
            sock.close()
            raise RuntimeError(f"Chrome 调试握手失败: {status_line}")
        if accept_key not in header_text:
            sock.close()
            raise RuntimeError("Chrome 调试握手返回的校验值不匹配")

        self._socket = sock

    def _discover_browser_endpoint(self) -> tuple[int, str]:
        possible_paths = [
            Path.home()
            / "Library/Application Support/Google/Chrome/DevToolsActivePort",
            Path.home()
            / "Library/Application Support/Google/Chrome Canary/DevToolsActivePort",
            Path.home() / "Library/Application Support/Chromium/DevToolsActivePort",
        ]
        for path in possible_paths:
            if not path.exists():
                continue
            try:
                return parse_devtools_active_port(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue

        raise RuntimeError(
            "未找到 Chrome DevToolsActivePort。请先在 chrome://inspect/#remote-debugging 中启用当前浏览器实例的远程调试。"
        )

    def _read_message(self, timeout: float) -> dict[str, Any]:
        while True:
            opcode, payload = self._read_frame(timeout)
            if opcode == 0x1:
                return json.loads(payload.decode("utf-8"))
            if opcode == 0x8:
                self.close()
                raise RuntimeError("Chrome 调试连接已关闭")
            if opcode == 0x9:
                self._send_frame(payload, opcode=0xA)
                continue
            if opcode == 0xA:
                continue

    def _read_frame(self, timeout: float) -> tuple[int, bytes]:
        first = self._recv_exact(1, timeout)
        second = self._recv_exact(1, timeout)

        opcode = first[0] & 0x0F
        masked = (second[0] & 0x80) != 0
        length = second[0] & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._recv_exact(2, timeout))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._recv_exact(8, timeout))[0]

        mask_key = self._recv_exact(4, timeout) if masked else b""
        payload = self._recv_exact(length, timeout)
        if masked:
            payload = bytes(
                value ^ mask_key[index % 4] for index, value in enumerate(payload)
            )
        return opcode, payload

    def _recv_exact(self, size: int, timeout: float) -> bytes:
        if self._socket is None:
            raise RuntimeError("Chrome 调试连接尚未建立")

        chunks = []
        remaining = size
        if self._recv_buffer:
            take = self._recv_buffer[:remaining]
            chunks.append(take)
            self._recv_buffer = self._recv_buffer[remaining:]
            remaining -= len(take)

        self._socket.settimeout(timeout)
        try:
            while remaining > 0:
                chunk = self._socket.recv(remaining)
                if not chunk:
                    raise RuntimeError("Chrome 调试连接已断开")
                chunks.append(chunk)
                remaining -= len(chunk)
        finally:
            self._socket.settimeout(None)

        return b"".join(chunks)

    def _send_frame(self, payload: bytes, opcode: int = 0x1) -> None:
        if self._socket is None:
            raise RuntimeError("Chrome 调试连接尚未建立")

        mask_key = secrets.token_bytes(4)
        masked_payload = bytes(
            value ^ mask_key[index % 4] for index, value in enumerate(payload)
        )

        header = bytearray([0x80 | opcode])
        length = len(masked_payload)
        if length <= 125:
            header.append(0x80 | length)
        elif length <= 0xFFFF:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))

        self._socket.sendall(bytes(header) + mask_key + masked_payload)


class BrowserReportBridge:
    def __init__(self, report_url: str) -> None:
        self.report_url = report_url
        self._cdp = ChromeDevToolsClient()

    def close(self) -> None:
        self._cdp.close()

    def fetch_authoritative_data(
        self,
        job_ids: list[str],
        operation_window: dict[str, str],
        process_ids: list[str],
    ) -> dict[str, Any]:
        target_id = self._ensure_report_target()
        operation_time = [
            str(to_epoch_ms(operation_window["start"], DEFAULT_TIMEZONE, False)),
            str(to_epoch_ms(operation_window["end"], DEFAULT_TIMEZONE, True)),
        ]
        overview_body = {
            "withAmount": True,
            "reportKey": "7573581010957828099",
            "reportType": "user",
            "widgetKey": OVERVIEW_WIDGET_KEY,
            "measures": OVERVIEW_MEASURES,
            "dimensions": [{"key": "appJob"}],
            "orders": [],
            "filters": {
                "values": {
                    "jobProcess": process_ids,
                    "jobRange": ["all"],
                    "jobStatus": ["1"],
                    "operationTime": operation_time,
                    "appJob": job_ids,
                },
                "meta": [],
            },
            "withSum": True,
            "showZeroRow": False,
            "shareOwnerData": 1,
            "fromReportKey": "7573581010957828099",
            "limit": 50,
            "offset": 0,
        }
        special_body = {
            "withAmount": False,
            "reportKey": "7573581010957828099",
            "reportType": "user",
            "widgetKey": SPECIAL_WIDGET_KEY,
            "measures": SPECIAL_MEASURES,
            "dimensions": [{"key": "appWeek"}],
            "orders": [
                {"direction": "ascend", "key": "appWeekName"},
                {"direction": "ascend", "key": "appMonthName"},
                {"direction": "ascend", "key": "appQuarterName"},
            ],
            "filters": {
                "values": {
                    "jobProcess": process_ids,
                    "jobRange": ["all"],
                    "jobStatus": ["1"],
                    "operationTime": operation_time,
                    "appJob": job_ids,
                },
                "meta": [],
            },
            "withSum": False,
            "showZeroRow": False,
            "shareOwnerData": 1,
            "fromReportKey": "7573581010957828099",
        }
        overview = self._widget_fetch(target_id, "table", overview_body)
        special = self._widget_fetch(target_id, "chart", special_body)
        return {"overview": overview, "special": special}

    def fetch_authoritative_daily_overview(
        self,
        job_ids: list[str],
        operation_window: dict[str, str],
        process_ids: list[str],
    ) -> dict[str, dict[str, Any]]:
        target_id = self._ensure_report_target()
        daily: dict[str, dict[str, Any]] = {}
        for day_key in iter_iso_dates(operation_window["start"], operation_window["end"]):
            operation_time = [
                str(to_epoch_ms(day_key, DEFAULT_TIMEZONE, False)),
                str(to_epoch_ms(day_key, DEFAULT_TIMEZONE, True)),
            ]
            overview_body = {
                "withAmount": True,
                "reportKey": "7573581010957828099",
                "reportType": "user",
                "widgetKey": OVERVIEW_WIDGET_KEY,
                "measures": OVERVIEW_MEASURES,
                "dimensions": [{"key": "appJob"}],
                "orders": [],
                "filters": {
                    "values": {
                        "jobProcess": process_ids,
                        "jobRange": ["all"],
                        "jobStatus": ["1"],
                        "operationTime": operation_time,
                        "appJob": job_ids,
                    },
                    "meta": [],
                },
                "withSum": True,
                "showZeroRow": False,
                "shareOwnerData": 1,
                "fromReportKey": "7573581010957828099",
                "limit": 50,
                "offset": 0,
            }
            daily[day_key] = self._widget_fetch(target_id, "table", overview_body)
        return daily

    def _ensure_report_target(self) -> str:
        targets = self._cdp.get_targets()
        for target in targets:
            if target.get("url") == self.report_url:
                self._wait_for_target_ready(target["targetId"])
                return target["targetId"]
        target_id = self._cdp.create_target(self.report_url, background=True)
        self._wait_for_target_ready(target_id)
        return target_id

    def _widget_fetch(self, target_id: str, widget_type: str, body: dict[str, Any]) -> dict[str, Any]:
        session_id = self._cdp.ensure_session(target_id)
        report_origin = urlparse(self.report_url)._replace(path="", params="", query="", fragment="").geturl().rstrip("/")
        js = f"""
(async () => {{
  const res = await fetch('{report_origin}/atsx/api/report/selfhelp/widget/data?type={widget_type}', {{
    method: 'POST',
    credentials: 'include',
    headers: {{'Content-Type': 'application/json'}},
    body: {json.dumps(json.dumps(body), ensure_ascii=False)}
  }});
  return JSON.stringify(await res.json());
}})()
"""
        payload = self._cdp.evaluate(session_id, js)
        result = payload.get("result", {}).get("result", {}).get("value")
        if payload.get("result", {}).get("exceptionDetails"):
            raise RuntimeError(
                f"Browser widget fetch failed for {widget_type}: {payload['result']['exceptionDetails']}"
            )
        if isinstance(result, str):
            result = json.loads(result)
        if not isinstance(result, dict) or not result.get("success"):
            raise RuntimeError(f"Browser widget fetch failed for {widget_type}: {result}")
        return result["data"]

    def _wait_for_target_ready(self, target_id: str, timeout: float = 30.0) -> None:
        session_id = self._cdp.ensure_session(target_id)
        deadline = time_module.monotonic() + timeout
        while time_module.monotonic() < deadline:
            try:
                payload = self._cdp.evaluate(
                    session_id,
                    "JSON.stringify({readyState: document.readyState, href: location.href})",
                )
                result = payload.get("result", {}).get("result", {}).get("value")
                state = json.loads(result) if isinstance(result, str) else {}
                if (
                    isinstance(state, dict)
                    and state.get("readyState") == "complete"
                    and isinstance(state.get("href"), str)
                    and state["href"].startswith(self.report_url)
                ):
                    return
            except Exception:
                pass
            time_module.sleep(0.5)

        raise TimeoutError(f"报表页面加载超时: {self.report_url}")


def run_lark_json(*args: str, max_attempts: int = 5) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        result = subprocess.run(
            ["lark-cli", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as error:
                last_error = error
        else:
            last_error = RuntimeError(
                f"lark-cli failed: {' '.join(args)}\nstdout={result.stdout}\nstderr={result.stderr}"
            )
        time_module.sleep(0.4 * attempt)
    raise RuntimeError(str(last_error))


def fetch_all_jobs() -> list[dict[str, Any]]:
    jobs = []
    page_token = ""
    while True:
        args = ["api", "GET", "/open-apis/hire/v1/jobs", "--as", "bot"]
        if page_token:
            args.extend(["--params", json.dumps({"page_token": page_token})])
        payload = run_lark_json(*args)
        jobs.extend(payload.get("data", {}).get("items", []))
        if not payload.get("data", {}).get("has_more"):
            break
        page_token = payload.get("data", {}).get("page_token", "")
    return jobs


def fetch_job_processes() -> list[dict[str, Any]]:
    payload = run_lark_json("api", "GET", "/open-apis/hire/v1/job_processes", "--as", "bot")
    return payload.get("data", {}).get("items", [])


def fetch_application_ids(job_ids: list[str]) -> list[str]:
    def fetch_job_application_ids(job_id: str) -> list[str]:
        job_ids_for_one_role: list[str] = []
        page_token = ""
        while True:
            params = {"job_id": job_id, "page_size": "200"}
            if page_token:
                params["page_token"] = page_token
            payload = run_lark_json(
                "api",
                "GET",
                "/open-apis/hire/v1/applications",
                "--as",
                "bot",
                "--params",
                json.dumps(params, ensure_ascii=False),
            )
            job_ids_for_one_role.extend(payload.get("data", {}).get("items", []))
            if not payload.get("data", {}).get("has_more"):
                break
            page_token = payload.get("data", {}).get("page_token", "")
        return job_ids_for_one_role

    if len(job_ids) <= 1:
        return fetch_job_application_ids(job_ids[0]) if job_ids else []

    collected_ids: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(len(job_ids), 4)
    ) as executor:
        for ids_for_job in executor.map(fetch_job_application_ids, job_ids):
            collected_ids.extend(ids_for_job)
    return collected_ids


def fetch_application_details(
    application_ids: list[str],
    max_workers: int = 18,
) -> list[dict[str, Any]]:
    def fetch_one(app_id: str) -> dict[str, Any] | None:
        payload = run_lark_json(
            "api",
            "GET",
            f"/open-apis/hire/v1/applications/{app_id}",
            "--as",
            "bot",
        )
        return payload.get("data", {}).get("application")

    applications: list[dict[str, Any]] = []
    failures: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(fetch_one, app_id): app_id for app_id in application_ids}
        for future in concurrent.futures.as_completed(future_map):
            app_id = future_map[future]
            try:
                application = future.result()
            except Exception:
                failures.append(app_id)
                continue
            if application:
                applications.append(application)
            else:
                failures.append(app_id)

    for app_id in failures[:]:
        try:
            application = fetch_one(app_id)
        except Exception:
            continue
        if application:
            applications.append(application)
            failures.remove(app_id)

    if failures:
        raise RuntimeError(
            f"Expected {len(application_ids)} application details, got {len(applications)}; missing {len(failures)} app ids"
        )
    return applications


def fetch_talent_names(
    talent_ids: list[str],
    max_workers: int = 12,
) -> dict[str, str]:
    unique_ids = sorted({talent_id for talent_id in talent_ids if talent_id})

    def fetch_one(talent_id: str) -> tuple[str, str]:
        payload = run_lark_json(
            "api",
            "GET",
            f"/open-apis/hire/v1/talents/{talent_id}",
            "--as",
            "bot",
        )
        talent = payload.get("data", {}).get("talent", {})
        name = talent.get("basic_info", {}).get("name", "")
        return talent_id, name

    names: dict[str, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for talent_id, name in executor.map(fetch_one, unique_ids):
            if name:
                names[talent_id] = name
    return names


def fetch_current_headcount(queries: list[str]) -> dict[str, Any]:
    result_sets: list[set[str]] = []
    names_by_open_id: dict[str, str] = {}
    for query in queries:
        payload = json.loads(
            subprocess.run(
                ["lark-cli", "contact", "+search-user", "--as", "user", "--query", query],
                capture_output=True,
                text=True,
                check=False,
            ).stdout
        )
        users = payload.get("data", {}).get("users", [])
        open_ids = {user.get("open_id") for user in users if user.get("open_id")}
        result_sets.append(open_ids)
        for user in users:
            if user.get("open_id") and user.get("name"):
                names_by_open_id[user["open_id"]] = user["name"]

    if not result_sets:
        return {"count": 0, "names": []}

    intersection = set.intersection(*result_sets) if len(result_sets) > 1 else result_sets[0]
    return {
        "count": len(intersection),
        "names": sorted(names_by_open_id[open_id] for open_id in intersection if open_id in names_by_open_id),
    }


def build_summary_from_report(report_data: dict[str, Any]) -> list[dict[str, Any]]:
    sum_row = report_data.get("sumRow", {})
    return [
        {
            "key": "resume_screening",
            "label": "进入「简历初筛」阶段",
            "count": int(sum_row.get("stageName_7483922292361365798", 0)),
        },
        {
            "key": "assigned_evaluation",
            "label": "安排评估",
            "count": int(sum_row.get("appEvaluationCount", 0)),
        },
        {
            "key": "initial_invite",
            "label": "进入「初面邀约」阶段",
            "count": int(sum_row.get("stageName_7487173396766968091", 0)),
        },
        {
            "key": "interview_1",
            "label": "进入「专业一面」阶段",
            "count": int(sum_row.get("stageName_7483922292361398566", 0)),
        },
        {
            "key": "conduct_interview_1",
            "label": "进行 1 面",
            "count": int(sum_row.get("interviewRound1Enter", 0)),
        },
        {
            "key": "interview_2",
            "label": "进入「专业二面」阶段",
            "count": int(sum_row.get("stageName_7484986929462872370", 0)),
        },
        {
            "key": "hr_interview",
            "label": "进入「HR面」阶段",
            "count": int(sum_row.get("stageName_7484987042608285962", 0)),
        },
        {
            "key": "onboarded",
            "label": "进入「已入职」阶段",
            "count": int(sum_row.get("stageName_7483922292361447718", 0)),
        },
    ]


def build_special_series_from_report(
    report_data: dict[str, Any],
    start_date: str,
    end_date: str,
    tz_name: str = DEFAULT_TIMEZONE,
) -> tuple[list[str], list[dict[str, Any]]]:
    rows = report_data.get("rows", [])
    week_ranges = build_week_ranges(start_date, end_date, tz_name)
    labels = [item["label"] for item in week_ranges]
    key_map = {
        "resume_screening": "stageName_7483922292361365798",
        "resume_evaluation": "stageName_7483922292361382182",
        "initial_invite": "stageName_7487173396766968091",
        "interview_1": "stageName_7483922292361398566",
        "interview_2": "stageName_7484986929462872370",
        "hr_interview": "stageName_7484987042608285962",
        "onboarded": "stageName_7483922292361447718",
    }
    series = []
    for stage_key, report_key in key_map.items():
        series.append(
            {
                "key": stage_key,
                "label": STAGE_KEY_LABELS[stage_key],
                "counts": [int(row.get(report_key, 0)) for row in rows],
            }
        )
    return labels, series


def build_dashboard_payload(config: dict[str, Any]) -> dict[str, Any]:
    timezone_name = config.get("timezone", DEFAULT_TIMEZONE)
    jobs = fetch_all_jobs()
    matched_jobs = filter_jobs_by_title(jobs, config["includedJobTitles"])
    missing_titles = sorted(
        set(config["includedJobTitles"]) - {job.get("title") for job in matched_jobs}
    )
    if missing_titles:
        raise RuntimeError(f"Missing jobs from whitelist: {missing_titles}")

    job_processes = fetch_job_processes()
    stage_catalog = build_stage_catalog(job_processes)
    application_ids = fetch_application_ids([job["id"] for job in matched_jobs])
    applications = fetch_application_details(application_ids)
    stage_summary = summarize_stage_entries(
        applications,
        stage_catalog,
        config["operationWindow"]["start"],
        config["operationWindow"]["end"],
        timezone_name,
    )
    daily_stage_entries = build_daily_stage_entries(applications, stage_catalog, timezone_name)
    week_ranges = build_week_ranges(
        config["operationWindow"]["start"],
        config["operationWindow"]["end"],
        timezone_name,
    )
    process_ids = sorted({job.get("process_id") for job in matched_jobs if job.get("process_id")})

    authority_mode = "openapi-fallback"
    summary_counts = build_summary_counts(
        applications,
        stage_catalog,
        stage_summary,
        config["operationWindow"]["start"],
        config["operationWindow"]["end"],
        timezone_name,
    )
    weekly_labels = [item["label"] for item in stage_summary["weekly"]]
    weekly_series = [
        {
            "key": key,
            "label": STAGE_KEY_LABELS[key],
            "counts": [bucket["counts"].get(key, 0) for bucket in stage_summary["weekly"]],
        }
        for key in STAGE_ORDER
    ]
    authoritative_daily_entries: dict[str, dict[str, int]] = {}
    authoritative_daily_missing: list[str] = []

    try:
        bridge = BrowserReportBridge(config["reportSource"]["widgetUrl"])
        try:
            authority = bridge.fetch_authoritative_data(
                [job["id"] for job in matched_jobs],
                config["operationWindow"],
                process_ids or ["7483922292361464102"],
            )
            summary_counts = build_summary_from_report(authority["overview"])
            weekly_labels, weekly_series = build_special_series_from_report(
                authority["special"],
                config["operationWindow"]["start"],
                config["operationWindow"]["end"],
                timezone_name,
            )
            daily_reports = bridge.fetch_authoritative_daily_overview(
                [job["id"] for job in matched_jobs],
                config["operationWindow"],
                process_ids or ["7483922292361464102"],
            )
            authoritative_daily_entries = build_authoritative_daily_stage_entries(daily_reports)
            authoritative_daily_missing = [
                day_key
                for day_key in iter_iso_dates(
                    config["operationWindow"]["start"],
                    config["operationWindow"]["end"],
                )
                if day_key not in authoritative_daily_entries
            ]
            authority_mode = "browser-report"
        finally:
            bridge.close()
    except Exception:
        pass

    headcount = fetch_current_headcount(config.get("currentHeadcountSource", {}).get("queries", []))
    target_current = headcount["count"]

    hr_talent_ids = [
        app.get("talent_id")
        for app in applications
        if "hr_interview" in reached_stage_keys(app, stage_catalog)
    ]
    pipeline_talent_ids = [
        app.get("talent_id")
        for app in applications
        if app.get("active_status") == 1
        and (
            "interview_1" in reached_stage_keys(app, stage_catalog)
            or "interview_2" in reached_stage_keys(app, stage_catalog)
        )
    ]
    talent_names = fetch_talent_names(hr_talent_ids + pipeline_talent_ids)

    pipeline_candidates = derive_pipeline_candidates(applications, stage_catalog, talent_names)
    hr_candidates = derive_hr_candidates(
        applications,
        stage_catalog,
        talent_names,
        config["operationWindow"]["start"],
        config["operationWindow"]["end"],
        timezone_name,
    )

    return {
        "generatedAt": datetime.now(ZoneInfo(timezone_name)).strftime("%Y-%m-%d %H:%M"),
        "reportSource": {
            "widgetUrl": config["reportSource"]["widgetUrl"],
            "operationWindow": config["operationWindow"],
            "summaryReference": config["reportSource"].get("summaryReference", {}),
        },
        "jobScope": {
            "includedJobTitles": config["includedJobTitles"],
            "matchedJobs": [
                {
                    "id": job.get("id"),
                    "title": job.get("title"),
                    "department": (job.get("department") or {}).get("zh_name"),
                    "processName": job.get("process_name"),
                    "activeStatus": job.get("active_status"),
                }
                for job in matched_jobs
            ],
        },
        "target": build_target_summary(config["goal"], target_current),
        "funnel": {
            "summaryStages": summary_counts,
            "weeklyLabels": weekly_labels,
            "weeklyRanges": [
                {"label": item["label"], "start": item["start"], "end": item["end"]}
                for item in week_ranges
            ],
            "weeklySeries": weekly_series,
            "dailyStageEntries": daily_stage_entries,
            "authoritativeDailyEntries": authoritative_daily_entries,
            "authoritativeMissingDates": authoritative_daily_missing,
        },
        "pipelineCandidates": pipeline_candidates,
        "hrInterview": hr_candidates,
        "links": {
            "hireReport": config["reportSource"]["widgetUrl"],
        },
        "runtime": {
            "autoSync": config.get("autoSync", "每 5 分钟"),
            "authorityMode": authority_mode,
        },
        "headcount": {
            "queries": config.get("currentHeadcountSource", {}).get("queries", []),
            "matchedNames": headcount["names"],
        },
    }


def build_summary_counts(
    applications: list[dict[str, Any]],
    stage_catalog: dict[str, dict[str, Any]],
    stage_summary: dict[str, Any],
    start_date: str | None = None,
    end_date: str | None = None,
    tz_name: str = DEFAULT_TIMEZONE,
) -> list[dict[str, Any]]:
    totals = stage_summary["totals"]
    interview_1_enter = totals.get("interview_1", 0)
    return [
        {
            "key": "resume_screening",
            "label": "进入「简历初筛」阶段",
            "count": totals.get("resume_screening", 0),
        },
        {
            "key": "assigned_evaluation",
            "label": "安排评估",
            "count": count_assigned_evaluation(
                applications,
                stage_catalog,
                start_date,
                end_date,
                tz_name,
            ),
        },
        {
            "key": "initial_invite",
            "label": "进入「初面邀约」阶段",
            "count": totals.get("initial_invite", 0),
        },
        {
            "key": "interview_1",
            "label": "进入「专业一面」阶段",
            "count": interview_1_enter,
        },
        {
            "key": "conduct_interview_1",
            "label": "进行 1 面",
            "count": interview_1_enter,
        },
        {
            "key": "interview_2",
            "label": "进入「专业二面」阶段",
            "count": totals.get("interview_2", 0),
        },
        {
            "key": "hr_interview",
            "label": "进入「HR面」阶段",
            "count": totals.get("hr_interview", 0),
        },
        {
            "key": "onboarded",
            "label": "进入「已入职」阶段",
            "count": totals.get("onboarded", 0),
        },
    ]


def count_assigned_evaluation(
    applications: list[dict[str, Any]],
    stage_catalog: dict[str, dict[str, Any]],
    start_date: str | None = None,
    end_date: str | None = None,
    tz_name: str = DEFAULT_TIMEZONE,
) -> int:
    start_ms = to_epoch_ms(start_date, tz_name, False) if start_date else None
    end_ms = to_epoch_ms(end_date, tz_name, True) if end_date else None
    count = 0
    for application in applications:
        if start_ms is not None and end_ms is not None:
            create_time = application.get("create_time")
            if not in_window(create_time, start_ms, end_ms):
                continue
        stage_keys = reached_stage_keys(application, stage_catalog)
        current_stage_key = stage_catalog.get(application.get("stage", {}).get("id"), {}).get("key")
        if "resume_evaluation" in stage_keys or current_stage_key in {
            "initial_invite",
            "interview_1",
            "interview_2",
            "hr_interview",
            "offer",
            "pending_onboard",
            "onboarded",
        }:
            count += 1
    return count
