#!/usr/bin/env python3
"""
token_stats.py — shittim API 用量统计工具

用法：
    # 记录一次使用（由 shittim 脚本调用）
    python3 token_stats.py record --model deepseek-v4-flash --type chat \
        --prompt 256 --completion 92 --cached 128

    # 查看统计报告
    python3 token_stats.py report

    # 查看今日统计
    python3 token_stats.py report --today
"""

import sys
import os
import json
import argparse
from datetime import datetime, date

STATS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "history", "token_stats.jsonl")

# DeepSeek 定价（美元/1M tokens，换算为人民币，汇率约 7.25）
PRICING = {
    "deepseek-v4-flash": {
        "input_cache_hit":  0.0028 * 7.25 / 1_000_000,   # ¥/千token
        "input_cache_miss": 0.14   * 7.25 / 1_000_000,
        "output":           0.28   * 7.25 / 1_000_000,
    },
    "deepseek-v4-pro": {
        "input_cache_hit":  0.003625 * 7.25 / 1_000_000,
        "input_cache_miss": 0.435    * 7.25 / 1_000_000,
        "output":           0.87     * 7.25 / 1_000_000,
    },
}
DEFAULT_MODEL = "deepseek-v4-flash"


def calc_cost(model, prompt_tokens, completion_tokens, cached_tokens=0):
    p = PRICING.get(model, PRICING[DEFAULT_MODEL])
    cache_hit   = cached_tokens
    cache_miss  = max(0, prompt_tokens - cached_tokens)
    cost = (cache_hit   * p["input_cache_hit"] +
            cache_miss  * p["input_cache_miss"] +
            completion_tokens * p["output"])
    return round(cost, 6)


def record(args):
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    entry = {
        "time":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model":      args.model,
        "type":       args.type,
        "prompt":     args.prompt,
        "completion": args.completion,
        "cached":     args.cached,
        "cost":       calc_cost(args.model, args.prompt, args.completion, args.cached),
    }
    with open(STATS_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_records(today_only=False):
    if not os.path.exists(STATS_FILE):
        return []
    records = []
    today_str = date.today().strftime("%Y-%m-%d")
    with open(STATS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                if today_only and not r["time"].startswith(today_str):
                    continue
                records.append(r)
            except Exception:
                continue
    return records


def report(args):
    records = load_records(today_only=args.today)
    if not records:
        print("暂无记录。")
        return

    # 按模型和类型汇总
    summary = {}
    for r in records:
        key = (r["model"], r["type"])
        if key not in summary:
            summary[key] = {"count": 0, "prompt": 0,
                            "completion": 0, "cached": 0, "cost": 0.0}
        s = summary[key]
        s["count"]      += 1
        s["prompt"]     += r["prompt"]
        s["completion"] += r["completion"]
        s["cached"]     += r["cached"]
        s["cost"]       += r["cost"]

    period = "今日" if args.today else "全部"
    total_cost = sum(s["cost"] for s in summary.values())
    total_requests = sum(s["count"] for s in summary.values())

    print(f"\n{'='*55}")
    print(f"  Shittim API 用量统计  [{period}]")
    print(f"{'='*55}")
    print(f"  总请求次数：{total_requests}")
    print(f"  预估总费用：¥{total_cost:.4f}")
    print(f"{'─'*55}")

    for (model, typ), s in sorted(summary.items()):
        print(f"\n  [{model}] {typ}")
        print(f"    请求次数：{s['count']}")
        print(f"    输入 tokens：{s['prompt']}  (缓存命中：{s['cached']})")
        print(f"    输出 tokens：{s['completion']}")
        print(f"    预估费用：¥{s['cost']:.4f}")

    print(f"\n{'='*55}")
    print(f"  注：价格按 DeepSeek 官方定价估算，汇率 7.25")
    print(f"  实际费用以 DeepSeek 控制台为准")
    print(f"{'='*55}\n")

    # 最近5条记录
    if not args.today:
        print("  最近5条记录：")
        for r in records[-5:]:
            print(f"  {r['time']}  {r['model']:20s} {r['type']:10s} "
                  f"p={r['prompt']:4d} c={r['completion']:4d} "
                  f"¥{r['cost']:.5f}")
        print()


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    rec = sub.add_parser("record")
    rec.add_argument("--model",      default="deepseek-v4-flash")
    rec.add_argument("--type",       default="chat")
    rec.add_argument("--prompt",     type=int, default=0)
    rec.add_argument("--completion", type=int, default=0)
    rec.add_argument("--cached",     type=int, default=0)

    rep = sub.add_parser("report")
    rep.add_argument("--today", action="store_true")

    args = parser.parse_args()
    if args.cmd == "record":
        record(args)
    elif args.cmd == "report":
        report(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()