import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from dashboard_data import (
    build_special_series_from_report,
    build_summary_from_report,
    build_target_summary,
    build_week_ranges,
    derive_hr_candidates,
    filter_jobs_by_title,
    summarize_stage_entries,
)


class FilterJobsByTitleTests(unittest.TestCase):
    def test_uses_exact_whitelist_only(self) -> None:
        jobs = [
            {"id": "1", "title": "ROOT-全栈工程师"},
            {"id": "2", "title": "AI 原生全栈工程师（工程-全栈）"},
            {"id": "3", "title": "ROOT-前端工程师"},
            {"id": "4", "title": "AI 原生产品经理"},
        ]

        matched = filter_jobs_by_title(
            jobs,
            [
                "ROOT-全栈工程师",
                "AI 原生全栈工程师（工程-全栈）",
            ],
        )

        self.assertEqual(["1", "2"], [job["id"] for job in matched])


class BuildWeekRangesTests(unittest.TestCase):
    def test_builds_partial_head_and_tail_weeks(self) -> None:
        ranges = build_week_ranges("2026-03-01", "2026-04-07")

        labels = [item["label"] for item in ranges]
        self.assertEqual(
            [
                "03-01 – 03-01",
                "03-02 – 03-08",
                "03-09 – 03-15",
                "03-16 – 03-22",
                "03-23 – 03-29",
                "03-30 – 04-05",
                "04-06 – 04-07",
            ],
            labels,
        )


class SummarizeStageEntriesTests(unittest.TestCase):
    def test_counts_stage_entries_by_stage_enter_time(self) -> None:
        tz = ZoneInfo("Asia/Shanghai")
        march_1 = str(int(datetime(2026, 3, 1, 9, 0, tzinfo=tz).timestamp() * 1000))
        march_3 = str(int(datetime(2026, 3, 3, 9, 0, tzinfo=tz).timestamp() * 1000))
        march_5 = str(int(datetime(2026, 3, 5, 9, 0, tzinfo=tz).timestamp() * 1000))
        march_8 = str(int(datetime(2026, 3, 8, 9, 0, tzinfo=tz).timestamp() * 1000))

        stage_catalog = {
            "screen": {"key": "resume_screening"},
            "eval": {"key": "resume_evaluation"},
            "invite": {"key": "initial_invite"},
        }
        applications = [
            {
                "create_time": march_1,
                "stage_time_list": [
                    {"stage_id": "screen", "enter_time": march_1},
                    {"stage_id": "eval", "enter_time": march_3},
                    {"stage_id": "invite", "enter_time": march_8},
                ],
            },
            {
                "create_time": march_3,
                "stage_time_list": [
                    {"stage_id": "screen", "enter_time": march_3},
                    {"stage_id": "eval", "enter_time": march_5},
                ],
            },
        ]

        summary = summarize_stage_entries(
            applications,
            stage_catalog,
            "2026-03-01",
            "2026-03-07",
            "Asia/Shanghai",
        )

        self.assertEqual(2, summary["totals"]["resume_screening"])
        self.assertEqual(2, summary["totals"]["resume_evaluation"])
        self.assertEqual(0, summary["totals"]["initial_invite"])


class BuildTargetSummaryTests(unittest.TestCase):
    def test_gap_is_computed_dynamically(self) -> None:
        target = build_target_summary(goal=10, current=4)

        self.assertEqual({"goal": 10, "current": 4, "gap": 6}, target)


class ReportAuthorityMappingTests(unittest.TestCase):
    def test_maps_overview_sum_row_to_summary_counts(self) -> None:
        summary = build_summary_from_report(
            {
                "sumRow": {
                    "stageName_7483922292361365798": "1397",
                    "appEvaluationCount": "343",
                    "stageName_7487173396766968091": "90",
                    "stageName_7483922292361398566": "18",
                    "interviewRound1Enter": "21",
                    "stageName_7484986929462872370": "9",
                    "stageName_7484987042608285962": "6",
                    "stageName_7483922292361447718": "0",
                }
            }
        )

        self.assertEqual(
            [1397, 343, 90, 18, 21, 9, 6, 0],
            [item["count"] for item in summary],
        )

    def test_maps_special_rows_to_weekly_series(self) -> None:
        labels, series = build_special_series_from_report(
            {
                "rows": [
                    {
                        "stageName_7483922292361365798": "2",
                        "stageName_7483922292361382182": "0",
                        "stageName_7487173396766968091": "0",
                        "stageName_7483922292361398566": "0",
                        "stageName_7484986929462872370": "0",
                        "stageName_7484987042608285962": "0",
                        "stageName_7483922292361447718": "0",
                    },
                    {
                        "stageName_7483922292361365798": "23",
                        "stageName_7483922292361382182": "30",
                        "stageName_7487173396766968091": "5",
                        "stageName_7483922292361398566": "2",
                        "stageName_7484986929462872370": "1",
                        "stageName_7484987042608285962": "0",
                        "stageName_7483922292361447718": "0",
                    },
                ]
            },
            "2026-03-01",
            "2026-03-08",
        )

        self.assertEqual(["03-01 – 03-01", "03-02 – 03-08"], labels)
        series_map = {item["key"]: item["counts"] for item in series}
        self.assertEqual([2, 23], series_map["resume_screening"])
        self.assertEqual([0, 30], series_map["resume_evaluation"])
        self.assertEqual([0, 5], series_map["initial_invite"])


class DeriveHrCandidatesTests(unittest.TestCase):
    def test_maps_statuses_from_stage_and_termination(self) -> None:
        stage_catalog = {
            "hr": {"key": "hr_interview"},
            "offer": {"key": "offer"},
            "pending": {"key": "pending_onboard"},
            "onboard": {"key": "onboarded"},
        }
        applications = [
            {
                "id": "app-offer",
                "talent_id": "tal-1",
                "active_status": 1,
                "termination_type": 0,
                "stage": {"id": "offer"},
                "stage_time_list": [
                    {"stage_id": "hr", "enter_time": "1774238400000"},
                    {"stage_id": "offer", "enter_time": "1774324800000"},
                ],
            },
            {
                "id": "app-pending",
                "talent_id": "tal-2",
                "active_status": 1,
                "termination_type": 0,
                "stage": {"id": "pending"},
                "stage_time_list": [
                    {"stage_id": "hr", "enter_time": "1774238400000"},
                    {"stage_id": "pending", "enter_time": "1774411200000"},
                ],
            },
            {
                "id": "app-decline",
                "talent_id": "tal-3",
                "active_status": 2,
                "termination_type": 22,
                "stage": {"id": "hr"},
                "stage_time_list": [
                    {"stage_id": "hr", "enter_time": "1774238400000"},
                ],
            },
            {
                "id": "app-reject",
                "talent_id": "tal-4",
                "active_status": 2,
                "termination_type": 1,
                "stage": {"id": "hr"},
                "stage_time_list": [
                    {"stage_id": "hr", "enter_time": "1774238400000"},
                ],
            },
        ]
        talent_names = {
            "tal-1": "张杰",
            "tal-2": "苗静思",
            "tal-3": "阮傅浩",
            "tal-4": "魏弘量",
        }

        hr = derive_hr_candidates(applications, stage_catalog, talent_names)

        self.assertEqual(4, hr["total"])
        labels_by_name = {item["name"]: item["label"] for item in hr["candidates"]}
        self.assertEqual("Offer 沟通中", labels_by_name["张杰"])
        self.assertEqual("待入职", labels_by_name["苗静思"])
        self.assertEqual("候选人放弃", labels_by_name["阮傅浩"])
        self.assertEqual("已淘汰", labels_by_name["魏弘量"])


if __name__ == "__main__":
    unittest.main()
