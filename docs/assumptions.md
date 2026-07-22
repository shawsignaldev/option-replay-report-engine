# Assumptions

## Contract model

The engine assumes standard equity option contract multiplier behavior: one listed contract controls 100 shares. Fees are modeled as a per-contract, per-leg cost, so round-trip fees equal entry fees plus exit fees.

## Fill model

Inputs must provide explicit entry and exit fills. The engine does not infer hidden liquidity, queue position, or broker execution quality. Slippage is measured against the midpoint snapshots provided by the caller.

## Volatility model

Volatility contribution is a simplified sensitivity estimate based on implied-volatility change, absolute delta, and contract count. It is useful for attribution direction and rough sizing, not for production-grade Greeks decomposition.

## Evidence boundary

This repository is public research infrastructure. It is not a broker, exchange simulator, regulatory system, or live trading agent.
