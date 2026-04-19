from __future__ import annotations

import concurrent.futures
import json
import subprocess
import time as time_module
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests


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
HR_STATUS_ORDER = {
    "accept": 1,
    "pending": 2,
    "decline": 3,
    "reject": 4,
}

CDP_BASE_URL = "http://localhost:3456"
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


def resolve_bucket(timestamp_ms: int, weekly_ranges: list[dict[str, Any]]) -> int | None:
    for index, bucket in enumerate(weekly_ranges):
        if bucket["start_ms"] <= timestamp_ms <= bucket["end_ms"]:
            return index
    return None


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
            candidates["interview_2"].append(payload)
        elif current_key == "interview_1" or "interview_1" in reached:
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


class BrowserReportBridge:
    def __init__(self, report_url: str) -> None:
        self.report_url = report_url

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

    def _ensure_report_target(self) -> str:
        targets = requests.get(f"{CDP_BASE_URL}/targets", timeout=10).json()
        for target in targets:
            if target.get("url") == self.report_url:
                return target["targetId"]
        response = requests.get(
            f"{CDP_BASE_URL}/new",
            params={"url": self.report_url},
            timeout=10,
        ).json()
        return response["targetId"]

    def _widget_fetch(self, target_id: str, widget_type: str, body: dict[str, Any]) -> dict[str, Any]:
        js = f"""
(async () => {{
  const res = await fetch('/atsx/api/report/selfhelp/widget/data?type={widget_type}', {{
    method: 'POST',
    credentials: 'include',
    headers: {{'Content-Type': 'application/json'}},
    body: {json.dumps(json.dumps(body), ensure_ascii=False)}
  }});
  return await res.json();
}})()
"""
        payload = requests.post(
            f"{CDP_BASE_URL}/eval",
            params={"target": target_id},
            data=js,
            timeout=30,
        ).json()
        result = payload.get("value")
        if not isinstance(result, dict) or not result.get("success"):
            raise RuntimeError(f"Browser widget fetch failed for {widget_type}: {result}")
        return result["data"]


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
    ids: list[str] = []
    for job_id in job_ids:
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
            ids.extend(payload.get("data", {}).get("items", []))
            if not payload.get("data", {}).get("has_more"):
                break
            page_token = payload.get("data", {}).get("page_token", "")
    return ids


def fetch_application_details(
    application_ids: list[str],
    max_workers: int = 6,
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
    max_workers: int = 4,
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
                ["lark-cli", "contact", "+search-user", "--query", query],
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
    labels = [item["label"] for item in build_week_ranges(start_date, end_date, tz_name)]
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

    try:
        bridge = BrowserReportBridge(config["reportSource"]["widgetUrl"])
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
        authority_mode = "browser-report"
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
            "weeklySeries": weekly_series,
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
