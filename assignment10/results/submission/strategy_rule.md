# Locked seasonal strategy

#### Part 1 — Trading theory and spread selection

Calendar spreads isolate seasonal relative-value effects while reducing the
outright price exposure common to both months. Before examining 2021–2025, I
chose 43 same-series candidates tied to natural-gas storage; energy refining,
heating and driving seasons; grain/soy crop transitions; or livestock/dairy
production cycles. Both legs are liquid months, year offset is at most one,
and the five R1 exclusions are omitted.

Using only trades exited by 31 December 2020, I tested entries 30, 60 and 120
business days before front LTD and exit at LTD minus two, separately in
contango and backwardation. Direction is the sign of training average gross
P&L. The screen required 12 total/eight same-regime observations, positive mean
and median net P&L, 60% hit rate, 1.5 t-statistic, early/late and neighboring-
exit stability, and positive mean with doubled costs and without the best
trade. `HE[V][Z0]` is a labelled pre-specified HW2 comparator (training t-stat
1.17). The 19 locked rules are:

| Spread    | Entry regime   |   Entry (business days to LTD) | Direction    | Selection      |   Exit (business days to LTD) |
|:----------|:---------------|-------------------------------:|:-------------|:---------------|------------------------------:|
| KE[H][N0] | backwardation  |                            120 | Short spread | Screen         |                             2 |
| ZC[U][Z0] | contango       |                            120 | Short spread | Screen         |                             2 |
| GF[Q][X0] | contango       |                             60 | Long spread  | Screen         |                             2 |
| KE[K][N0] | backwardation  |                            120 | Short spread | Screen         |                             2 |
| RB[J][M0] | contango       |                             30 | Long spread  | Screen         |                             2 |
| ZL[N][Z0] | contango       |                            120 | Short spread | Screen         |                             2 |
| HE[N][Q0] | backwardation  |                             30 | Long spread  | Screen         |                             2 |
| HO[U][F0] | contango       |                             30 | Long spread  | Screen         |                             2 |
| GF[U][X0] | backwardation  |                             30 | Long spread  | Screen         |                             2 |
| CL[H][M0] | contango       |                            120 | Short spread | Screen         |                             2 |
| HE[M][N0] | backwardation  |                            120 | Short spread | Screen         |                             2 |
| NG[J][X0] | contango       |                             60 | Short spread | Screen         |                             2 |
| ZW[K][N0] | contango       |                             60 | Short spread | Screen         |                             2 |
| NG[H][J0] | backwardation  |                            120 | Short spread | Screen         |                             2 |
| G[V][H0]  | contango       |                            120 | Long spread  | Screen         |                             2 |
| LE[M][V0] | contango       |                             30 | Long spread  | Screen         |                             2 |
| HO[V][H0] | contango       |                             60 | Long spread  | Screen         |                             2 |
| ZC[N][Z0] | contango       |                            120 | Short spread | Screen         |                             2 |
| HE[V][Z0] | backwardation  |                             30 | Long spread  | HW2 comparator |                             2 |

#### Part 2 — Trade implementation, position size, and solvency controls

On the settlement immediately before entry, I recompute business days to LTD
from `ltd` and trade only when the observed curve regime matches the table.
Entry is the next settlement; direction, lots and the LTD-minus-two exit date
are fixed, with no stops, early exits, compounding or resizing. Calculations use
only same-spread/same-regime instances exited before the decision. Fills use
settlements; each leg costs 2.5 bp of absolute notional at entry and exit.

Let `sigma` be the median daily dollar P&L volatility of one lot across those
completed instances. The risk size is
`q_risk = ($10m × 8% / sqrt(252) / sqrt(8)) / sigma`, so one new trade receives
about $17,817 of daily volatility before caps. At decision prices, one spread
lot has two-leg notional `n = P × (abs(S1) + abs(S2))`. Final lots equal the
minimum of `q_risk` and every remaining cap, rounded down to 0.01 lot. Caps are
20% of capital per trade, 25% per ticker, 40% per economic group and 150% total
gross, with at most ten trades and two per group. Simultaneous signals use the
higher training score first. I conservatively proxy margin as 15% of gross
notional and cap it at 25% of capital. The limits cannot eliminate gap risk,
but prevent reliance on unlimited leverage or unquantified margin.
