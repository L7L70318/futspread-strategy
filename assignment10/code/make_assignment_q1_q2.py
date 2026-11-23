"""Create submission-ready answers for Assignment 10 Questions 1 and 2."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


CAPITAL = 10_000_000.0
TRADING_DAYS = 252
WORKSPACE = Path(__file__).resolve().parents[2]
RESULTS = WORKSPACE / "assignment10" / "results" / "backtest"
OUT = WORKSPACE / "assignment10" / "results" / "submission"
SHORTLIST = WORKSPACE / "strategy_research" / "results" / "seasonal_shortlist.csv"


def max_drawdown(pnl: pd.Series) -> float:
    cumulative = np.r_[0.0, pnl.cumsum().to_numpy(float)] / CAPITAL
    return float(np.min(cumulative - np.maximum.accumulate(cumulative)))


def performance_row(daily: pd.DataFrame, trades: pd.DataFrame,
                    label: str, year: int | None):
    if year is None:
        d = daily.copy()
        t = trades.copy()
    else:
        d = daily[daily.date.dt.year.eq(year)].copy()
        t = trades[trades.entry_date.dt.year.eq(year)].copy()
    gross_return = float(d.gross_pnl.mean() / CAPITAL * TRADING_DAYS)
    net_return = float(d.net_pnl.mean() / CAPITAL * TRADING_DAYS)
    gross_vol = float((d.gross_pnl / CAPITAL).std(ddof=1) * np.sqrt(TRADING_DAYS))
    net_vol = float((d.net_pnl / CAPITAL).std(ddof=1) * np.sqrt(TRADING_DAYS))
    gross_total = float(d.gross_pnl.sum())
    return {
        "Period": label,
        "Gross Return": gross_return,
        "Gross Vol": gross_vol,
        "Gross Sharpe": gross_return / gross_vol if gross_vol else np.nan,
        "Gross Max DD": max_drawdown(d.gross_pnl),
        "Net Return": net_return,
        "Net Vol": net_vol,
        "Net Sharpe": net_return / net_vol if net_vol else np.nan,
        "Net Max DD": max_drawdown(d.net_pnl),
        "Trades": len(t),
        "Won": float((t.gross_pnl > 0).mean()),
        "Cost/gross": float(d.cost.sum() / gross_total) if gross_total else np.nan,
    }


def fmt_money(value):
    return f"${value:,.0f}"


def markdown_performance(table: pd.DataFrame):
    display = table.copy()
    pct_cols = ["Gross Return", "Gross Vol", "Gross Max DD", "Net Return",
                "Net Vol", "Net Max DD", "Won", "Cost/gross"]
    for col in pct_cols:
        display[col] = display[col].map(lambda x: f"{x:.2%}")
    for col in ["Gross Sharpe", "Net Sharpe"]:
        display[col] = display[col].map(lambda x: f"{x:.2f}")
    return display.to_markdown(index=False)


def main():
    daily = pd.read_csv(RESULTS / "daily_portfolio.csv", parse_dates=["date"])
    trades = pd.read_csv(
        RESULTS / "trades.csv",
        parse_dates=["decision_date", "entry_date", "exit_date"])
    shortlist = pd.read_csv(SHORTLIST)
    configs = shortlist[[
        "combo", "regime", "entry_dte", "direction_label", "selection_note"
    ]].copy().rename(columns={
        "combo": "Spread", "regime": "Entry regime",
        "entry_dte": "Entry (business days to LTD)",
        "direction_label": "Direction", "selection_note": "Selection",
    })
    configs["Direction"] = configs.Direction.map({
        "long_spread": "Long spread", "short_spread": "Short spread"})
    configs["Selection"] = configs.Selection.map({
        "strict_screen": "Screen", "required_hw2_comparator": "HW2 comparator"})
    configs["Exit (business days to LTD)"] = 2
    rows = [performance_row(daily, trades, str(year), year)
            for year in range(2021, 2026)]
    rows.append(performance_row(daily, trades, "2021–2025", None))
    performance = pd.DataFrame(rows)
    performance.to_csv(OUT / "question2_performance_table.csv", index=False)

    q1_trades = trades[trades.entry_date.dt.year.eq(2021)].copy()
    q1_trades = q1_trades[[
        "combo", "direction_label", "entry_date", "exit_date", "lots",
        "historical_n", "historical_avg_net_1lot",
    ]].rename(columns={
        "combo": "Spread", "direction_label": "Direction",
        "entry_date": "Entry", "exit_date": "Exit",
        "lots": "Lots",
        "historical_n": "Past instances",
        "historical_avg_net_1lot": "Past average net P&L (one lot)",
    })
    q1_trades["Direction"] = q1_trades.Direction.map({
        "long_spread": "Long spread", "short_spread": "Short spread"})
    q1_trades["Entry"] = q1_trades.Entry.dt.strftime("%Y-%m-%d")
    q1_trades["Exit"] = q1_trades.Exit.dt.strftime("%Y-%m-%d")
    q1_trades.to_csv(OUT / "question1b_2021_trades.csv", index=False)
    q1_display = q1_trades.copy()
    q1_display["Past average net P&L (one lot)"] = q1_display[
        "Past average net P&L (one lot)"].map(fmt_money)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(daily.date, daily.gross_pnl.cumsum(), label="Gross P&L", lw=1.8)
    ax.plot(daily.date, daily.net_pnl.cumsum(), label="Net P&L", lw=1.8)
    ax.axhline(0, color="black", lw=.7)
    ax.set_title("Cumulative P&L, 2021–2025")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative P&L ($)")
    ax.grid(alpha=.25)
    ax.legend()
    ax.ticklabel_format(axis="y", style="plain")
    fig.tight_layout()
    fig.savefig(OUT / "question2_cumulative_gross_net_pnl.png", dpi=200)
    plt.close(fig)

    answer = f"""# Assignment 10 — Questions 1 and 2

## Question 1. Strategy

### (a) Rule

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

{configs.to_markdown(index=False)}

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

### (b) Trades chosen in 2021

The historical average below is the average net P&L per one-lot spread among
same-regime instances completed before that trade's decision date.

{q1_display.to_markdown(index=False)}

## Question 2. Performance, 2021–2025

### (a) Performance table

Returns and volatility are annualized from daily, non-compounded returns using
252 trading days. Drawdown includes zero as the initial peak for each row.
Annual P&L is assigned to the calendar day on which it occurred. “Trades” and
“Won” are classified by entry year; “Won” uses positive gross whole-trade P&L.
Cost/gross uses costs and gross P&L charged in the displayed calendar period.

{markdown_performance(performance)}

### (b) Cumulative gross and net P&L

![Cumulative gross and net P&L](question2_cumulative_gross_net_pnl.png)
"""
    (OUT / "assignment_q1_q2.md").write_text(answer)
    rule = answer.split("### (a) Rule\n", 1)[1].split("### (b)", 1)[0]
    (OUT / "strategy_rule.md").write_text(
        "# Locked seasonal strategy\n\n" + rule.strip() + "\n")
    q3b_path = OUT / "assignment_question3b.md"
    if q3b_path.exists():
        combined = answer.rstrip() + "\n\n" + q3b_path.read_text().strip() + "\n"
        (OUT / "assignment_answers_q1_q2_q3b.md").write_text(combined)
    print(performance.to_string(index=False))
    print("\nWrote", OUT / "assignment_q1_q2.md")


if __name__ == "__main__":
    main()
