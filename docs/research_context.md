# Research Context

The option replay report engine belongs to the options microstructure and 0DTE research flagship.

The core research question is simple: when a short-dated option trade made money or lost money, what actually drove the result? A useful replay should separate directional edge, fill quality, spread cost, time decay, volatility movement, and reward-to-risk instead of compressing everything into raw PnL.

## Review checklist

- Was the contract liquid enough to trade?
- Did the underlying move in the expected direction?
- Did the spread consume too much of the edge?
- Did theta drag matter during the holding window?
- Did implied volatility help or hurt?
- Was reward-to-risk strong enough before entry?
- Should the setup be promoted, watchlisted, or rejected?

## How it connects to future systems

This package can consume snapshots from a synthetic chain generator, historical option data, or paper-trading logs. Its Markdown reports can feed a research ledger, dashboard, or agentic strategy-review workflow.
