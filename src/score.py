"""
Turn the raw logs into one tidy table: one row per question asked.

Usage:
    python src/score.py          # real data
    python src/score.py --mock   # test data

Output: data/models/responses.csv with a column "risky":
    1 = chose the risky option, 0 = chose the sure option.
Replies that still couldn't be read after a second try are marked
invalid and left out of the analysis. Their count is printed per model.
"""

import argparse
import json

import pandas as pd

from config import model_dirs


def load_logs(raw_dir):
    rows = []
    for path in sorted(raw_dir.glob("*.jsonl")):
        with open(path) as f:
            rows += [json.loads(line) for line in f]
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    dirs = model_dirs(mock=args.mock)

    logs = load_logs(dirs["raw"])
    if logs.empty:
        print(f"No logs found in {dirs['raw']}. Run run_models.py first.")
        return

    final = logs[logs["final"]].copy()
    final["valid"] = final["choice"].notna()
    final["risky"] = (final["choice"] == "risky").astype(int)

    # How many replies needed a second try, and how many failed both times
    summary = final.groupby("model").agg(
        calls=("valid", "size"),
        invalid=("valid", lambda v: int((~v).sum())),
        needed_retry=("attempt", lambda a: int((a == 2).sum())),
        reasoning_setting=("reasoning_setting", lambda s: ", ".join(sorted(set(s)))),
        input_tokens=("input_tokens", "sum"),
        output_tokens=("output_tokens", "sum"),
    )
    print(summary.to_string())

    keep = ["model", "provider", "size", "scenario", "frame", "mode", "order", "run",
            "letter", "choice", "valid", "risky", "reasoning_setting"]
    final[keep].sort_values(["model", "scenario", "frame", "mode", "run"]).to_csv(
        dirs["responses"], index=False)
    dirs["tables"].mkdir(parents=True, exist_ok=True)
    summary.to_csv(dirs["tables"] / "model_call_summary.csv")
    print(f"\nSaved {len(final)} rows to {dirs['responses']}")


if __name__ == "__main__":
    main()
