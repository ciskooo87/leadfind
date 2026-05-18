import json

from sqlalchemy.orm import Session

from app.db.models import StrategyAnalysisRun
from app.schemas.strategy import StrategyAnalysisRequest, StrategyAnalysisResponse
from app.schemas.strategy_run import StrategyAnalysisRunCreate, StrategyAnalysisRunDetail, StrategyAnalysisRunRead
from app.services.strategy_engine import analyze_strategy


def create_strategy_run(db: Session, payload: StrategyAnalysisRunCreate) -> StrategyAnalysisRunDetail:
    response = analyze_strategy(payload.request)
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
            created_at=run.created_at,
        )
        for run in runs
    ]


def get_strategy_run(db: Session, run_id: int) -> StrategyAnalysisRunDetail | None:
    run = db.get(StrategyAnalysisRun, run_id)
    if not run:
        return None
    return StrategyAnalysisRunDetail(
        id=run.id,
        title=run.title,
        winner_name=run.winner_name,
        top_opportunity_names=json.loads(run.top_opportunity_names or '[]'),
        created_at=run.created_at,
        request=StrategyAnalysisRequest(**json.loads(run.request_payload)),
        response=StrategyAnalysisResponse(**json.loads(run.response_payload)),
    )
