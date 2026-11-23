# Seasonal Futures-Spread Strategy

Rule-based calendar-spread research and an out-of-sample backtest for Columbia
IEOR E4576. The strategy was selected using data through 2020 and then run once
on the locked 2021–2025 holdout.

## Results

- 19 economically motivated spread/regime sub-strategies
- 38 holdout trades
- $1,002,586 net P&L on $10 million capital
- 2.01% annualized non-compounded net return
- 1.09 net Sharpe ratio after all prescribed costs
- −2.89% maximum drawdown

The main write-up is
[`assignment10/results/submission/assignment_answers_q1_q2_q3b.md`](assignment10/results/submission/assignment_answers_q1_q2_q3b.md).

## Repository layout

- `futspread/`: course package plus explicit `POINT_VALUE` contract metadata.
- `strategy_research/`: training-only economic universe and shortlist research.
- `assignment10/code/`: formal holdout and assignment-generation scripts.
- `assignment10/results/backtest/`: CSV/JSON audit outputs from the locked run.
- `assignment10/results/submission/`: submission-ready prose, tables, and chart.

## Data and reproduction

WRDS data and generated Parquet files are intentionally excluded. After
installing the dependencies, download/build data into `futspread_data/` at the
repository root:

```bash
python -m pip install -r requirements.txt
FUTSPREAD_ROOT="$PWD/futspread_data" python -m futspread download --username YOUR_WRDS_USERNAME
```

Build the 43 candidates listed in `strategy_research/seasonal_universe.py`, then
run the workflow from the repository root:

```bash
python -m strategy_research.seasonal_shortlist
python -m assignment10.code.seasonal_backtest
python -m assignment10.code.question3b_heavy_tails
python -m assignment10.code.make_assignment_q1_q2
```

Further details are in
[`strategy_research/README.md`](strategy_research/README.md) and
[`assignment10/README.md`](assignment10/README.md).
