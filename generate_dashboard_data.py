#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dashboard_data import build_dashboard_payload, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate structured dashboard data from Feishu Hire."
    )
    parser.add_argument(
        "--config",
        default="dashboard.config.json",
        help="Path to dashboard config JSON.",
    )
    parser.add_argument(
        "--output",
        default="data.json",
        help="Path to write the generated JSON payload.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    payload = build_dashboard_payload(config)

    output_path = Path(args.output)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote dashboard payload to {output_path}")


if __name__ == "__main__":
    main()
