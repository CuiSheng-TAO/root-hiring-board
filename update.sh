#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[ROOT 招聘看板] 生成结构化 data.json ..."
python3 generate_dashboard_data.py --config dashboard.config.json --output data.json
echo "[ROOT 招聘看板] 已完成。刷新页面即可拉取最新数据。"
