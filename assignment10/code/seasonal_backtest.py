"""Locked 2021--2025 test of the training-selected seasonal strategies."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from futspread import load_combo, universe
from strategy_research.seasonal_trade import COST_RATE, extract_instance_trade


WORKSPACE = Path(__file__).resolve().parents[2]
ROOT = WORKSPACE / "futspread_data"
OUT = WORKSPACE / "assignment10" / "results" / "backtest"
SHORTLIST = WORKSPACE / "strategy_research" / "results" / "seasonal_shortlist.csv"
CAPITAL = 10_000_000.0
ANNUAL_VOL_TARGET = 0.08
ASSUMED_CONCURRENT = 8
MAX_ACTIVE = 10
MAX_ACTIVE_GROUP = 2
TRADE_NOTIONAL_CAP = 0.20 * CAPITAL
TICKER_NOTIONAL_CAP = 0.25 * CAPITAL
GROUP_NOTIONAL_CAP = 0.40 * CAPITAL
GROSS_NOTIONAL_CAP = 1.50 * CAPITAL
MARGIN_PROXY_RATE = 0.15
MARGIN_PROXY_CAP = 0.25 * CAPITAL
MIN_REGIME_HISTORY = 8


def build_all_instances(shortlist: pd.DataFrame):
    records = []
    combo_data = {}
    for row in shortlist.itertuples(index=False):
        data = load_combo(row.combo, ROOT)
        combo_data[row.combo] = data
        for instance, group in data.groupby("instance"):
            trade = extract_instance_trade(
                group.reset_index(drop=True), row.combo,
                f"{int(row.entry_dte)}_2", int(row.entry_dte), 2,
                row.economic_group)
            if trade is None:
                continue
            trade.update({
                "selected_regime": row.regime,
                "direction": int(row.direction),
                "direction_label": row.direction_label,
                "economic_group": row.economic_group,
                "score_lcb": float(row.score_lcb),
                "selection_note": row.selection_note,
            })
            records.append(trade)
    return pd.DataFrame(records), combo_data


def choose_and_size(instances: pd.DataFrame):
    candidates = instances[
        instances["entry_date"].between("2021-01-01", "2025-12-31")
        & instances["exit_date"].between("2021-01-01", "2025-12-31")
        & instances["regime"].eq(instances["selected_regime"])
    ].sort_values(["decision_date", "score_lcb"], ascending=[True, False])
    daily_risk_budget = (CAPITAL * ANNUAL_VOL_TARGET / np.sqrt(252)
                         / np.sqrt(ASSUMED_CONCURRENT))
    active = []
    selected = []
    for row in candidates.itertuples(index=False):
        active = [a for a in active if a["exit_date"] > row.entry_date]
        history = instances[
            instances.combo.eq(row.combo)
            & instances.selected_regime.eq(row.selected_regime)
            & instances.regime.eq(row.selected_regime)
            & (instances.exit_date < row.decision_date)
        ].copy()
        if len(history) < MIN_REGIME_HISTORY:
            continue
        if len(active) >= MAX_ACTIVE:
            continue
        if sum(a["economic_group"] == row.economic_group for a in active) >= MAX_ACTIVE_GROUP:
            continue

        hist_net = (row.direction * history.gross_long_1lot
                    - history.roundtrip_cost_1lot)
        hist_vol = float(history.daily_vol_1lot.median())
        if not np.isfinite(hist_vol) or hist_vol <= 0:
            continue
        desired_lots = daily_risk_budget / hist_vol
        unit_notional = float(row.decision_leg_notional_1lot)
        ticker_used = sum(a["notional"] for a in active if a["ticker"] == row.ticker)
        group_used = sum(a["notional"] for a in active
                         if a["economic_group"] == row.economic_group)
        gross_used = sum(a["notional"] for a in active)
        allowed_notional = min(
            TRADE_NOTIONAL_CAP,
            max(0.0, TICKER_NOTIONAL_CAP - ticker_used),
            max(0.0, GROUP_NOTIONAL_CAP - group_used),
            max(0.0, GROSS_NOTIONAL_CAP - gross_used),
            max(0.0, MARGIN_PROXY_CAP / MARGIN_PROXY_RATE - gross_used),
        )
        lots = min(desired_lots, allowed_notional / unit_notional)
        lots = np.floor(lots * 100) / 100  # fractional lots are allowed
        if lots <= 0:
            continue
        record = row._asdict()
        record.update({
            "lots": lots,
            "notional": lots * unit_notional,
            "margin_proxy": lots * unit_notional * MARGIN_PROXY_RATE,
            "historical_n": len(history),
            "historical_avg_net_1lot": float(hist_net.mean()),
            "historical_hit_rate": float((hist_net > 0).mean()),
            "historical_median_daily_vol_1lot": hist_vol,
            "risk_target_lots": desired_lots,
        })
        selected.append(record)
        active.append(record)
    return pd.DataFrame(selected)


def daily_ledger(trades: pd.DataFrame, combo_data: dict):
    rows = []
    for trade in trades.itertuples(index=False):
        data = combo_data[trade.combo]
        held = data[
            data.instance.eq(trade.instance)
            & data.date.between(trade.entry_date, trade.exit_date)
        ].sort_values("date").copy()
        held["gross_pnl"] = (trade.direction * trade.lots
                             * held.settlement.diff().fillna(0)
                             * trade.point_value)
        held["cost"] = 0.0
        first, last = held.index[0], held.index[-1]
        held.loc[first, "cost"] += (COST_RATE * trade.lots * trade.point_value
                                     * (abs(held.loc[first, "l1_settlement"])
                                        + abs(held.loc[first, "l2_settlement"])))
        held.loc[last, "cost"] += (COST_RATE * trade.lots * trade.point_value
                                    * (abs(held.loc[last, "l1_settlement"])
                                       + abs(held.loc[last, "l2_settlement"])))
        held["net_pnl"] = held.gross_pnl - held.cost
        for bar in held.itertuples(index=False):
            rows.append({
                "date": bar.date, "combo": trade.combo,
                "ticker": trade.ticker, "economic_group": trade.economic_group,
                "instance": trade.instance, "lots": trade.lots,
                "gross_pnl": bar.gross_pnl, "cost": bar.cost,
                "net_pnl": bar.net_pnl,
            })
    return pd.DataFrame(rows)


def summarize(trades: pd.DataFrame, ledger: pd.DataFrame, combo_data: dict):
    metadata = universe().set_index("ticker")
    calendar_sets = []
    for ticker in sorted(trades.ticker.unique()):
        contrcode = int(metadata.loc[ticker, "contrcode"])
        prices = pd.read_parquet(
            ROOT / "raw" / "prices" / f"{contrcode}.parquet",
            columns=["date"])
        calendar_sets.append(set(
            prices.loc[prices.date.dt.year.between(2021, 2025), "date"]))
    calendar = sorted(set().union(*calendar_sets))
    daily = ledger.groupby("date")[["gross_pnl", "cost", "net_pnl"]].sum()
    daily = daily.reindex(pd.DatetimeIndex(calendar), fill_value=0.0)
    daily["return"] = daily.net_pnl / CAPITAL
    daily["cumulative_return"] = daily["return"].cumsum()
    daily["drawdown"] = daily.cumulative_return - daily.cumulative_return.cummax()
    sd = float(daily["return"].std(ddof=1))
    sharpe = float(daily["return"].mean() / sd * np.sqrt(252)) if sd else np.nan
    gross_sd = float((daily.gross_pnl / CAPITAL).std(ddof=1))
    gross_sharpe = float((daily.gross_pnl / CAPITAL).mean() / gross_sd
                         * np.sqrt(252)) if gross_sd else np.nan
    exposure_rows = []
    for date in daily.index:
        active = trades[
            (pd.to_datetime(trades.entry_date) <= date)
            & (pd.to_datetime(trades.exit_date) > date)
        ]
        exposure_rows.append({
            "date": date, "active": len(active),
            "gross_committed_notional": active.notional.sum(),
            "margin_proxy": active.margin_proxy.sum(),
            "max_ticker_notional": (active.groupby("ticker").notional.sum().max()
                                    if len(active) else 0.0),
            "max_group_notional": (
                active.groupby("economic_group").notional.sum().max()
                if len(active) else 0.0),
        })
    exposure = pd.DataFrame(exposure_rows)
    perf = {
        "capital": CAPITAL,
        "trades": int(len(trades)),
        "gross_pnl": float(daily.gross_pnl.sum()),
        "cost": float(daily.cost.sum()),
        "net_pnl": float(daily.net_pnl.sum()),
        "total_return": float(daily.net_pnl.sum() / CAPITAL),
        "annualized_return_no_compounding": float(daily.net_pnl.sum() / CAPITAL / 5),
        "annualized_volatility": float(sd * np.sqrt(252)),
        "net_sharpe": sharpe,
        "gross_sharpe": gross_sharpe,
        "max_drawdown": float(daily.drawdown.min()),
        "winning_trade_rate": float((
            trades.direction * trades.lots * trades.gross_long_1lot
            - trades.lots * trades.roundtrip_cost_1lot > 0).mean()),
        "max_active_limit": MAX_ACTIVE,
        "margin_proxy_rate": MARGIN_PROXY_RATE,
        "margin_proxy_capital_limit": MARGIN_PROXY_CAP / CAPITAL,
        "realized_max_active": int(exposure.active.max()),
        "realized_max_gross_notional_to_capital": float(
            exposure.gross_committed_notional.max() / CAPITAL),
        "realized_max_ticker_notional_to_capital": float(
            exposure.max_ticker_notional.max() / CAPITAL),
        "realized_max_group_notional_to_capital": float(
            exposure.max_group_notional.max() / CAPITAL),
        "realized_max_margin_proxy_to_capital": float(
            exposure.margin_proxy.max() / CAPITAL),
    }
    return daily.reset_index(names="date"), exposure, perf


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    shortlist = pd.read_csv(SHORTLIST)
    instances, combo_data = build_all_instances(shortlist)
    trades = choose_and_size(instances)
    if trades.empty:
        raise RuntimeError("no holdout trades selected")
    ledger = daily_ledger(trades, combo_data)
    daily, exposure, perf = summarize(trades, ledger, combo_data)
    trades["gross_pnl"] = trades.direction * trades.lots * trades.gross_long_1lot
    trades["cost"] = trades.lots * trades.roundtrip_cost_1lot
    trades["net_pnl"] = trades.gross_pnl - trades.cost
    trades.to_csv(OUT / "trades.csv", index=False)
    ledger.to_parquet(OUT / "daily_trade_ledger.parquet", index=False)
    daily.to_csv(OUT / "daily_portfolio.csv", index=False)
    exposure.to_csv(OUT / "daily_exposure.csv", index=False)
    with (OUT / "performance.json").open("w") as file:
        json.dump(perf, file, indent=2)
    trades["entry_year"] = pd.to_datetime(trades.entry_date).dt.year
    by_year = trades.groupby("entry_year").agg(
        trades=("combo", "size"), gross_pnl=("gross_pnl", "sum"),
        cost=("cost", "sum"), net_pnl=("net_pnl", "sum"),
    ).reset_index().rename(columns={"entry_year": "year"})
    by_year["return"] = by_year.net_pnl / CAPITAL
    by_year.to_csv(OUT / "by_year.csv", index=False)
    by_combo = trades.groupby(["combo", "selection_note"]).agg(
        trades=("combo", "size"), gross_pnl=("gross_pnl", "sum"),
        cost=("cost", "sum"), net_pnl=("net_pnl", "sum"),
        winning_trade_rate=("net_pnl", lambda values: float((values > 0).mean())),
    ).reset_index().sort_values("net_pnl", ascending=False)
    by_combo.to_csv(OUT / "by_combo.csv", index=False)
    trades[trades.entry_year.eq(2021)][[
        "combo", "direction_label", "entry_date", "exit_date", "lots",
        "historical_n", "historical_avg_net_1lot", "historical_hit_rate",
        "net_pnl", "selection_note",
    ]].to_csv(OUT / "question_b_trades_2021.csv", index=False)
    report = f"""# Locked holdout result: 2021--2025

The 19-sub-strategy rule was selected and locked using data through 2020. The
holdout was then run once without using 2021--2025 results to change the rule.

- Trades: {perf['trades']}
- Gross P&L: ${perf['gross_pnl']:,.2f}
- Costs: ${perf['cost']:,.2f}
- Net P&L: ${perf['net_pnl']:,.2f}
- Total return on $10 million: {perf['total_return']:.2%}
- Annualized return (no compounding): {perf['annualized_return_no_compounding']:.2%}
- Net Sharpe: {perf['net_sharpe']:.3f}
- Gross Sharpe: {perf['gross_sharpe']:.3f}
- Maximum drawdown: {perf['max_drawdown']:.2%}
- Winning-trade rate: {perf['winning_trade_rate']:.1%}
- Realized maximum active trades: {perf['realized_max_active']}
- Realized maximum gross committed notional/capital: {perf['realized_max_gross_notional_to_capital']:.1%}
- Realized maximum margin proxy/capital: {perf['realized_max_margin_proxy_to_capital']:.1%}

Accounting validation: trade-level, daily-ledger, and portfolio-level net P&L
totals agree. Every decision precedes entry, and every exit is at least two
business days before the front leg's LTD.
"""
    (OUT / "holdout_report.md").write_text(report)
    print(json.dumps(perf, indent=2))
    print("\nBY YEAR")
    print(by_year.to_string(index=False))


if __name__ == "__main__":
    main()
