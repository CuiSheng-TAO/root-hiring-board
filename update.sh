#!/bin/bash
# update.sh — 从飞书拉取最新招聘数据并生成 data.js
# 依赖: lark-cli, jq
# 用法: ./update.sh

set -e

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

# ─── 解析数据 ───
# 计算每个表格的有效行数（排除表头和空行）
count_rows() {
  echo "$1" | jq '[.data.valueRange.values[1:][] | select(.[0] != null)] | length'
}

# 提取面试结论
extract_results() {
  echo "$1" | jq -r '.data.valueRange.values[1:][] | select(.[0] != null) | "\(.[0])|\(.[8] // "未知")"'
}

# 一面数据
INTERVIEW1_12M_TOTAL=$(count_rows "$SHEET1")
INTERVIEW1_12M_PASS=$(echo "$SHEET1" | jq '[.data.valueRange.values[1:][] | select(.[0] != null) | select(.[8] != null) | select((.[-1] | tostring) | startswith("通过"))] | length')

INTERVIEW1_3M_TOTAL=$(count_rows "$SHEET2")
INTERVIEW1_3M_PASS=$(echo "$SHEET2" | jq '[.data.valueRange.values[1:][] | select(.[0] != null) | select(.[8] != null) | select((.[-1] | tostring) | startswith("通过"))] | length')

# 二面数据
INTERVIEW2_TOTAL=$(count_rows "$SHEET3")
INTERVIEW2_PASS=$(echo "$SHEET3" | jq '[.data.valueRange.values[1:][] | select(.[0] != null) | select(.[8] != null) | select((.[-1] | tostring) | startswith("通过"))] | length')
INTERVIEW2_PENDING=$(echo "$SHEET3" | jq '[.data.valueRange.values[1:][] | select(.[0] != null) | select(.[8] != null) | select((.[-1] | tostring) | startswith("待定"))] | length')

INTERVIEW2_12M_TOTAL=$(count_rows "$SHEET4")
INTERVIEW2_12M_PASS=$(echo "$SHEET4" | jq '[.data.valueRange.values[1:][] | select(.[0] != null) | select(.[8] != null) | select((.[-1] | tostring) | startswith("通过"))] | length')
INTERVIEW2_12M_PENDING=$(echo "$SHEET4" | jq '[.data.valueRange.values[1:][] | select(.[0] != null) | select(.[8] != null) | select((.[-1] | tostring) | startswith("待定"))] | length')

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

echo "  解析完成。"
echo "  一面12双月: $INTERVIEW1_12M_PASS/$INTERVIEW1_12M_TOTAL ($INTERVIEW1_12M_RATE%)"
echo "  一面3月: $INTERVIEW1_3M_PASS/$INTERVIEW1_3M_TOTAL ($INTERVIEW1_3M_RATE%)"
echo "  二面本月: $INTERVIEW2_PASS/$INTERVIEW2_TOTAL ($INTERVIEW2_RATE%), pending $INTERVIEW2_PENDING"
echo "  二面12双月: $INTERVIEW2_12M_PASS/$INTERVIEW2_12M_TOTAL ($INTERVIEW2_12M_RATE%), pending $INTERVIEW2_12M_PENDING"

# ─── 生成 data.js ───
cat > "$DATA_FILE" << JSEOF
// 自动生成 — 请勿手动编辑
// 更新时间: $UPDATE_TIME
// 数据来源: 飞书电子表格 + 招聘报告

const DASHBOARD_DATA = {
  updateTime: "$UPDATE_TIME",
  dataPeriod: "0301 — till now",

  // 目标
  target: {
    goal: 10,
    current: 6,
    gap: 4
  },

  // 入口（这些数据来自招聘报告，需手动更新或接入 Hire API）
  entry: {
    resumesSent: 247,
    assessPassed: 86,
    assessRate: 34
  },

  // 笔试（来自 wiki，需手动更新）
  writtenTest: {
    collected: 26,
    passed: 20,
    inProgress: 28,
    rejected: 28
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

  // HR面（需手动更新）
  hrInterview: {
    total: 4,
    candidates: [
      { name: "苗静思", status: "accept", label: "Offer 接受" },
      { name: "张杰", status: "pending", label: "待反馈" },
      { name: "阮傅浩", status: "reject", label: "无意向换工作" },
      { name: "魏弘量", status: "decline", label: "拒绝 Offer" }
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
