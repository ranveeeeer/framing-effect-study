"""
Analyse the student survey.

Input: the two Google Forms exports, saved as
    data/students/gain.csv
    data/students/loss.csv

Rule: only the first 15 responses per form (by time submitted) are used,
so both groups are the same size. The rule is fixed in advance, so no one
picks which students to keep.

Usage:
    python src/analyse_students.py
"""

import pandas as pd
from scipy.stats import mannwhitneyu, sem, t

from config import N_STUDENTS_PER_FRAME, STUDENT_DIR, model_dirs
from items import SCENARIOS
from stats_helpers import compare_frames

# Words that identify each question's column in the Forms export
COLUMN_KEYWORDS = {
    "health": "600 people",
    "money": "30,000",
    "marks": "30 marks",
    "jobs": "300 jobs",
    "crops": "90 acres",
}

# The result reported at the showcase. The code must reproduce it.
EXPECTED_RISKY = {
    "gain": {"health": 9, "money": 8, "marks": 7, "jobs": 8, "crops": 6},
    "loss": {"health": 12, "money": 11, "marks": 9, "jobs": 12, "crops": 10},
}


def find_column(columns, keyword):
    matches = [c for c in columns if keyword in c]
    if len(matches) != 1:
        raise ValueError(f"Expected one column containing '{keyword}', found {matches}")
    return matches[0]


def is_risky(answer):
    """Every risky option, in both frames, starts 'There is a probability...'."""
    return int("probability" in str(answer).lower())


def per_student_ci(scores, n_questions=5):
    """95% confidence interval for the average % risky, treating each student as one data point."""
    share = scores / n_questions
    low, high = t.interval(0.95, len(share) - 1, loc=share.mean(), scale=sem(share))
    return f"{100 * max(0, low):.0f}-{100 * min(1, high):.0f}"


def load_form(frame):
    df = pd.read_csv(STUDENT_DIR / f"{frame}.csv")

    # Order by time submitted. Google Forms already exports in that order,
    # so if the timestamps can't be read we simply keep the file order.
    if "Timestamp" in df.columns:
        times = pd.to_datetime(df["Timestamp"], errors="coerce", format="mixed")
        if times.notna().all():
            df = df.assign(_t=times).sort_values("_t", kind="stable").drop(columns="_t")

    # A valid response answers all five questions
    cols = {s: find_column(df.columns, kw) for s, kw in COLUMN_KEYWORDS.items()}
    df = df.dropna(subset=list(cols.values()))
    print(f"{frame}: {len(df)} valid responses, using the first {N_STUDENTS_PER_FRAME}")
    df = df.head(N_STUDENTS_PER_FRAME)

    out = pd.DataFrame({s: df[c].map(is_risky) for s, c in cols.items()})
    out["frame"] = frame
    return out.reset_index(drop=True)


def main():
    gain, loss = load_form("gain"), load_form("loss")
    tables = model_dirs()["tables"]
    tables.mkdir(parents=True, exist_ok=True)

    # Check against the reported result before going further
    for frame, df in [("gain", gain), ("loss", loss)]:
        for s in SCENARIOS:
            got, want = int(df[s].sum()), EXPECTED_RISKY[frame][s]
            if got != want:
                raise SystemExit(
                    f"MISMATCH: {frame}/{s} risky = {got}, expected {want}. "
                    "Check the CSV files before trusting any results.")
    print("Check passed: counts match the reported result (38/75 vs 54/75).\n")

    # 1. Each scenario, and all five pooled
    rows = []
    for s in SCENARIOS:
        rows.append({"scenario": s, **compare_frames(
            int(gain[s].sum()), len(gain), int(loss[s].sum()), len(loss))})
    # Pooled row. Each student answered all five questions, so the 75 answers
    # per frame are NOT independent. The confidence interval and the test for
    # this row are therefore worked out per student (score out of 5), not per
    # answer, which would make the result look more certain than it is.
    gain_scores = gain[SCENARIOS].sum(axis=1)
    loss_scores = loss[SCENARIOS].sum(axis=1)
    _, p_mw = mannwhitneyu(gain_scores, loss_scores, alternative="two-sided")
    pooled = compare_frames(int(gain_scores.sum()), gain[SCENARIOS].size,
                            int(loss_scores.sum()), loss[SCENARIOS].size)
    pooled["ci_gain"] = per_student_ci(gain_scores)
    pooled["ci_loss"] = per_student_ci(loss_scores)
    pooled["fisher_p"] = None
    pooled["mann_whitney_p"] = round(p_mw, 4)
    rows.append({"scenario": "all", **pooled})
    by_scenario = pd.DataFrame(rows)
    by_scenario.to_csv(tables / "students_by_scenario.csv", index=False)
    print(by_scenario.to_string(index=False))
    print("(The 'all' row uses per-student intervals and the Mann-Whitney test.)")

    # 2. Each student's number of risky choices out of 5
    per_student = pd.DataFrame([{
        "mean_risky_gain": round(gain_scores.mean(), 2),
        "mean_risky_loss": round(loss_scores.mean(), 2),
        "majority_risky_gain": f"{int((gain_scores >= 3).sum())}/{len(gain_scores)}",
        "majority_risky_loss": f"{int((loss_scores >= 3).sum())}/{len(loss_scores)}",
        "mann_whitney_p": round(p_mw, 4),
    }])
    per_student.to_csv(tables / "students_per_student.csv", index=False)
    print("\nRisky choices per student (out of 5):")
    print(per_student.to_string(index=False))


if __name__ == "__main__":
    main()
