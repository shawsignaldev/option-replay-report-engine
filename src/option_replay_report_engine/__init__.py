from __future__ import annotations

from dataclasses import dataclass


VALID_SIDES = {"long_call", "long_put"}


@dataclass(frozen=True)
class OptionSnapshot:
    underlying_price: float
    option_mid: float
    option_bid: float
    option_ask: float
    implied_volatility: float
    delta: float
    theta: float
    timestamp: str

    @property
    def spread(self) -> float:
        return max(0.0, self.option_ask - self.option_bid)


@dataclass(frozen=True)
class OptionTrade:
    side: str
    contracts: int
    entry_fill: float
    exit_fill: float
    fees_per_contract: float = 0.65

    def __post_init__(self) -> None:
        if self.side not in VALID_SIDES:
            raise ValueError(f"side must be one of {sorted(VALID_SIDES)}")
        if self.contracts <= 0:
            raise ValueError("contracts must be positive")


@dataclass(frozen=True)
class ReplayInputs:
    symbol: str
    strategy_name: str
    entry: OptionSnapshot
    exit: OptionSnapshot
    trade: OptionTrade
    signal_edge_bps: float
    expected_move: float
    stop_loss: float
    target: float

    @classmethod
    def sample(cls, symbol: str = "SPY", side: str = "long_call", contracts: int = 1) -> "ReplayInputs":
        delta = 0.52 if side == "long_call" else -0.48
        return cls(
            symbol=symbol,
            strategy_name="First Hour Momentum Replay",
            entry=OptionSnapshot(
                underlying_price=100.0,
                option_mid=2.00,
                option_bid=1.95,
                option_ask=2.05,
                implied_volatility=0.45,
                delta=delta,
                theta=-0.08,
                timestamp="2026-07-21T09:35:00-04:00",
            ),
            exit=OptionSnapshot(
                underlying_price=101.4,
                option_mid=2.72,
                option_bid=2.66,
                option_ask=2.78,
                implied_volatility=0.49,
                delta=delta + (0.04 if side == "long_call" else -0.04),
                theta=-0.07,
                timestamp="2026-07-21T10:10:00-04:00",
            ),
            trade=OptionTrade(
                side=side,
                contracts=contracts,
                entry_fill=2.05,
                exit_fill=2.66,
                fees_per_contract=0.65,
            ),
            signal_edge_bps=35.0,
            expected_move=1.2,
            stop_loss=1.45,
            target=3.1,
        )


@dataclass(frozen=True)
class ReplayReport:
    symbol: str
    strategy_name: str
    side: str
    contracts: int
    contract_pnl: float
    net_pnl: float
    edge_component: float
    slippage_component: float
    theta_component: float
    volatility_component: float
    spread_cost_bps: float
    realized_underlying_move: float
    reward_to_risk: float
    quality_score: float
    verdict: str
    primary_failure: str
    evidence_boundary: str


def explain_replay(inputs: ReplayInputs) -> ReplayReport:
    entry = inputs.entry
    exit_ = inputs.exit
    trade = inputs.trade
    multiplier = 100 * trade.contracts

    contract_pnl = (trade.exit_fill - trade.entry_fill) * multiplier
    fees = trade.fees_per_contract * trade.contracts * 2
    net_pnl = contract_pnl - fees

    direction = 1 if trade.side == "long_call" else -1
    realized_underlying_move = (exit_.underlying_price - entry.underlying_price) * direction
    delta_dollars = realized_underlying_move * abs(entry.delta) * multiplier
    edge_component = delta_dollars * max(0.2, inputs.signal_edge_bps / 35.0)

    entry_slippage = trade.entry_fill - entry.option_mid
    exit_slippage = exit_.option_mid - trade.exit_fill
    slippage_component = -(entry_slippage + exit_slippage) * multiplier

    theta_component = ((entry.theta + exit_.theta) / 2.0) * trade.contracts
    volatility_component = (exit_.implied_volatility - entry.implied_volatility) * abs(entry.delta) * 250 * trade.contracts

    spread_cost_bps = _spread_cost_bps(entry, exit_)
    reward_to_risk = _reward_to_risk(inputs)
    quality_score = _quality_score(
        net_pnl=net_pnl,
        signal_edge_bps=inputs.signal_edge_bps,
        spread_cost_bps=spread_cost_bps,
        reward_to_risk=reward_to_risk,
        realized_underlying_move=realized_underlying_move,
    )
    verdict = _verdict(quality_score)
    primary_failure = _primary_failure(net_pnl, spread_cost_bps, realized_underlying_move, inputs.signal_edge_bps)

    return ReplayReport(
        symbol=inputs.symbol.upper(),
        strategy_name=inputs.strategy_name,
        side=trade.side,
        contracts=trade.contracts,
        contract_pnl=round(contract_pnl, 2),
        net_pnl=round(net_pnl, 2),
        edge_component=round(edge_component, 2),
        slippage_component=round(slippage_component, 2),
        theta_component=round(theta_component, 2),
        volatility_component=round(volatility_component, 2),
        spread_cost_bps=round(spread_cost_bps, 2),
        realized_underlying_move=round(realized_underlying_move, 2),
        reward_to_risk=round(reward_to_risk, 2),
        quality_score=round(quality_score, 2),
        verdict=verdict,
        primary_failure=primary_failure,
        evidence_boundary=(
            "Replay uses provided option snapshots and deterministic attribution. "
            "It does not claim broker fills, exchange certification, or complete historical chain coverage."
        ),
    )


def render_markdown_report(report: ReplayReport) -> str:
    lines = [
        f"# Option Replay Report: {report.symbol}",
        "",
        f"Strategy: {report.strategy_name}",
        f"Side: {report.side.replace('_', ' ')}",
        f"Contracts: {report.contracts}",
        f"Verdict: {report.verdict}",
        "",
        "## PnL Attribution",
        "",
        f"- Contract PnL: ${report.contract_pnl:,.2f}",
        f"- Net PnL: ${report.net_pnl:,.2f}",
        f"- Signal edge estimate: ${report.edge_component:,.2f}",
        f"- Liquidity cost: ${abs(report.slippage_component):,.2f}",
        f"- Theta drag: ${abs(report.theta_component):,.2f}",
        f"- Volatility contribution: ${report.volatility_component:,.2f}",
        "",
        "## Quality Checks",
        "",
        f"- Spread cost: {report.spread_cost_bps:,.2f} bps",
        f"- Realized underlying move: {report.realized_underlying_move:,.2f}",
        f"- Reward to risk: {report.reward_to_risk:,.2f}",
        f"- Replay quality score: {report.quality_score:,.2f}",
        f"- Primary failure: {report.primary_failure}",
        "",
        "## Evidence boundary",
        "",
        report.evidence_boundary,
        "",
        "Generated by option-replay-report-engine.",
    ]
    return "\n".join(lines)


def _spread_cost_bps(entry: OptionSnapshot, exit_: OptionSnapshot) -> float:
    entry_bps = entry.spread / max(entry.option_mid, 0.01) * 10_000
    exit_bps = exit_.spread / max(exit_.option_mid, 0.01) * 10_000
    return (entry_bps + exit_bps) / 2


def _reward_to_risk(inputs: ReplayInputs) -> float:
    risk = max(0.01, inputs.trade.entry_fill - inputs.stop_loss)
    reward = max(0.0, inputs.target - inputs.trade.entry_fill)
    return reward / risk


def _quality_score(
    *,
    net_pnl: float,
    signal_edge_bps: float,
    spread_cost_bps: float,
    reward_to_risk: float,
    realized_underlying_move: float,
) -> float:
    score = 50.0
    score += min(25.0, max(-25.0, net_pnl / 20.0))
    score += min(15.0, signal_edge_bps / 3.0)
    score += min(10.0, reward_to_risk * 3.0)
    score += min(10.0, realized_underlying_move * 4.0)
    score -= min(30.0, spread_cost_bps / 150.0)
    return min(100.0, max(0.0, score))


def _verdict(score: float) -> str:
    if score >= 75.0:
        return "Promote"
    if score >= 55.0:
        return "Watchlist"
    return "Reject"


def _primary_failure(
    net_pnl: float,
    spread_cost_bps: float,
    realized_underlying_move: float,
    signal_edge_bps: float,
) -> str:
    if spread_cost_bps > 1800:
        return "Spread cost overwhelmed the setup"
    if net_pnl < 0 and realized_underlying_move <= 0:
        return "Underlying move went against the contract"
    if signal_edge_bps < 15:
        return "Signal edge was too weak"
    if net_pnl < 0:
        return "Contract PnL was negative after costs"
    return "No material failure detected"


__all__ = [
    "OptionSnapshot",
    "OptionTrade",
    "ReplayInputs",
    "ReplayReport",
    "explain_replay",
    "render_markdown_report",
]
