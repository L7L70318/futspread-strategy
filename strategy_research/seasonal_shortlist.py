"""Training-only shortlist of economically motivated seasonal sub-strategies."""
from pathlib import Path

import numpy as np
import pandas as pd

from futspread import load_combo
from strategy_research.seasonal_universe import SEASONAL_SPREADS
from strategy_research.seasonal_trade import extract_instance_trade


WORKSPACE = Path(__file__).resolve().parents[1]
ROOT = WORKSPACE / 'futspread_data'
OUT = WORKSPACE / 'strategy_research' / 'results'
OUT.mkdir(exist_ok=True)
ENTRIES = [120, 60, 30]
EXITS = [10, 2]                 # 10 is a robustness neighbour; trade exits at 2.
MIN_ALL = 12
MIN_REGIME = 8
MAX_SUBSTRATEGIES = 20
REQUIRED_HW2 = {
    # Retained for direct comparability with Assignment 2.  This configuration
    # is economically positive and cost-robust, but misses the strict t >= 1.5
    # screen, so it is labelled rather than silently treated as a pass.
    'HE[V][Z0]': ('backwardation', 30),
}


def metrics(net: np.ndarray):
    n = len(net)
    sd = float(np.std(net, ddof=1))
    mean = float(np.mean(net))
    se = sd / np.sqrt(n) if n and sd > 0 else np.nan
    split = n // 2
    return {
        'n': n, 'mean': mean, 'median': float(np.median(net)),
        'std': sd, 'se': se, 'hit': float(np.mean(net > 0)),
        't': mean / se if se > 0 else np.nan,
        'early_mean': float(np.mean(net[:split])) if split else np.nan,
        'late_mean': float(np.mean(net[split:])) if split else np.nan,
        'leave_best_mean': float((net.sum() - net.max()) / (n - 1)) if n > 1 else np.nan,
    }


def build_records():
    rows = []
    for combo, (group, reason) in SEASONAL_SPREADS.items():
        df = load_combo(combo, ROOT)
        for instance, g in df.groupby('instance'):
            if int(instance) > 2020:
                continue
            for entry in ENTRIES:
                for exit_ in EXITS:
                    r = extract_instance_trade(
                        g.reset_index(drop=True), combo,
                        f'{entry}_{exit_}', entry, exit_, group)
                    if r is None or r['exit_date'].year > 2020:
                        continue
                    r['economic_group'] = group
                    r['economic_reason'] = reason
                    r['entry_target'] = entry
                    r['exit_target'] = exit_
                    rows.append(r)
    x = pd.DataFrame(rows)
    x.to_parquet(OUT / 'seasonal_candidate_instances_train.parquet', index=False)
    return x


def evaluate(x: pd.DataFrame):
    all_counts = (x[x.exit_target == 2]
                  .groupby(['combo', 'entry_target']).instance.nunique())
    rows = []
    for (combo, entry, regime), g in x.groupby(
            ['combo', 'entry_target', 'regime']):
        if regime == 'flat':
            continue
        p2 = g[g.exit_target == 2].sort_values('exit_date')
        p10 = g[g.exit_target == 10].sort_values('exit_date')
        common = sorted(set(p2.instance) & set(p10.instance))
        p2 = p2[p2.instance.isin(common)]
        p10 = p10[p10.instance.isin(common)]
        n_all = int(all_counts.get((combo, entry), 0))
        if len(common) == 0:
            continue
        direction = 1 if p2.gross_long_1lot.mean() >= 0 else -1
        net2 = (direction * p2.gross_long_1lot
                - p2.roundtrip_cost_1lot).to_numpy(float)
        net10 = (direction * p10.gross_long_1lot
                 - p10.roundtrip_cost_1lot).to_numpy(float)
        m2, m10 = metrics(net2), metrics(net10)
        gross2 = (direction * p2.gross_long_1lot).to_numpy(float)
        cost2 = p2.roundtrip_cost_1lot.to_numpy(float)
        coverage = float(gross2.mean() / cost2.mean())
        double_cost_mean = float(np.mean(gross2 - 2 * cost2))
        direction10 = 1 if p10.gross_long_1lot.mean() >= 0 else -1
        passed = bool(
            n_all >= MIN_ALL and m2['n'] >= MIN_REGIME
            and direction10 == direction
            and m2['mean'] > 0 and m2['median'] > 0
            and m10['mean'] > 0 and m10['median'] > 0
            and m2['hit'] >= .60 and m2['t'] >= 1.5
            and m2['early_mean'] > 0 and m2['late_mean'] > 0
            and m2['leave_best_mean'] > 0
            and double_cost_mean > 0 and coverage >= 3.0
        )
        score = ((m2['mean'] - m2['se']) / m2['std']
                 if m2['std'] > 0 else np.nan)
        group = p2.economic_group.iloc[0]
        rows.append({
            'combo': combo, 'ticker': p2.ticker.iloc[0],
            'economic_group': group,
            'economic_reason': p2.economic_reason.iloc[0],
            'regime': regime, 'entry_dte': entry, 'exit_dte': 2,
            'direction': direction,
            'direction_label': 'long_spread' if direction > 0 else 'short_spread',
            'n_all': n_all, 'n_regime': m2['n'],
            'mean_net_2': m2['mean'], 'median_net_2': m2['median'],
            'hit_2': m2['hit'], 't_2': m2['t'],
            'mean_net_10': m10['mean'], 'median_net_10': m10['median'],
            'early_mean_2': m2['early_mean'], 'late_mean_2': m2['late_mean'],
            'leave_best_mean_2': m2['leave_best_mean'],
            'double_cost_mean_2': double_cost_mean,
            'cost_coverage_2': coverage, 'score_lcb': score,
            'passes': passed,
        })
    result = pd.DataFrame(rows).sort_values(
        ['passes', 'score_lcb'], ascending=[False, False])
    result.to_csv(OUT / 'seasonal_candidate_summary_train.csv', index=False)
    return result


def shortlist(result: pd.DataFrame):
    selected = []
    ticker_count = {}
    group_count = {}
    used_combos = set()
    for r in result[result.passes].itertuples(index=False):
        if r.combo in used_combos:
            continue
        if ticker_count.get(r.ticker, 0) >= 2:
            continue
        if group_count.get(r.economic_group, 0) >= 6:
            continue
        row = r._asdict()
        row['selection_note'] = 'strict_screen'
        selected.append(row)
        used_combos.add(r.combo)
        ticker_count[r.ticker] = ticker_count.get(r.ticker, 0) + 1
        group_count[r.economic_group] = group_count.get(r.economic_group, 0) + 1
        if len(selected) == MAX_SUBSTRATEGIES:
            break
    for combo, (regime, entry) in REQUIRED_HW2.items():
        if any(row['combo'] == combo for row in selected):
            continue
        forced = result[
            result.combo.eq(combo) & result.regime.eq(regime)
            & result.entry_dte.eq(entry)
        ]
        if forced.empty:
            raise RuntimeError(f'missing required HW2 configuration: {combo}')
        row = forced.iloc[0].to_dict()
        row['selection_note'] = 'required_hw2_comparator'
        selected.append(row)
    if len(selected) > MAX_SUBSTRATEGIES:
        raise RuntimeError('required HW2 additions exceed sub-strategy cap')
    out = pd.DataFrame(selected)
    out.to_csv(OUT / 'seasonal_shortlist.csv', index=False)
    return out


if __name__ == '__main__':
    records = build_records()
    result = evaluate(records)
    chosen = shortlist(result)
    print(f'{len(SEASONAL_SPREADS)} whitelist spreads; '
          f'{int(result.passes.sum())} configurations pass; '
          f'{len(chosen)} shortlisted')
    print(chosen[[
        'combo', 'economic_group', 'regime', 'entry_dte',
        'direction_label', 'n_regime', 'mean_net_2', 'hit_2', 't_2',
        'score_lcb']].to_string(index=False))
