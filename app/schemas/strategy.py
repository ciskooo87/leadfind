from pydantic import BaseModel, Field


class StrategyAnalysisRequest(BaseModel):
    available_capital_brl: float = Field(default=2500, ge=0)
    target_brl: float = Field(default=20000, ge=1000)
    max_hours_per_day: float = Field(default=2, gt=0, le=24)
    market_scope: str = Field(default='Brasil + global')
    profile: str = Field(default='executor solo orientado a ativos')
    end_horizon: str = Field(default='até o final do ano')
    prioritize_recurrence: bool = True
    prioritize_automation: bool = True
    avoid_saturated: bool = True
    market_signals: list[str] = Field(default_factory=list)
    external_context: dict[str, int] = Field(default_factory=dict)


class OpportunityIdea(BaseModel):
    name: str
    summary: str
    speed_of_return: int
    operational_ease: int
    scale_potential: int
    risk_level: int
    barrier_to_entry: int
    automation_fit: int
    realistic_20k_score: int
    asymmetry_score: int
    hidden: bool = False
    category: str
    why_now: str
    execution_hint: str
    eliminate_reason: str | None = None


class DeepOpportunity(BaseModel):
    rank: int
    name: str
    thesis: str
    why_it_wins: str
    how_to_start_with_2500: list[str]
    structure_needed: list[str]
    tools: list[str]
    daily_time_real: str
    where_the_money_is: str
    how_to_scale: str
    main_risks: list[str]
    risk_reduction: list[str]
    first_customers: list[str]
    revenue_30d: str
    revenue_60d: str
    revenue_90d: str
    revenue_180d: str
    automate_first: list[str]
    kill_fast_if: list[str]


class OpportunityMatrix(BaseModel):
    low_risk_high_scale: list[str]
    low_risk_low_scale: list[str]
    high_risk_high_scale: list[str]
    hidden_opportunities: list[str]


class StrategyWinner(BaseModel):
    name: str
    why_it_wins: str
    why_others_lose: list[str]
    best_execution_path: list[str]
    real_bottleneck: str
    common_mistakes: list[str]
    operating_in_2h: list[str]


class StrategyAnalysisResponse(BaseModel):
    framing: str
    ideas: list[OpportunityIdea]
    top5: list[DeepOpportunity]
    matrix: OpportunityMatrix
    winner: StrategyWinner
    implementation_plan: list[str]
