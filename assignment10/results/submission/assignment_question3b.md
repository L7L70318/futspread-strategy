# Question 3(b). Heavy tails

For each of `NG[H][J0]`, `CL[F][G0]`, and `HE[J][M0]`, I kept contract-year
instances 2000--2025 and observations with `td_to_ltd` from -250 through -2.
Within each instance I computed the daily spread-price difference
$\Delta S_t=S_t-S_{t-1}$, estimated that instance's own sample mean and sample
standard deviation, and formed $z_t=(\Delta S_t-\bar{\Delta S})/s_{\Delta S}$.
I then pooled the standardized observations across instances of the same spread
and calculated the raw kurtosis as the pooled average of $z_t^4$ (not Fisher
excess kurtosis).

The stored `CL[F][G0]` file has no 2000 instance, so its available sample is
2001--2025 (25 instances); the other two spreads contain all 26 instances from
2000--2025.

| Spread    |   Instances |   Standardized daily changes |   Kurtosis E[z^4] |   Excess above normal |   Abs(z) > 4 observations | Abs(z) > 4 rate   |
|:----------|------------:|-----------------------------:|------------------:|----------------------:|--------------------------:|:------------------|
| NG[H][J0] |          26 |                         6448 |            16.947 |                13.947 |                        46 | 0.713%            |
| CL[F][G0] |          25 |                         6200 |            13.882 |                10.882 |                        42 | 0.677%            |
| HE[J][M0] |          26 |                         6298 |             8.169 |                 5.169 |                        30 | 0.476%            |

All three kurtoses are greater than the normal benchmark of 3, so all three
spreads have heavy-tailed daily changes after controlling for differences in
mean and volatility across contract-year instances. The fourth-power statistic
is especially large for the spread with the highest reported kurtosis, meaning
that a relatively small number of extreme standardized moves has a large
effect on the estimate. The `Abs(z) > 4` counts are included as a transparent
cross-check; under normality such events would occur only about 0.006% of the
time.
