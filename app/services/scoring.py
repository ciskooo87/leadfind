from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime

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


def _signal_age_days(signal: Signal) -> int:
    detected_at = signal.detected_at
    if detected_at.tzinfo is None:
        detected_at = detected_at.replace(tzinfo=UTC)
    now = datetime.now(UTC)
    return max((now - detected_at).days, 0)


def _recency_multiplier(signal: Signal) -> float:
    age_days = _signal_age_days(signal)
    if age_days <= 30:
        return 1.0
    if age_days <= 60:
        return 0.9
    if age_days <= 90:
        return 0.75
    if age_days <= 120:
        return 0.6
    return 0.45


def _base_weight(signal: Signal) -> float:
    category_map = SIGNAL_WEIGHTS.get(signal.category, {})
    weight = signal.weight_override if signal.weight_override is not None else category_map.get(signal.signal_type, 3)
    confidence = max(min(signal.confidence, 1.0), 0.1)
    return weight * confidence * _recency_multiplier(signal)


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


def _source_buckets(signals: list[Signal]) -> dict[str, int]:
    counts = {"jobs": 0, "news": 0, "legal": 0, "reputation": 0, "other": 0}
    for signal in signals:
        source_name = signal.source_name.lower()
        if source_name in {"linkedin jobs", "indeed", "gupy", "greenhouse", "lever", "workday", "corporate careers"}:
            counts["jobs"] += 1
        elif source_name in {"notícias regionais", "noticias regionais"}:
            counts["news"] += 1
        elif source_name in {"jusbrasil"}:
            counts["legal"] += 1
        elif source_name in {"reclamações operacionais", "reclamacoes operacionais"}:
            counts["reputation"] += 1
        else:
            counts["other"] += 1
    return counts


def _cross_source_bonus(source_buckets: dict[str, int], counter: Counter) -> tuple[float, list[str]]:
    bonus = 0.0
    reasons: list[str] = []

    if source_buckets["jobs"] and source_buckets["news"]:
        bonus += 8
        reasons.append("jobs+news")
    if source_buckets["jobs"] and source_buckets["legal"]:
        bonus += 12
        reasons.append("jobs+legal")
    if source_buckets["news"] and source_buckets["legal"]:
        bonus += 15
        reasons.append("news+legal")
    if source_buckets["reputation"] and source_buckets["legal"]:
        bonus += 16
        reasons.append("reputation+legal")
    if source_buckets["reputation"] and source_buckets["news"]:
        bonus += 11
        reasons.append("reputation+news")
    if source_buckets["jobs"] and source_buckets["reputation"]:
        bonus += 9
        reasons.append("jobs+reputation")
    if source_buckets["jobs"] and source_buckets["news"] and source_buckets["legal"]:
        bonus += 10
        reasons.append("jobs+news+legal")
    if source_buckets["news"] and source_buckets["legal"] and source_buckets["reputation"]:
        bonus += 14
        reasons.append("news+legal+reputation")

    if counter["financial_restructuring"] and counter["judicial_recovery_signal"]:
        bonus += 10
        reasons.append("restructuring+judicial_recovery")
    if counter["new_branch"] and counter["controller_hiring"]:
        bonus += 6
        reasons.append("expansion+financial_hiring")
    if counter["new_distribution_center"] and counter["treasury_hiring"]:
        bonus += 6
        reasons.append("distribution+treasury")
    if counter["execution_process"] and counter["legal_collection_growth"]:
        bonus += 8
        reasons.append("execution+collection")
    if counter["delivery_delay_complaints"] and counter["billing_delay_complaints"]:
        bonus += 8
        reasons.append("delivery+billing_complaints")
    if counter["delivery_delay_complaints"] and counter["execution_process"]:
        bonus += 10
        reasons.append("operational_delay+execution")
    if counter["service_breakdown_complaints"] and counter["judicial_recovery_signal"]:
        bonus += 12
        reasons.append("service_breakdown+judicial_recovery")
    if counter["new_branch"] and counter["delivery_delay_complaints"]:
        bonus += 7
        reasons.append("expansion+operational_breakdown")

    return bonus, reasons


def _product_recommendation(counter: Counter, source_buckets: dict[str, int], score: float) -> str:
    if counter["judicial_recovery_signal"] or counter["financial_restructuring"]:
        return "crédito estruturado / reestruturação financeira"
    if source_buckets["reputation"] and source_buckets["legal"]:
        return "capital de giro emergencial / reestruturação consultiva"
    if source_buckets["legal"] and source_buckets["news"]:
        return "capital de giro estruturado / FIDC performado"
    if counter["erp_change"] or counter["erp_implementation"]:
        return "ERP financeiro / automação financeira"
    if counter["new_branch"] or counter["fleet_expansion"] or counter["geographic_expansion"] or counter["new_distribution_center"]:
        return "antecipação de recebíveis / FIDC performado"
    if source_buckets["legal"] and score >= 55:
        return "factoring consultivo / crédito com análise reforçada"
    return "consultoria financeira + capital de giro"


def _pain_and_approach(counter: Counter, source_buckets: dict[str, int]) -> tuple[str, str, str]:
    if counter["judicial_recovery_signal"] or counter["financial_restructuring"]:
        return (
            "Sinais jurídicos e financeiros sugerem estresse relevante, possível deterioração de caixa e necessidade de reestruturação.",
            "Abordagem consultiva sênior, focada em solução estruturada, governança e proteção de liquidez.",
            "imediato, antes de agravamento do quadro"
        )
    if source_buckets["reputation"] and source_buckets["legal"]:
        return (
            "Há combinação de dor operacional visível no mercado com pressão jurídica/financeira, sugerindo tensão concreta na operação e no caixa.",
            "Abordagem consultiva, direta e orientada a estabilização operacional, liquidez e reorganização do ciclo financeiro.",
            "imediato, enquanto a dor está pública e relevante"
        )
    if source_buckets["news"] and source_buckets["jobs"]:
        return (
            "Expansão operacional acompanhada de reforço administrativo/financeiro sugere descasamento entre crescimento e caixa.",
            "Abordagem orientada a funding do crescimento, previsibilidade de recebíveis e eficiência operacional.",
            "imediato, enquanto a expansão ainda está sendo absorvida"
        )
    if source_buckets["reputation"]:
        return (
            "Reclamações operacionais indicam desgaste de entrega, faturamento ou atendimento, com potencial impacto no caixa e retenção de clientes.",
            "Abordagem baseada em eficiência operacional, recuperação de previsibilidade e reforço do fluxo financeiro.",
            "curto prazo, com foco em resolução objetiva de dor"
        )
    if source_buckets["legal"]:
        return (
            "Pressão jurídica indica tensão financeira, cobrança crescente ou perda de controle do ciclo de pagamentos.",
            "Abordagem cuidadosa, consultiva e baseada em estabilização financeira e alternativas de liquidez.",
            "curto prazo, com sensibilidade comercial"
        )
    if counter["new_branch"] or counter["fleet_expansion"] or counter["geographic_expansion"] or counter["new_distribution_center"]:
        return (
            "Expansão operacional pode estar pressionando caixa, frota, estoque ou ciclo de recebimento.",
            "Abordagem consultiva orientada a funding para crescimento sem travar a operação.",
            "imediato, enquanto a expansão ainda está sendo absorvida"
        )
    if counter["controller_hiring"] or counter["treasury_hiring"] or counter["collections_hiring"]:
        return (
            "Reforço financeiro sugere dor de controle, previsibilidade de caixa ou cobrança.",
            "Abordagem focada em previsibilidade financeira, recebíveis e governança de caixa.",
            "curto prazo, antes de a empresa estabilizar o novo time"
        )
    if counter["erp_change"] or counter["erp_implementation"]:
        return (
            "Mudança de stack indica janela de transformação administrativa e financeira.",
            "Oferta de eficiência operacional e integração de crédito/recebíveis com stack financeira.",
            "durante a implantação ou seleção de fornecedores"
        )
    return (
        "Sinais sugerem necessidade potencial, mas ainda difusa entre operação e finanças.",
        "Abordagem leve, validando contexto e prioridade financeira.",
        "após confirmação de novo sinal forte"
    )


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
    recent_signals_count = sum(1 for signal in signals if _signal_age_days(signal) <= 60)
    evidence_bonus = 5 if recent_signals_count >= 2 else 0
    signal_counter = Counter(signal.signal_type for signal in signals)
    source_buckets = _source_buckets(signals)
    cross_source_bonus, cross_reasons = _cross_source_bonus(source_buckets, signal_counter)

    raw_score = weighted_sum + sector_bonus + size_bonus + signal_density_bonus + evidence_bonus + cross_source_bonus
    score = round(min(raw_score, 100), 2)

    top_signals = ", ".join(signal.signal_type for signal in signals[:8])
    conversion = _conversion_label(score)
    tier = _tier(score)
    product = _product_recommendation(signal_counter, source_buckets, score)
    pain, approach, timing = _pain_and_approach(signal_counter, source_buckets)

    summary = (
        f"Empresa com {len(signals)} sinais monitorados. Principais gatilhos detectados: {top_signals}. "
        f"Distribuição por fonte: jobs={source_buckets['jobs']}, news={source_buckets['news']}, legal={source_buckets['legal']}, reputation={source_buckets['reputation']}. "
        f"Score calculado em {score}, sugerindo probabilidade {conversion} de necessidade de capital ou eficiência financeira."
    )

    if score >= 81:
        risk = "baixo"
    elif score >= 61:
        risk = "médio"
    else:
        risk = "alto"

    explanation = (
        f"weighted_sum={round(weighted_sum, 2)}; sector_bonus={sector_bonus}; size_adjustment={size_bonus}; "
        f"signal_density_bonus={signal_density_bonus}; evidence_bonus={evidence_bonus}; cross_source_bonus={cross_source_bonus}; "
        f"recent_signals_count={recent_signals_count}; source_buckets={source_buckets}; cross_reasons={cross_reasons}; final_score={score}"
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
