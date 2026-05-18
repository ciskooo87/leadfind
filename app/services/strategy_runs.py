import json

from sqlalchemy.orm import Session

from app.db.models import StrategyAnalysisRun
from app.schemas.strategy import StrategyAnalysisRequest, StrategyAnalysisResponse
from app.schemas.strategy_run import StrategyAnalysisRunCreate, StrategyAnalysisRunDetail, StrategyAnalysisRunRead
from app.services.strategy_engine import analyze_strategy, infer_market_signals


def _applied_signals(request: StrategyAnalysisRequest) -> list[str]:
    return list(dict.fromkeys((request.market_signals or []) + infer_market_signals(request)))


def create_strategy_run(db: Session, payload: StrategyAnalysisRunCreate) -> StrategyAnalysisRunDetail:
    response = analyze_strategy(payload.request)
    applied_signals = _applied_signals(payload.request)
    run = StrategyAnalysisRun(
        title=payload.title,
        request_payload=payload.request.model_dump_json(),
        response_payload=response.model_dump_json(),
        winner_name=response.winner.name,
        top_opportunity_names=json.dumps([item.name for item in response.top5]),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return StrategyAnalysisRunDetail(
        id=run.id,
        title=run.title,
        winner_name=run.winner_name,
        top_opportunity_names=json.loads(run.top_opportunity_names or '[]'),
        applied_signals=applied_signals,
        created_at=run.created_at,
        request=StrategyAnalysisRequest(**json.loads(run.request_payload)),
        response=response,
    )


def list_strategy_runs(db: Session) -> list[StrategyAnalysisRunRead]:
    runs = db.query(StrategyAnalysisRun).order_by(StrategyAnalysisRun.created_at.desc()).all()
    return [
        StrategyAnalysisRunRead(
            id=run.id,
            title=run.title,
            winner_name=run.winner_name,
            top_opportunity_names=json.loads(run.top_opportunity_names or '[]'),
            applied_signals=_applied_signals(StrategyAnalysisRequest(**json.loads(run.request_payload))),
            created_at=run.created_at,
        )
        for run in runs
    ]


def get_strategy_run(db: Session, run_id: int) -> StrategyAnalysisRunDetail | None:
    run = db.get(StrategyAnalysisRun, run_id)
    if not run:
        return None
    request = StrategyAnalysisRequest(**json.loads(run.request_payload))
    return StrategyAnalysisRunDetail(
        id=run.id,
        title=run.title,
        winner_name=run.winner_name,
        top_opportunity_names=json.loads(run.top_opportunity_names or '[]'),
        applied_signals=_applied_signals(request),
        created_at=run.created_at,
        request=request,
        response=StrategyAnalysisResponse(**json.loads(run.response_payload)),
    )
