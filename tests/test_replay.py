from option_replay_report_engine import (
    OptionSnapshot,
    OptionTrade,
    ReplayInputs,
    explain_replay,
    render_markdown_report,
)


def test_replay_attributes_contract_pnl_and_costs():
    replay = explain_replay(
        ReplayInputs(
            symbol="NVDA",
            strategy_name="Opening Drive Continuation",
            entry=OptionSnapshot(
                underlying_price=140.0,
                option_mid=4.00,
                option_bid=3.90,
                option_ask=4.10,
                implied_volatility=0.62,
                delta=0.54,
                theta=-0.18,
                timestamp="2026-07-21T09:35:00-04:00",
            ),
            exit=OptionSnapshot(
                underlying_price=143.0,
                option_mid=5.35,
                option_bid=5.25,
                option_ask=5.45,
                implied_volatility=0.66,
                delta=0.58,
                theta=-0.16,
                timestamp="2026-07-21T10:20:00-04:00",
            ),
            trade=OptionTrade(
                side="long_call",
                contracts=3,
                entry_fill=4.10,
                exit_fill=5.25,
                fees_per_contract=0.65,
            ),
            signal_edge_bps=42.0,
            expected_move=2.20,
            stop_loss=2.90,
            target=5.80,
        )
    )

    assert replay.symbol == "NVDA"
    assert replay.contract_pnl == 345.0
    assert replay.net_pnl == 341.10
    assert replay.edge_component > 150.0
    assert replay.slippage_component < 0.0
    assert replay.theta_component < 0.0
    assert replay.volatility_component > 0.0
    assert replay.quality_score >= 80.0
    assert replay.verdict == "Promote"


def test_replay_penalizes_bad_liquidity_and_drawdown_risk():
    replay = explain_replay(
        ReplayInputs(
            symbol="SNDK",
            strategy_name="Failed Breakout Fade",
            entry=OptionSnapshot(
                underlying_price=62.0,
                option_mid=2.50,
                option_bid=2.05,
                option_ask=2.95,
                implied_volatility=0.88,
                delta=-0.42,
                theta=-0.31,
                timestamp="2026-07-21T09:40:00-04:00",
            ),
            exit=OptionSnapshot(
                underlying_price=62.8,
                option_mid=2.10,
                option_bid=1.70,
                option_ask=2.50,
                implied_volatility=0.84,
                delta=-0.39,
                theta=-0.29,
                timestamp="2026-07-21T10:05:00-04:00",
            ),
            trade=OptionTrade(
                side="long_put",
                contracts=2,
                entry_fill=2.95,
                exit_fill=1.70,
                fees_per_contract=0.65,
            ),
            signal_edge_bps=8.0,
            expected_move=1.10,
            stop_loss=1.85,
            target=4.10,
        )
    )

    assert replay.net_pnl == -252.60
    assert replay.spread_cost_bps > 2500.0
    assert replay.quality_score < 45.0
    assert replay.verdict == "Reject"
    assert "spread" in replay.primary_failure.lower()


def test_markdown_report_is_recruiter_readable_and_audit_friendly():
    replay = explain_replay(
        ReplayInputs.sample(symbol="MU", side="long_call", contracts=1)
    )

    markdown = render_markdown_report(replay)

    assert "# Option Replay Report: MU" in markdown
    assert "## PnL Attribution" in markdown
    assert "Net PnL" in markdown
    assert "Theta drag" in markdown
    assert "Liquidity cost" in markdown
    assert "Evidence boundary" in markdown
    assert "_" not in markdown.replace("option-replay-report-engine", "")
