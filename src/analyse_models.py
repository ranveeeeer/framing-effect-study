"""
Analyse the AI model answers.

For every model and mode (direct / step_by_step):
  - % choosing the risky option in each frame, with 95% confidence intervals
  - Fisher's exact test, gain vs loss
  - the framing gap = % risky (loss) - % risky (gain), in percentage points
    (the students' gap is the benchmark)

Usage:
    python src/analyse_models.py          # real data
    python src/analyse_models.py --mock   # test data
"""

import argparse

import pandas as pd

from config import model_dirs
from items import SCENARIOS
from stats_helpers import compare_frames


def frame_comparison(df):
    """Run compare_frames on a slice of the responses table."""
    g = df[df["frame"] == "gain"]["risky"]
    l = df[df["frame"] == "loss"]["risky"]
    return compare_frames(int(g.sum()), len(g), int(l.sum()), len(l))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    dirs = model_dirs(mock=args.mock)
    dirs["tables"].mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(dirs["responses"])
    data = data[data["valid"]]  # leave out replies that couldn't be read

    # 1. Pooled over the five scenarios
    pooled = []
    for (model, size, mode), df in data.groupby(["model", "size", "mode"], sort=False):
        pooled.append({"model": model, "size": size, "mode": mode, **frame_comparison(df)})
    pooled = pd.DataFrame(pooled)
    pooled.to_csv(dirs["tables"] / "models_pooled.csv", index=False)

    # 2. Each scenario separately
    per_scenario = []
    for (model, mode, scenario), df in data.groupby(["model", "mode", "scenario"], sort=False):
        per_scenario.append({"model": model, "mode": mode, "scenario": scenario,
                             **frame_comparison(df)})
    per_scenario = pd.DataFrame(per_scenario)
    per_scenario["scenario"] = pd.Categorical(per_scenario["scenario"], SCENARIOS)
    per_scenario = per_scenario.sort_values(["model", "mode", "scenario"])
    per_scenario.to_csv(dirs["tables"] / "models_by_scenario.csv", index=False)

    # 3. Does thinking step by step shrink the framing gap?
    gaps = pooled.pivot(index="model", columns="mode", values="gap_points")
    gaps["change"] = gaps["step_by_step"] - gaps["direct"]
    gaps = gaps.reset_index()
    gaps.to_csv(dirs["tables"] / "models_gap_direct_vs_step.csv", index=False)

    # 4. Side by side with the students, if their table exists
    students_path = model_dirs()["tables"] / "students_by_scenario.csv"
    if students_path.exists():
        st = pd.read_csv(students_path)
        st = st[st["scenario"] == "all"].assign(model="students", size="-", mode="-")
        both = pd.concat([st[pooled.columns], pooled], ignore_index=True)
        both.to_csv(dirs["tables"] / "students_vs_models.csv", index=False)

    cols = ["model", "mode", "pct_gain", "ci_gain", "pct_loss", "ci_loss", "gap_points", "fisher_p"]
    print("Pooled over five scenarios (% chose the risky option):")
    print(pooled[cols].to_string(index=False))
    print("\nFraming gap (points), direct vs step by step:")
    print(gaps.to_string(index=False))
    print(f"\nTables saved in {dirs['tables']}")


if __name__ == "__main__":
    main()
