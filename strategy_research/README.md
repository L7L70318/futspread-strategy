# Training-only strategy research

This folder contains code and results used to design the strategy using only
instances whose exit date is no later than 31 December 2020. Formal holdout
backtesting and submission files live in `../assignment10/`.

- `results/seasonal_candidate_summary_train.csv`: every tested configuration.
- `results/seasonal_shortlist.csv`: final, non-duplicated shortlist (one window
  per spread, normally at most two per ticker, plus the required HW2 comparator;
  19 sub-strategies in total).
- `results/seasonal_candidate_instances_train.parquet`: auditable observations.
- `results/hw2_reference/`: retained HW2 window/path evidence for the original four
  spreads.
- `seasonal_universe.py`: the 43 economically motivated candidates.
- `seasonal_shortlist.py`: training screen and final shortlist.
- `seasonal_trade.py`: shared fixed-window trade extraction.
- `hw2_window_scan.py`: original four-spread window diagnostics.

The candidate universe is deliberately limited to 43 calendar spreads with a
clear storage, crop-cycle, livestock-cycle, refinery, driving-season, or
heating-season rationale. Metals, FX, equity indices, rates, lumber, and softs
are not searched.

Run from the workspace root with:

```bash
python -m strategy_research.seasonal_shortlist
python -m strategy_research.hw2_window_scan
```
