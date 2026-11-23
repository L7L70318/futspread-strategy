"""Small, assignment-specific helpers for seasonal spread research."""
from __future__ import annotations

import numpy as np
import pandas as pd

from futspread import POINT_VALUE


COST_RATE = 2.5e-4


def _business_dte(dates: pd.Series, ltd: pd.Timestamp) -> np.ndarray:
    dates_np = dates.to_numpy(dtype="datetime64[D]")
    end = np.datetime64(pd.Timestamp(ltd).date(), "D")
    return np.busday_count(dates_np, end)


def _row_at_or_before_target_dte(g: pd.DataFrame, target: int):
    eligible = g[g["days_to_ltd"] >= target]
    if eligible.empty:
        return None
    return eligible.sort_values(["days_to_ltd", "date"]).iloc[0]


def extract_instance_trade(g: pd.DataFrame, combo: str, template: str,
                           entry_dte: int, exit_dte: int,
                           sector: str) -> dict | None:
    """Turn one annual combo instance into one fixed-window one-lot trade."""
    g = g.sort_values("date").copy()
    ltd = pd.Timestamp(g["ltd"].iloc[0])
    g["days_to_ltd"] = _business_dte(g["date"], ltd)
    entry = _row_at_or_before_target_dte(g, entry_dte)
    exit_ = _row_at_or_before_target_dte(g, exit_dte)
    if entry is None or exit_ is None or entry["date"] >= exit_["date"]:
        return None
    entry_idx = int(g.index.get_loc(entry.name))
    if entry_idx == 0:
        return None
    decision = g.iloc[entry_idx - 1]
    decision_spread = float(decision["l1_settlement"] - decision["l2_settlement"])
    regime = ("backwardation" if decision_spread > 0 else
              "contango" if decision_spread < 0 else "flat")

    ticker = str(g["ticker"].iloc[0])
    point = float(POINT_VALUE[ticker])
    entry_spread = float(entry["l1_settlement"] - entry["l2_settlement"])
    exit_spread = float(exit_["l1_settlement"] - exit_["l2_settlement"])
    gross_long = (exit_spread - entry_spread) * point
    cost = COST_RATE * point * (
        abs(float(entry["l1_settlement"])) + abs(float(entry["l2_settlement"]))
        + abs(float(exit_["l1_settlement"])) + abs(float(exit_["l2_settlement"])))

    held = g[(g["date"] >= entry["date"]) & (g["date"] <= exit_["date"])]
    one_lot_daily = held["settlement"].diff().dropna() * point
    if len(one_lot_daily) < 2:
        return None
    daily_vol = float(one_lot_daily.std(ddof=1))
    if not np.isfinite(daily_vol) or daily_vol <= 0:
        return None

    return {
        "combo": combo, "ticker": ticker, "sector": sector,
        "template": template, "instance": int(g["instance"].iloc[0]),
        "decision_date": pd.Timestamp(decision["date"]),
        "entry_date": pd.Timestamp(entry["date"]),
        "exit_date": pd.Timestamp(exit_["date"]), "ltd": ltd,
        "entry_dte": int(entry["days_to_ltd"]),
        "exit_dte": int(exit_["days_to_ltd"]),
        "decision_spread": decision_spread, "entry_spread": entry_spread,
        "exit_spread": exit_spread, "regime": regime,
        "gross_long_1lot": gross_long, "roundtrip_cost_1lot": cost,
        "daily_vol_1lot": daily_vol,
        "decision_leg_notional_1lot": point * (
            abs(float(decision["l1_settlement"]))
            + abs(float(decision["l2_settlement"]))),
        "entry_leg_notional_1lot": point * (
            abs(float(entry["l1_settlement"]))
            + abs(float(entry["l2_settlement"]))),
        "point_value": point,
    }
