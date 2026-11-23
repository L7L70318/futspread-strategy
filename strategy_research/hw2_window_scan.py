"""Training-only average-P&L window scan for the four HW2 spreads."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from futspread import load_combo
from strategy_research.seasonal_trade import extract_instance_trade


WORKSPACE = Path(__file__).resolve().parents[1]
ROOT = WORKSPACE / 'futspread_data'
OUT = WORKSPACE / 'strategy_research' / 'results' / 'hw2_reference'
OUT.mkdir(parents=True, exist_ok=True)
SPREADS = {
    'NG[H][J0]': ('energy', -1),
    'ZC[U][Z0]': ('grains', -1),
    'ZW[K][N0]': ('grains', -1),
    'HE[V][Z0]': ('livestock', 1),
}
ENTRIES = [160, 140, 120, 100, 80, 60, 40, 20]
EXITS = [100, 80, 60, 40, 20, 10, 2]


def main():
    per_instance = []
    for combo, (sector, direction) in SPREADS.items():
        df = load_combo(combo, ROOT)
        for instance, g in df.groupby('instance'):
            if int(instance) > 2020:
                continue
            for entry in ENTRIES:
                for exit_ in EXITS:
                    if entry <= exit_:
                        continue
                    r = extract_instance_trade(
                        g.reset_index(drop=True), combo,
                        f'{entry}_{exit_}', entry, exit_, sector)
                    if r is None or r['exit_date'].year > 2020:
                        continue
                    r['direction'] = direction
                    r['net_1lot'] = (direction * r['gross_long_1lot']
                                     - r['roundtrip_cost_1lot'])
                    r['entry_target'] = entry
                    r['exit_target'] = exit_
                    per_instance.append(r)
    x = pd.DataFrame(per_instance)
    x.to_parquet(OUT / 'per_instance.parquet', index=False)

    rows = []
    for (combo, entry, exit_), g in x.groupby(
            ['combo', 'entry_target', 'exit_target']):
        p = g['net_1lot'].to_numpy(float)
        sd = float(np.std(p, ddof=1))
        mean = float(np.mean(p))
        rows.append({
            'combo': combo, 'entry_dte': entry, 'exit_dte': exit_,
            'n': len(p), 'mean_gross_1lot': float(
                (g['direction'] * g['gross_long_1lot']).mean()),
            'mean_cost_1lot': float(g['roundtrip_cost_1lot'].mean()),
            'mean_net_1lot': mean, 'median_net_1lot': float(np.median(p)),
            'std_net_1lot': sd, 'hit_rate': float(np.mean(p > 0)),
            't_stat': mean / (sd / np.sqrt(len(p))) if sd > 0 else np.nan,
            'mean_over_std': mean / sd if sd > 0 else np.nan,
        })
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT / 'window_summary_by_spread.csv', index=False)

    portfolio = summary.groupby(['entry_dte', 'exit_dte']).agg(
        spreads=('combo', 'size'), avg_t_stat=('t_stat', 'mean'),
        min_t_stat=('t_stat', 'min'), avg_hit_rate=('hit_rate', 'mean'),
        all_positive_mean=('mean_net_1lot', lambda s: bool((s > 0).all())),
        all_positive_median=('median_net_1lot', lambda s: bool((s > 0).all())),
        avg_mean_over_std=('mean_over_std', 'mean'),
    ).reset_index()
    portfolio = portfolio.sort_values(
        ['all_positive_mean', 'avg_t_stat'], ascending=[False, False])
    portfolio.to_csv(OUT / 'window_summary_across_spreads.csv', index=False)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, combo in zip(axes.flat, SPREADS):
        s = summary[summary['combo'] == combo]
        pivot = s.pivot(index='entry_dte', columns='exit_dte',
                        values='t_stat').sort_index(ascending=False)
        im = ax.imshow(pivot, aspect='auto', cmap='RdYlGn', vmin=-2, vmax=4)
        ax.set_xticks(range(len(pivot.columns)), pivot.columns)
        ax.set_yticks(range(len(pivot.index)), pivot.index)
        ax.set_title(combo + ' training net-P&L t-stat')
        ax.set_xlabel('exit business days before LTD')
        ax.set_ylabel('entry business days before LTD')
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                v = pivot.iloc[i, j]
                if np.isfinite(v):
                    ax.text(j, i, f'{v:.1f}', ha='center', va='center', fontsize=7)
    fig.colorbar(im, ax=axes.ravel().tolist(), shrink=.8)
    fig.savefig(OUT / 'window_tstat_heatmaps.png', dpi=180, bbox_inches='tight')

    # HW2-style average P&L path: rebase at 120 business days and evaluate a
    # hypothetical exit at every subsequent DTE, including both leg costs.
    profile_rows = []
    for combo, (sector, direction) in SPREADS.items():
        df = load_combo(combo, ROOT)
        for instance, g in df.groupby('instance'):
            if int(instance) > 2020:
                continue
            for exit_ in range(119, 1, -1):
                r = extract_instance_trade(
                    g.reset_index(drop=True), combo, 'profile_120',
                    120, exit_, sector)
                if r is None or r['exit_date'].year > 2020:
                    continue
                profile_rows.append({
                    'combo': combo, 'instance': int(instance),
                    'exit_dte': exit_,
                    'net_1lot': direction * r['gross_long_1lot']
                                - r['roundtrip_cost_1lot'],
                })
    profile_raw = pd.DataFrame(profile_rows)
    profile_raw.to_parquet(OUT / 'profile_120_per_instance.parquet', index=False)
    profile = profile_raw.groupby(['combo', 'exit_dte']).agg(
        n=('net_1lot', 'size'), mean_net=('net_1lot', 'mean'),
        median_net=('net_1lot', 'median'), std_net=('net_1lot', 'std'),
        hit_rate=('net_1lot', lambda s: (s > 0).mean())).reset_index()
    profile['se'] = profile['std_net'] / np.sqrt(profile['n'])
    profile.to_csv(OUT / 'profile_120_summary.csv', index=False)
    fig2, axes2 = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    for ax, combo in zip(axes2.flat, SPREADS):
        p = profile[profile['combo'] == combo].sort_values('exit_dte', ascending=False)
        xaxis = -p['exit_dte'].to_numpy()
        mean = p['mean_net'].to_numpy()
        se = p['se'].to_numpy()
        ax.plot(xaxis, mean, color='#2457a7', lw=1.8, label='mean net P&L')
        ax.fill_between(xaxis, mean - se, mean + se, color='#2457a7', alpha=.18)
        ax.axhline(0, color='black', lw=.7)
        ax.axvline(-60, color='#c43c39', ls='--', lw=1, label='old exit -60')
        ax.axvline(-2, color='#2a8f55', ls='--', lw=1, label='R5 exit -2')
        ax.set_title(combo)
        ax.set_ylabel('average one-lot net P&L ($)')
        ax.grid(alpha=.25)
    axes2[1, 0].set_xlabel('business days to front-leg LTD')
    axes2[1, 1].set_xlabel('business days to front-leg LTD')
    axes2[0, 0].legend(fontsize=8)
    fig2.suptitle('HW2-style average net P&L paths, entry at -120 (training only)')
    fig2.tight_layout()
    fig2.savefig(OUT / 'average_pnl_paths_entry_120.png', dpi=180,
                 bbox_inches='tight')
    print(portfolio.head(20).to_string(index=False))


if __name__ == '__main__':
    main()
