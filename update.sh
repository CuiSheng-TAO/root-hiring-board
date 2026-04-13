#!/bin/bash
# update.sh — 从飞书拉取最新招聘数据并生成 data.js
# 依赖: lark-cli, python3
# 用法: ./update.sh
#
# 数据自动化状态（全部自动）：
#   entry        — ✅ Hire API: 总申请数 + 逐条 detail 统计评估通过数
#   writtenTest  — ✅ 飞书 Wiki 嵌入电子表格自动拉取
#   interview1/2 — ✅ 飞书电子表格自动拉取
#   候选人链接   — ✅ Hire API 自动拉取

set -e

export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_FILE="$SCRIPT_DIR/data.js"

echo "[招聘看板] 开始拉取飞书数据..."

# ─── 读取4个电子表格 ───
echo "  读取一面-12双月明细..."
SHEET1=$(lark-cli sheets +read \
  --url "https://deepwisdom.feishu.cn/sheets/HGh6splmdh8xgPtrDX1cNtT9ntb" \
  --range "0xmzyS!A1:I50" \
  --value-render-option ToString 2>/dev/null)

echo "  读取一面-3月明细..."
SHEET2=$(lark-cli sheets +read \
  --url "https://deepwisdom.feishu.cn/sheets/XZUIsXtH5hgMoZt5IGZcv2hxnHh" \
  --range "0zJdUJ!A1:I50" \
  --value-render-option ToString 2>/dev/null)

echo "  读取二面-本月明细..."
SHEET3=$(lark-cli sheets +read \
  --url "https://deepwisdom.feishu.cn/sheets/HrIosFttQhvq3qt6iIPcIum5nNg" \
  --range "0Zcujn!A1:I50" \
  --value-render-option ToString 2>/dev/null)

echo "  读取二面-12双月对比..."
SHEET4=$(lark-cli sheets +read \
  --url "https://deepwisdom.feishu.cn/sheets/Wq33sHFBihdjm2tLRaCc9zHynR1" \
  --range "0AspYr!A1:I50" \
  --value-render-option ToString 2>/dev/null)

# ─── 解析数据：提取原始面试记录（含日期） ───
# 统一用 Python 从 4 张表提取 interviewRecords 数组
# SHEET1 (一面12双月): col0=姓名(纯文本), col3=日期("YYYY-MM-DD HH:MM"), col4=结论, 无表头
# SHEET2 (一面3月):    col0=姓名(HYPERLINK), col6=日期(Excel serial), col8=结论, 有表头
# SHEET3 (二面本月):   同 SHEET2 列布局
# SHEET4 (二面12双月): 同 SHEET2 列布局
# 去重策略：SHEET1 + SHEET2 合并(round 1)，SHEET3 + SHEET4 合并(round 2)，同名取有链接的优先

# Save sheets to temp files for Python processing
TMPDIR_SHEETS=$(mktemp -d)
echo "$SHEET1" > "$TMPDIR_SHEETS/s1.json"
echo "$SHEET2" > "$TMPDIR_SHEETS/s2.json"
echo "$SHEET3" > "$TMPDIR_SHEETS/s3.json"
echo "$SHEET4" > "$TMPDIR_SHEETS/s4.json"

INTERVIEW_RECORDS=$(python3 << PYEOF
import json, re
from datetime import datetime, timedelta

def excel_to_date(serial):
    try:
        return (datetime(1899, 12, 30) + timedelta(days=float(serial))).strftime("%Y-%m-%d")
    except:
        return ""

def parse_name_cell(cell):
    cell = str(cell).strip()
    if not cell or cell == "None":
        return None
    m = re.search(r'HYPERLINK\("https://deepwisdom\.feishu\.cn/hire/talent/([^"?]+)\?application_id=([^"]+)",\s*"([^"]+)"\)', cell)
    if m:
        return {"name": m.group(3), "talent_id": m.group(1), "application_id": m.group(2)}
    if "HYPERLINK" not in cell:
        return {"name": cell}
    return None

def load_sheet(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

tmpdir = "$TMPDIR_SHEETS"
s1 = load_sheet(f"{tmpdir}/s1.json")
s2 = load_sheet(f"{tmpdir}/s2.json")
s3 = load_sheet(f"{tmpdir}/s3.json")
s4 = load_sheet(f"{tmpdir}/s4.json")

records = []
seen = set()

# SHEET2 (一面3月) first — HYPERLINK versions take priority
for row in s2.get("data", {}).get("valueRange", {}).get("values", [])[1:]:
    if not row or not row[0]: continue
    info = parse_name_cell(row[0])
    if not info: continue
    date_val = row[6] if len(row) > 6 and row[6] else ""
    result = str(row[8]) if len(row) > 8 and row[8] else ""
    key = (info["name"], 1)
    if key not in seen:
        seen.add(key)
        records.append({**info, "round": 1, "date": excel_to_date(date_val) if date_val else "", "result": result})

# SHEET1 (一面12双月) — fill in missing
for row in s1.get("data", {}).get("valueRange", {}).get("values", []):
    if not row or not row[0]: continue
    info = parse_name_cell(row[0])
    if not info: continue
    date_val = str(row[3]).strip() if len(row) > 3 and row[3] else ""
    result = str(row[4]) if len(row) > 4 and row[4] else ""
    date_str = date_val[:10] if date_val and date_val != "None" else ""
    key = (info["name"], 1)
    if key not in seen:
        seen.add(key)
        records.append({**info, "round": 1, "date": date_str, "result": result})
    else:
        for r in records:
            if r["name"] == info["name"] and r["round"] == 1 and not r["date"] and date_str:
                r["date"] = date_str

# SHEET3 (二面本月) first — HYPERLINK priority
for row in s3.get("data", {}).get("valueRange", {}).get("values", [])[1:]:
    if not row or not row[0]: continue
    info = parse_name_cell(row[0])
    if not info: continue
    date_val = row[6] if len(row) > 6 and row[6] else ""
    result = str(row[8]) if len(row) > 8 and row[8] else ""
    key = (info["name"], 2)
    if key not in seen:
        seen.add(key)
        records.append({**info, "round": 2, "date": excel_to_date(date_val) if date_val else "", "result": result})

# SHEET4 (二面12双月)
for row in s4.get("data", {}).get("valueRange", {}).get("values", [])[1:]:
    if not row or not row[0]: continue
    info = parse_name_cell(row[0])
    if not info: continue
    date_val = row[6] if len(row) > 6 and row[6] else ""
    result = str(row[8]) if len(row) > 8 and row[8] else ""
    key = (info["name"], 2)
    if key not in seen:
        seen.add(key)
        records.append({**info, "round": 2, "date": excel_to_date(date_val) if date_val else "", "result": result})

# Cross-reference talent_id across rounds
name_map = {}
for r in records:
    if r.get("talent_id") and r["name"] not in name_map:
        name_map[r["name"]] = {"talent_id": r["talent_id"], "application_id": r.get("application_id", "")}
for r in records:
    if not r.get("talent_id") and r["name"] in name_map:
        r["talent_id"] = name_map[r["name"]]["talent_id"]
        r["application_id"] = name_map[r["name"]]["application_id"]

print(json.dumps(records, ensure_ascii=False))
PYEOF
)

rm -rf "$TMPDIR_SHEETS"

RECORD_COUNT=$(echo "$INTERVIEW_RECORDS" | python3 -c "import json,sys; r=json.load(sys.stdin); print(f'Round 1: {sum(1 for x in r if x[\"round\"]==1)}, Round 2: {sum(1 for x in r if x[\"round\"]==2)}')")
echo "  面试记录: $RECORD_COUNT"

UPDATE_TIME=$(date "+%Y.%m.%d %H:%M")

# ─── 入口数据：从 Hire API 拉取总申请数 + 评估通过数 ───
echo "  拉取入口数据（Hire API 全量）..."

ENTRY_JSON=$(python3 << 'PYEOF'
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

JOBS = ["7539897631183980810", "7593964671033100563"]

def list_all_app_ids():
    """Paginate all application IDs for both jobs."""
    all_ids = []
    for job_id in JOBS:
        pt = ""
        while True:
            params = {"job_id": job_id, "page_size": "200"}
            if pt:
                params["page_token"] = pt
            r = subprocess.run(
                ["lark-cli", "api", "GET", "/open-apis/hire/v1/applications",
                 "--params", json.dumps(params), "--as", "bot"],
                capture_output=True, text=True)
            if r.returncode != 0 or not r.stdout.strip():
                break
            d = json.loads(r.stdout)
            all_ids.extend(d.get("data", {}).get("items", []))
            if not d.get("data", {}).get("has_more"):
                break
            pt = d.get("data", {}).get("page_token", "")
    return all_ids

def get_app_detail(app_id):
    """Fetch single application detail."""
    r = subprocess.run(
        ["lark-cli", "api", "GET", f"/open-apis/hire/v1/applications/{app_id}", "--as", "bot"],
        capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    d = json.loads(r.stdout)
    return d.get("data", {}).get("application", {})

print("  listing...", file=sys.stderr)
app_ids = list_all_app_ids()
total = len(app_ids)
print(f"  {total} applications found, fetching details...", file=sys.stderr)

passed_screening = 0
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(get_app_detail, aid): aid for aid in app_ids}
    done = 0
    for f in as_completed(futures):
        done += 1
        if done % 500 == 0:
            print(f"  ...{done}/{total}", file=sys.stderr)
        app = f.result()
        if not app:
            continue
        stages = app.get("stage_time_list", [])
        stage_type = app.get("stage", {}).get("type", 0)
        if len(stages) > 1 or stage_type > 2:
            passed_screening += 1

rate = round(passed_screening / total * 100) if total > 0 else 0
print(json.dumps({"total": total, "passed": passed_screening, "rate": rate}))
PYEOF
)

ENTRY_RESUMES=$(echo "$ENTRY_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['total'])")
ENTRY_PASSED=$(echo "$ENTRY_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['passed'])")
ENTRY_RATE=$(echo "$ENTRY_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['rate'])")
echo "  入口: $ENTRY_RESUMES 份简历, $ENTRY_PASSED 通过评估 ($ENTRY_RATE%)"

# ─── 笔试数据：从 Wiki 嵌入电子表格自动拉取 ───
echo "  读取笔试 Pipeline 电子表格..."

WRITTEN_SHEET=$(lark-cli sheets +read \
  --url "https://deepwisdom.feishu.cn/sheets/XxpusdPtoh5pkwtpKSicPDjYnlh" \
  --range "HgPg6g!A1:I300" \
  --value-render-option ToString 2>/dev/null)

WRITTEN_JSON=$(echo "$WRITTEN_SHEET" | python3 -c "
import json, sys
data = json.load(sys.stdin)
rows = data.get('data', {}).get('valueRange', {}).get('values', [])
collected = 0
in_progress = 0
passed = 0
rejected = 0
for row in rows[1:]:
    if not row or not row[0]:
        continue
    g = str(row[6]).strip() if len(row) > 6 and row[6] else ''
    i = str(row[8]).strip() if len(row) > 8 and row[8] else ''
    if g == '已回收':
        collected += 1
    elif g == '笔试中':
        in_progress += 1
    if i == '通过':
        passed += 1
    elif i == '不通过':
        rejected += 1
print(json.dumps({'collected': collected, 'passed': passed, 'inProgress': in_progress, 'rejected': rejected}))
")

WRITTEN_COLLECTED=$(echo "$WRITTEN_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['collected'])")
WRITTEN_PASSED=$(echo "$WRITTEN_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['passed'])")
WRITTEN_IN_PROGRESS=$(echo "$WRITTEN_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['inProgress'])")
WRITTEN_REJECTED=$(echo "$WRITTEN_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['rejected'])")
echo "  笔试: 已回收 $WRITTEN_COLLECTED, 通过 $WRITTEN_PASSED, 笔试中 $WRITTEN_IN_PROGRESS, 不通过 $WRITTEN_REJECTED"

echo "  解析完成。"

# ─── 生成 data.js ───
cat > "$DATA_FILE" << JSEOF
// 自动生成 — 请勿手动编辑
// 更新时间: $UPDATE_TIME
// 数据来源: Hire API(入口) + Wiki 电子表格(笔试) + 飞书电子表格(面试) + Hire API(候选人链接)

const DASHBOARD_DATA = {
  updateTime: "$UPDATE_TIME",

  // 目标
  target: {
    goal: 10,
    current: 6,
    gap: 4
  },

  // 入口（✅ Hire API 自动拉取）
  entry: {
    resumesSent: $ENTRY_RESUMES,
    assessPassed: $ENTRY_PASSED,
    assessRate: $ENTRY_RATE
  },

  // 笔试（✅ Wiki 嵌入电子表格自动拉取）
  writtenTest: {
    collected: $WRITTEN_COLLECTED,
    passed: $WRITTEN_PASSED,
    inProgress: $WRITTEN_IN_PROGRESS,
    rejected: $WRITTEN_REJECTED
  },

  // 面试记录（含日期，前端按时间段动态聚合）
  // round: 1=一面, 2=二面
  interviewRecords: $INTERVIEW_RECORDS,

  // HR面（⚠️ 手动维护 — 候选人不常变动）
  hrInterview: {
    total: 4,
    candidates: [
      { name: "苗静思", status: "accept", label: "Offer 接受", role: "Root 全栈", date: "近期", nextAction: null, talent_id: "7605124900320495881", application_id: "7605124896885311771" },
      { name: "张杰", status: "accept", label: "Offer 沟通中", role: "Root 全栈", date: "近期", nextAction: null, talent_id: "7601899456342821129", application_id: "7621085664163563786" },
      { name: "阮傅浩", status: "reject", label: "无意向换工作", role: "Root 全栈", date: "近期", nextAction: null, talent_id: "7618999486904338697", application_id: "7618999656626489650" },
      { name: "魏弘量", status: "decline", label: "拒绝 Offer", role: "Root 全栈", date: "近期", nextAction: null, talent_id: "7615575380410386694", application_id: "7615617644800215346" }
    ]
  },

  // 链接
  links: {
    hireReport: "https://deepwisdom.feishu.cn/hire/reports/7578526668101258184",
    wiki: "https://deepwisdom.feishu.cn/wiki/Un5MwIF0oimoSukvwvjca9fznoN",
    writtenTestPipeline: "https://deepwisdom.feishu.cn/wiki/NUMRwkfCeiVrGMkF4TWc7EZ0nxg",
    interview1_3m: "https://deepwisdom.feishu.cn/hire/reports/762705618927226317/widgets/7627056189327576021",
    interview2_detail: "https://deepwisdom.feishu.cn/hire/reports/7627056633239292891/widgets/_"
  }
};
JSEOF

echo "[招聘看板] data.js 已更新: $DATA_FILE"
echo "[招聘看板] 刷新浏览器即可看到最新数据"
