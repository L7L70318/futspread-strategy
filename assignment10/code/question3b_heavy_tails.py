"""Assignment 10 Question 3(b): pooled within-instance spread kurtosis."""
from pathlib import Path

import numpy as np
import pandas as pd

from futspread import load_combo


WORKSPACE = Path(__file__).resolve().parents[2]
ROOT = WORKSPACE / "futspread_data"
OUT = WORKSPACE / "assignment10" / "results" / "submission"
DIAGNOSTICS = WORKSPACE / "assignment10" / "results" / "diagnostics"
SPREADS = ["NG[H][J0]", "CL[F][G0]", "HE[J][M0]"]


def standardized_changes(combo: str):
    data = load_combo(combo, ROOT)
    data = data[
        data.instance.between(2000, 2025)
        & data.td_to_ltd.between(-250, -2)
    ].sort_values(["instance", "date"])
    rows = []
    instance_stats = []
    for instance, group in data.groupby("instance"):
        changes = group.settlement.diff().dropna()
        mean = float(changes.mean())
        std = float(changes.std(ddof=1))
        if len(changes) < 2 or not np.isfinite(std) or std <= 0:
            continue
        z = (changes - mean) / std
        rows.append(pd.DataFrame({
            "combo": combo, "instance": int(instance), "z": z.to_numpy(),
            "z4": z.to_numpy() ** 4,
        }))
        instance_stats.append({
            "combo": combo, "instance": int(instance),
            "observations": len(changes), "mean_change": mean,
            "std_change": std,
        })
    return pd.concat(rows, ignore_index=True), pd.DataFrame(instance_stats)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
    pooled_parts = []
    stat_parts = []
    summary = []
    for combo in SPREADS:
        pooled, stats = standardized_changes(combo)
        pooled_parts.append(pooled)
        stat_parts.append(stats)
        summary.append({
            "Spread": combo,
            "Instances": int(stats.instance.nunique()),
            "Standardized daily changes": len(pooled),
            "Kurtosis E[z^4]": float(pooled.z4.mean()),
            "Excess above normal": float(pooled.z4.mean() - 3.0),
            "Abs(z) > 4 observations": int((pooled.z.abs() > 4).sum()),
            "Abs(z) > 4 rate": float((pooled.z.abs() > 4).mean()),
        })
    result = pd.DataFrame(summary)
    result.to_csv(OUT / "question3b_kurtosis.csv", index=False)
    pd.concat(stat_parts, ignore_index=True).to_csv(
        DIAGNOSTICS / "question3b_instance_stats.csv", index=False)
    pd.concat(pooled_parts, ignore_index=True).to_parquet(
        DIAGNOSTICS / "question3b_standardized_changes.parquet", index=False)

    display = result.copy()
    display["Kurtosis E[z^4]"] = display["Kurtosis E[z^4]"].map(
        lambda value: f"{value:.3f}")
    display["Excess above normal"] = display["Excess above normal"].map(
        lambda value: f"{value:.3f}")
    display["Abs(z) > 4 rate"] = display["Abs(z) > 4 rate"].map(
        lambda value: f"{value:.3%}")
    answer = rf"""# Question 3(b). Heavy tails

For each of `NG[H][J0]`, `CL[F][G0]`, and `HE[J][M0]`, I kept contract-year
instances 2000--2025 and observations with `td_to_ltd` from -250 through -2.
Within each instance I computed the daily spread-price difference
$\Delta S_t=S_t-S_{{t-1}}$, estimated that instance's own sample mean and sample
standard deviation, and formed $z_t=(\Delta S_t-\bar{{\Delta S}})/s_{{\Delta S}}$.
I then pooled the standardized observations across instances of the same spread
and calculated the raw kurtosis as the pooled average of $z_t^4$ (not Fisher
excess kurtosis).

The stored `CL[F][G0]` file has no 2000 instance, so its available sample is
2001--2025 (25 instances); the other two spreads contain all 26 instances from
2000--2025.

{display.to_markdown(index=False)}

All three kurtoses are greater than the normal benchmark of 3, so all three
spreads have heavy-tailed daily changes after controlling for differences in
mean and volatility across contract-year instances. The fourth-power statistic
is especially large for the spread with the highest reported kurtosis, meaning
that a relatively small number of extreme standardized moves has a large
effect on the estimate. The `Abs(z) > 4` counts are included as a transparent
cross-check; under normality such events would occur only about 0.006% of the
time.
"""
    (OUT / "assignment_question3b.md").write_text(answer)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
