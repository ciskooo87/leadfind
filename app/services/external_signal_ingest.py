from urllib.parse import urlparse

from app.schemas.external_signal import ExternalMarketSignalCreate
from app.services.strategy_engine import MARKET_SIGNALS


KEYWORD_MAP: dict[str, tuple[str, int]] = {
    'documento': ('doc_generation', 4),
    'documentação': ('doc_generation', 4),
    'ocr': ('doc_generation', 4),
    'contrato': ('doc_generation', 3),
    'caixa': ('cash_pressure', 4),
    'inadimpl': ('cash_pressure', 4),
    'cobran': ('cash_pressure', 4),
    'automação': ('ops_automation', 3),
    'automacao': ('ops_automation', 3),
    'redução de equipe': ('team_reduction', 3),
    'enxuta': ('team_reduction', 2),
    'ia local': ('ai_local', 3),
    'privacidade': ('ai_local', 2),
    'creator': ('creator_ai', 2),
    'ugc': ('creator_ai', 2),
    'dashboard': ('bi_simplified', 2),
    'bi': ('bi_simplified', 2),
    'setor tradicional': ('aged_niches', 2),
    'indústria': ('aged_niches', 2),
    'industria': ('aged_niches', 2),
}


def suggest_external_signal(raw_text: str, source_url: str | None = None, title: str | None = None, source_name: str | None = None) -> ExternalMarketSignalCreate:
    blob = ' '.join(filter(None, [title, raw_text, source_url])).lower()
    scores: dict[str, int] = {key: 0 for key in MARKET_SIGNALS}
    for keyword, (signal_key, weight) in KEYWORD_MAP.items():
        if keyword in blob:
            scores[signal_key] += weight

    signal_key = max(scores, key=scores.get) if any(scores.values()) else 'ops_automation'
    relevance_weight = min(max(scores.get(signal_key, 0), 1), 10)
    normalized_title = title or f'Sinal assistido · {MARKET_SIGNALS[signal_key].label}'
    source = source_name or (urlparse(source_url).netloc if source_url else 'manual-assistido') or 'manual-assistido'
    summary = raw_text.strip()[:500] or MARKET_SIGNALS[signal_key].description

    return ExternalMarketSignalCreate(
        signal_key=signal_key,
        title=normalized_title,
        source_name=source,
        source_url=source_url,
        summary=summary,
        relevance_weight=relevance_weight,
        active=True,
    )
