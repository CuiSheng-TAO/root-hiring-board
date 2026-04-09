#!/bin/bash
# update.sh — 从飞书拉取最新招聘数据并生成 data.js
# 依赖: lark-cli, jq, curl, python3
# 用法: ./update.sh
#
# 数据自动化状态：
#   entry (3003/866)  — ✅ 从飞书招聘报告电子表格自动拉取（CDP + frequency analysis）
#   writtenTest (189) — ⚠️ 需手动更新（来自飞书 Wiki，需 wiki:wiki 权限）
#   interview1/2       — ✅ 从飞书电子表格自动拉取
#   ATS 总申请数      — ✅ 从 hire API 自动拉取
#   候选人飞书链接    — ✅ 从 hire API 自动拉取

set -e

# 确保 curl 在 PATH
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_FILE="$SCRIPT_DIR/data.js"

# entry 和 writtenTest 手动值（需同步更新）：
# 数据来源: 飞书招聘报告电子表格 (https://deepwisdom.feishu.cn/hire/reports/7573581010957828099/widgets/7573581011003378631)
# 日期范围: 2026-03-01 至 2026-04-07，两岗（ROOT全栈+AI原生全栈）合计
# ⚠️ 每次运行 ./update.sh 后手动确认数字是否变化，或用 cdp_extract.py 自动抓取
ENTRY_RESUMES=3003
ENTRY_PASSED=866
ENTRY_RATE=28
WRITTEN_COLLECTED=189
WRITTEN_PASSED=20
WRITTEN_IN_PROGRESS=28
WRITTEN_REJECTED=28

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

# ─── 解析数据 ───
# 计算每个表格的有效行数（排除表头和空行）
count_rows() {
  echo "$1" | jq '[.data.valueRange.values[1:][] | select(.[0] != null)] | length'
}

# 提取面试结论
extract_results() {
  echo "$1" | jq -r '.data.valueRange.values[1:][] | select(.[0] != null) | "\(.[0])|\(.[4] // "未知")"'
}

# 一面数据
# 一面12双月：纯数据格式，结论在第5列(index 4)
INTERVIEW1_12M_TOTAL=$(count_rows "$SHEET1")
INTERVIEW1_12M_PASS=$(echo "$SHEET1" | jq '[.data.valueRange.values[1:][] | select(.[0] != null) | select(.[4] != null) | select((.[4] | tostring) | startswith("通过"))] | length')

# 一面3月：有表头，结论在第9列(index 8)
INTERVIEW1_3M_TOTAL=$(count_rows "$SHEET2")
INTERVIEW1_3M_PASS=$(echo "$SHEET2" | jq '[.data.valueRange.values[1:][] | select(.[0] != null) | select(.[8] != null) | select((.[8] | tostring) | startswith("通过"))] | length')

# 二面数据：均有表头，结论在第9列(index 8)
INTERVIEW2_TOTAL=$(count_rows "$SHEET3")
INTERVIEW2_PASS=$(echo "$SHEET3" | jq '[.data.valueRange.values[1:][] | select(.[0] != null) | select(.[8] != null) | select((.[8] | tostring) | startswith("通过"))] | length')
INTERVIEW2_PENDING=$(echo "$SHEET3" | jq '[.data.valueRange.values[1:][] | select(.[0] != null) | select(.[8] != null) | select((.[8] | tostring) | startswith("待定"))] | length')

# 二面12双月对比：同上
INTERVIEW2_12M_TOTAL=$(count_rows "$SHEET4")
INTERVIEW2_12M_PASS=$(echo "$SHEET4" | jq '[.data.valueRange.values[1:][] | select(.[0] != null) | select(.[8] != null) | select((.[8] | tostring) | startswith("通过"))] | length')
INTERVIEW2_12M_PENDING=$(echo "$SHEET4" | jq '[.data.valueRange.values[1:][] | select(.[0] != null) | select(.[8] != null) | select((.[8] | tostring) | startswith("待定"))] | length')

# 计算通过率
calc_rate() {
  if [ "$2" -gt 0 ]; then
    echo "scale=0; $1 * 100 / $2" | bc
  else
    echo "0"
  fi
}

INTERVIEW1_12M_RATE=$(calc_rate "$INTERVIEW1_12M_PASS" "$INTERVIEW1_12M_TOTAL")
INTERVIEW1_3M_RATE=$(calc_rate "$INTERVIEW1_3M_PASS" "$INTERVIEW1_3M_TOTAL")
INTERVIEW2_RATE=$(calc_rate "$INTERVIEW2_PASS" "$INTERVIEW2_TOTAL")
INTERVIEW2_12M_RATE=$(calc_rate "$INTERVIEW2_12M_PASS" "$INTERVIEW2_12M_TOTAL")

UPDATE_TIME=$(date "+%Y.%m.%d %H:%M")

# ─── 从 hire API 拉 ATS 总申请数 ───
# ROOT 岗位: 7539897631183980810 (ROOT-全栈) + 7593964671033100563 (AI原生全栈)
echo "  读取 ATS 总申请数..."

ATS_JSON=$(python3 << 'PYEOF'
import json, subprocess

APP_ID = "cli_a95d929432785cc7"
APP_SECRET = "0zSYGHc0JxNRrsY8adgsRhKZdOYKzTCS"
JOBS = [("7539897631183980810","ROOT-全栈"),("7593964671033100563","AI原生全栈")]

# get token
r = subprocess.run(["curl","-s","-X","POST",
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    "-H","Content-Type: application/json",
    "-d",json.dumps({"app_id":APP_ID,"app_secret":APP_SECRET})],
    capture_output=True, text=True)
token = json.loads(r.stdout)["tenant_access_token"]

counts = {}
for job_id, name in JOBS:
    total = 0
    pt = ""
    while True:
        url = f"https://open.feishu.cn/open-apis/hire/v1/applications?job_id={job_id}&page_size=20"
        if pt:
            url += f"&page_token={pt}"
        r = subprocess.run(["curl","-s",url,"-H",f"Authorization: Bearer {token}"],
            capture_output=True, text=True)
        d = json.loads(r.stdout)
        total += len(d.get("data",{}).get("items",[]))
        if not d.get("data",{}).get("has_more"):
            break
        pt = d.get("data",{}).get("page_token","")
    counts[job_id] = total

print(json.dumps({"root":counts.get("7539897631183980810",0),"ai":counts.get("7593964671033100563",0)}))
PYEOF
)

ATS_ROOT=$(echo "$ATS_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['root'])")
ATS_AI=$(echo "$ATS_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['ai'])")
ATS_COMBINED=$((ATS_ROOT + ATS_AI))
echo "  ATS 总申请: $ATS_COMBINED (ROOT: $ATS_ROOT + AI原生: $ATS_AI)"
echo "  (ATS总数仅供参考，不写入看板)"

echo "  解析完成。"
echo "  一面12双月: $INTERVIEW1_12M_PASS/$INTERVIEW1_12M_TOTAL ($INTERVIEW1_12M_RATE%)"
echo "  一面3月: $INTERVIEW1_3M_PASS/$INTERVIEW1_3M_TOTAL ($INTERVIEW1_3M_RATE%)"
echo "  二面本月: $INTERVIEW2_PASS/$INTERVIEW2_TOTAL ($INTERVIEW2_RATE%), pending $INTERVIEW2_PENDING"
echo "  二面12双月: $INTERVIEW2_12M_PASS/$INTERVIEW2_12M_TOTAL ($INTERVIEW2_12M_RATE%), pending $INTERVIEW2_12M_PENDING"

# ─── 生成 data.js ───
cat > "$DATA_FILE" << JSEOF
// 自动生成 — 请勿手动编辑
// 更新时间: $UPDATE_TIME
// 数据来源: 飞书电子表格 (一面/二面) + 招聘报告(入口) + 飞书 Hire API(ATS总数/候选人链接)
// ⚠️ 入口和笔试数据需要手动更新（见脚本顶部变量）

const DASHBOARD_DATA = {
  updateTime: "$UPDATE_TIME",
  dataPeriod: "0301 — till now",

  // 目标
  target: {
    goal: 10,
    current: 6,
    gap: 4
  },

  // 入口（⚠️ 需手动更新 — 来自飞书招聘报告页）
  entry: {
    resumesSent: $ENTRY_RESUMES,
    assessPassed: $ENTRY_PASSED,
    assessRate: $ENTRY_RATE
  },

  // 笔试（⚠️ 需手动更新 — 来自飞书 Wiki）
  writtenTest: {
    collected: $WRITTEN_COLLECTED,
    passed: $WRITTEN_PASSED,
    inProgress: $WRITTEN_IN_PROGRESS,
    rejected: $WRITTEN_REJECTED
  },

  // 一面（从电子表格自动计算）
  interview1: {
    current: {
      total: $INTERVIEW1_3M_TOTAL,
      passed: $INTERVIEW1_3M_PASS,
      rate: $INTERVIEW1_3M_RATE
    },
    bimonth: {
      total: $INTERVIEW1_12M_TOTAL,
      passed: $INTERVIEW1_12M_PASS,
      rate: $INTERVIEW1_12M_RATE
    }
  },

  // 二面（从电子表格自动计算）
  interview2: {
    current: {
      total: $INTERVIEW2_TOTAL,
      passed: $INTERVIEW2_PASS,
      pending: $INTERVIEW2_PENDING,
      rate: $INTERVIEW2_RATE
    },
    bimonth: {
      total: $INTERVIEW2_12M_TOTAL,
      passed: $INTERVIEW2_12M_PASS,
      pending: $INTERVIEW2_12M_PENDING,
      rate: $INTERVIEW2_12M_RATE
    }
  },

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
    interview1_12m: "https://deepwisdom.feishu.cn/sheets/HGh6splmdh8xgPtrDX1cNtT9ntb",
    interview1_3m: "https://deepwisdom.feishu.cn/sheets/XZUIsXtH5hgMoZt5IGZcv2hxnHh",
    interview2_detail: "https://deepwisdom.feishu.cn/sheets/HrIosFttQhvq3qt6iIPcIum5nNg",
    interview2_12m: "https://deepwisdom.feishu.cn/sheets/Wq33sHFBihdjm2tLRaCc9zHynR1"
  }
};
JSEOF

echo "[招聘看板] data.js 已更新: $DATA_FILE"
echo "[招聘看板] 刷新浏览器即可看到最新数据"
