# Option Replay Report Engine

Deterministic option trade replay reports for short-dated options research.

This repository converts option entry and exit snapshots into an audit-friendly report that separates contract PnL, fees, liquidity cost, theta drag, volatility contribution, realized underlying move, reward-to-risk, quality score, and promotion verdict.

## Why this exists

Short-dated option research can look profitable when the backtest ignores spread, fill location, theta, volatility change, and contract selection. This engine gives each replay a clear attribution layer so a strategy can be reviewed before it is promoted into a larger research system.

## Implemented capabilities

- Typed option snapshots and trade inputs.
- Long call and long put replay support.
- Round-trip contract PnL and fee accounting.
- Slippage and liquidity cost attribution.
- Theta drag and volatility contribution estimates.
- Spread cost in basis points.
- Reward-to-risk calculation from target and stop.
- Evidence-gated quality score.
- Promote, Watchlist, or Reject verdict.
- Markdown report rendering for recruiter and research review.

## Example

```python
from option_replay_report_engine import ReplayInputs, explain_replay, render_markdown_report

replay = explain_replay(
    ReplayInputs.sample(symbol="MU", side="long_call", contracts=1)
)

print(render_markdown_report(replay))
```

## Research posture

The engine is intentionally deterministic and public-data friendly. It does not claim live brokerage fills, exchange certification, or complete historical options-chain coverage. Its purpose is to make option replay claims inspectable, repeatable, and honest before they feed a larger 0DTE research operating system.

## Verification

```powershell
python -m pytest -q -p no:cacheprovider
```

Expected result:

```text
3 passed
```

## Portfolio role signal

This project supports quant developer, options research, trading systems, and AI-governed research roles by showing that strategy results are not treated as one number. Each replay exposes the drivers behind the result and gives a documented reason to promote, watchlist, or reject the setup.
