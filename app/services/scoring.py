from collections import Counter
from dataclasses import dataclass

from app.data.signal_weights import PRIORITY_SECTORS, SIGNAL_WEIGHTS
from app.db.models import Company, Signal


@dataclass
class ScoreResult:
    score: float
    conversion_probability: str
    lead_tier: str
    summary: str
    hypothesis_of_pain: str
    best_approach: str
    recommended_product: str
    timing: str
    risk: str
    score_explanation: str


def _base_weight(signal: Signal) -> float:
    category_map = SIGNAL_WEIGHTS.get(signal.category, {})
    weight = signal.weight_override if signal.weight_override is not None else category_map.get(signal.signal_type, 3)
    return weight * max(min(signal.confidence, 1.0), 0.1)


def _sector_bonus(sector: str | None) -> float:
    if not sector:
        return 0
    normalized = sector.strip().lower()
    return PRIORITY_SECTORS.get(normalized, 0)


def _size_adjustment(estimated_size: str | None) -> float:
    if not estimated_size:
        return 0
    normalized = estimated_size.strip().lower()
    if normalized in {"micro", "mei", "small"}:
        return -15
    if normalized in {"medium", "mid", "médio", "medio"}:
        return 6
    if normalized in {"large", "enterprise", "grande"}:
        return 10
    return 0


def _conversion_label(score: float) -> str:
    if score >= 81:
        return "muito alta"
    if score >= 61:
        return "alta"
    if score >= 31:
        return "média"
    return "baixa"


def _tier(score: float) -> str:
    if score >= 81:
        return "A"
    if score >= 61:
        return "B"
    if score >= 41:
        return "C"
    return "D"


def _product_recommendation(counter: Counter) -> str:
    if counter["explicit_credit_search"] or counter["financial_restructuring"]:
        return "crédito estruturado"
    if counter["erp_change"] or counter["erp_implementation"]:
        return "ERP financeiro / automação financeira"
    if counter["new_branch"] or counter["fleet_expansion"] or counter["geographic_expansion"]:
        return "antecipação de recebíveis / FIDC performado"
    return "consultoria financeira + capital de giro"


def score_company(company: Company, signals: list[Signal]) -> ScoreResult:
    if not signals:
        return ScoreResult(
            score=0,
            conversion_probability="baixa",
            lead_tier="D",
            summary="Nenhum sinal suficiente encontrado para inferir necessidade financeira.",
            hypothesis_of_pain="Sem evidências públicas suficientes.",
            best_approach="Monitorar antes de abordar.",
            recommended_product="nenhum no momento",
            timing="aguardar novos sinais",
            risk="alto risco de falso positivo",
            score_explanation="Sem sinais cadastrados.",
        )

    weighted_sum = sum(_base_weight(signal) for signal in signals)
    sector_bonus = _sector_bonus(company.sector)
    size_bonus = _size_adjustment(company.estimated_size)
    signal_density_bonus = 10 if len(signals) >= 3 else 0
    raw_score = weighted_sum + sector_bonus + size_bonus + signal_density_bonus
    score = round(min(raw_score, 100), 2)

    signal_counter = Counter(signal.signal_type for signal in signals)
    top_signals = ", ".join(signal.signal_type for signal in signals[:5])
    product = _product_recommendation(signal_counter)
    conversion = _conversion_label(score)
    tier = _tier(score)

    summary = (
        f"Empresa com {len(signals)} sinais monitorados. Principais gatilhos detectados: {top_signals}. "
        f"Score calculado em {score}, sugerindo probabilidade {conversion} de necessidade de capital ou eficiência financeira."
    )

    if signal_counter["new_branch"] or signal_counter["fleet_expansion"] or signal_counter["geographic_expansion"]:
        pain = "Expansão operacional pode estar pressionando caixa, frota, estoque ou ciclo de recebimento."
        approach = "Abordagem consultiva orientada a funding para crescimento sem travar a operação."
        timing = "imediato, enquanto a expansão ainda está sendo absorvida"
    elif signal_counter["controller_hiring"] or signal_counter["treasury_hiring"] or signal_counter["collections_hiring"]:
        pain = "Reforço financeiro sugere dor de controle, previsibilidade de caixa ou cobrança."
        approach = "Abordagem focada em previsibilidade financeira, recebíveis e governança de caixa."
        timing = "curto prazo, antes de a empresa estabilizar o novo time"
    elif signal_counter["erp_change"] or signal_counter["erp_implementation"]:
        pain = "Mudança de stack indica janela de transformação administrativa e financeira."
        approach = "Oferta de eficiência operacional e integração de crédito/recebíveis com stack financeira."
        timing = "durante a implantação ou seleção de fornecedores"
    else:
        pain = "Sinais sugerem necessidade potencial, mas ainda difusa entre operação e finanças."
        approach = "Abordagem leve, validando contexto e prioridade financeira."
        timing = "após confirmação de novo sinal forte"

    risk = "baixo" if score >= 81 else "médio" if score >= 61 else "alto"
    explanation = (
        f"weighted_sum={round(weighted_sum, 2)}; sector_bonus={sector_bonus}; "
        f"size_adjustment={size_bonus}; signal_density_bonus={signal_density_bonus}; final_score={score}"
    )

    return ScoreResult(
        score=score,
        conversion_probability=conversion,
        lead_tier=tier,
        summary=summary,
        hypothesis_of_pain=pain,
        best_approach=approach,
        recommended_product=product,
        timing=timing,
        risk=risk,
        score_explanation=explanation,
    )
