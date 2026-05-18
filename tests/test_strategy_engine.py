from app.schemas.strategy import StrategyAnalysisRequest
from app.services.strategy_engine import analyze_strategy


def test_strategy_engine_returns_20_ideas_and_top5():
    result = analyze_strategy(StrategyAnalysisRequest())

    assert len(result.ideas) == 20
    assert len(result.top5) == 5
    assert result.winner.name == 'Agente de cobrança preventiva para PMEs'
    assert any(item.eliminate_reason for item in result.ideas)


def test_strategy_engine_framing_mentions_capital_and_target():
    result = analyze_strategy(StrategyAnalysisRequest(available_capital_brl=2500, target_brl=20000, max_hours_per_day=2))

    assert 'R$2.500' in result.framing
    assert 'R$20.000' in result.framing
    assert '2h/dia' in result.framing
