from collections import defaultdict

from app.db.models import Company, Signal
from app.schemas.lead import LeadExecutiveRead
from app.services.scoring import ScoreResult


SOURCE_CONTACT_HINTS = {
    'linkedin jobs': ['RH', 'Controller', 'Coordenador Financeiro'],
    'indeed': ['RH', 'Tesouraria', 'Financeiro'],
    'gupy': ['RH', 'Financeiro'],
    'corporate careers': ['RH', 'Diretoria Administrativa'],
    'notícias regionais': ['Diretor Operacional', 'Diretor Financeiro'],
    'noticias regionais': ['Diretor Operacional', 'Diretor Financeiro'],
    'jusbrasil': ['Diretor Financeiro', 'Jurídico', 'Sócio-administrador'],
}


def _location(company: Company) -> str | None:
    if company.city and company.state:
        return f"{company.city}/{company.state}"
    return company.city or company.state


def _score_bucket(score: float) -> str:
    if score <= 30:
        return 'baixa probabilidade'
    if score <= 60:
        return 'média probabilidade'
    if score <= 80:
        return 'alta probabilidade'
    return 'oportunidade prioritária'


def _lead_confidence(score: float, signal_count: int, source_count: int) -> str:
    if score >= 81 and signal_count >= 4 and source_count >= 2:
        return 'alta'
    if score >= 55 and signal_count >= 2:
        return 'média'
    return 'baixa'


def _contexto_operacional(company: Company, signals: list[Signal]) -> str:
    signal_types = {signal.signal_type for signal in signals}
    if {'new_branch', 'geographic_expansion', 'new_distribution_center'} & signal_types:
        return 'Há sinais públicos de expansão operacional e aumento de complexidade logística/comercial.'
    if {'controller_hiring', 'treasury_hiring', 'collections_hiring'} & signal_types:
        return 'Há sinais de reforço da estrutura financeira e administrativa.'
    if {'execution_process', 'judicial_recovery_signal', 'financial_restructuring'} & signal_types:
        return 'Há sinais de pressão jurídica/financeira com potencial impacto no caixa e na operação.'
    return f'Empresa monitorada no setor {company.sector or "não identificado"}, com sinais públicos relevantes em análise.'


def _contatos(signals: list[Signal]) -> list[str]:
    contacts: list[str] = []
    for signal in signals:
        contacts.extend(SOURCE_CONTACT_HINTS.get(signal.source_name.lower(), []))
    deduped = []
    for item in contacts:
        if item not in deduped:
            deduped.append(item)
    return deduped[:6]


def _evidencias(signals: list[Signal]) -> list[str]:
    items = []
    for signal in signals[:8]:
        excerpt = signal.excerpt.strip().replace('\n', ' ')
        if len(excerpt) > 140:
            excerpt = excerpt[:137] + '...'
        items.append(f"[{signal.source_name}] {signal.signal_type}: {excerpt}")
    return items


def _fontes(signals: list[Signal]) -> list[str]:
    seen = []
    for signal in signals:
        if signal.source_name not in seen:
            seen.append(signal.source_name)
    return seen


def format_executive_lead(company: Company, signals: list[Signal], score_result: ScoreResult) -> LeadExecutiveRead:
    ordered_signals = sorted(signals, key=lambda s: s.detected_at, reverse=True)
    principais_sinais = []
    seen_signal_types = set()
    for signal in ordered_signals:
        if signal.signal_type in seen_signal_types:
            continue
        principais_sinais.append(signal.signal_type)
        seen_signal_types.add(signal.signal_type)
    principais_sinais = principais_sinais[:8]

    fontes = _fontes(ordered_signals)
    resumo = (
        f"{company.trade_name or company.legal_name} apresenta sinais consistentes de intenção financeira/comercial. "
        f"Score {score_result.score} ({_score_bucket(score_result.score)}), com destaque para {', '.join(principais_sinais[:3]) or 'sinais monitorados'}"
        f" e fontes {', '.join(fontes[:3]) or 'não identificadas'}."
    )

    return LeadExecutiveRead(
        company_id=company.id,
        empresa=company.trade_name or company.legal_name,
        setor=company.sector,
        localizacao=_location(company),
        porte_estimado=company.estimated_size,
        score_necessidade_capital=score_result.score,
        probabilidade_conversao=score_result.conversion_probability,
        score_bucket=_score_bucket(score_result.score),
        principais_sinais_detectados=principais_sinais,
        contexto_operacional=_contexto_operacional(company, ordered_signals),
        hipotese_de_dor=score_result.hypothesis_of_pain,
        melhor_abordagem_comercial=score_result.best_approach,
        produto_mais_indicado=score_result.recommended_product,
        timing_ideal_de_abordagem=score_result.timing,
        risco=score_result.risk,
        contatos_encontrados=_contatos(ordered_signals),
        fontes_utilizadas=fontes,
        confianca_do_lead=_lead_confidence(score_result.score, len(ordered_signals), len(fontes)),
        evidencias=_evidencias(ordered_signals),
        resumo_executivo=resumo,
        criado_em=ordered_signals[0].detected_at if ordered_signals else company.created_at,
    )
