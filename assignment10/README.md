# Assignment 10: formal backtest and submission

This directory is separated from training research so that the locked
2021--2025 holdout and the submitted answers are easy to audit.

- `code/seasonal_backtest.py`: the formal settlement-only holdout backtest.
- `code/make_assignment_q1_q2.py`: Question 1/2 tables, prose, and chart.
- `code/question3b_heavy_tails.py`: Question 3(b) kurtosis calculation.
- `results/backtest/`: trades, daily ledger, exposures, and performance.
- `results/submission/`: submission-ready Markdown, CSV tables, and chart.
- `results/diagnostics/`: large audit files used to verify Question 3(b).

Reproduce from the workspace root in this order:

```bash
python -m assignment10.code.seasonal_backtest
python -m assignment10.code.question3b_heavy_tails
python -m assignment10.code.make_assignment_q1_q2
```

The main partial submission is
`results/submission/assignment_answers_q1_q2_q3b.md`.

Question 2(b)'s required cumulative gross/net P&L chart is
[`results/submission/question2_cumulative_gross_net_pnl.png`](results/submission/question2_cumulative_gross_net_pnl.png).
