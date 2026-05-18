from dataclasses import dataclass
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
    'fluxo de caixa': ('cash_pressure', 5),
    'automação': ('ops_automation', 3),
    'automacao': ('ops_automation', 3),
    'eficiência': ('ops_automation', 2),
    'eficiencia': ('ops_automation', 2),
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


@dataclass(frozen=True)
class SignalSuggestion:
    signal_key: str
    label: str
    score: int
    reasons: list[str]


@dataclass(frozen=True)
class AssistedSignalSuggestion:
    primary: ExternalMarketSignalCreate
    alternatives: list[SignalSuggestion]
    reasons: list[str]


def _score_blob(blob: str) -> tuple[dict[str, int], dict[str, list[str]]]:
    scores: dict[str, int] = {key: 0 for key in MARKET_SIGNALS}
    reasons: dict[str, list[str]] = {key: [] for key in MARKET_SIGNALS}
    for keyword, (signal_key, weight) in KEYWORD_MAP.items():
        if keyword in blob:
            scores[signal_key] += weight
            reasons[signal_key].append(f'contém "{keyword}" (+{weight})')
    return scores, reasons


def suggest_external_signal(raw_text: str, source_url: str | None = None, title: str | None = None, source_name: str | None = None) -> ExternalMarketSignalCreate:
    return suggest_external_signal_details(raw_text, source_url=source_url, title=title, source_name=source_name).primary


def suggest_external_signal_details(raw_text: str, source_url: str | None = None, title: str | None = None, source_name: str | None = None) -> AssistedSignalSuggestion:
    blob = ' '.join(filter(None, [title, raw_text, source_url])).lower()
    scores, reasons_map = _score_blob(blob)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    signal_key = ranked[0][0] if ranked and ranked[0][1] > 0 else 'ops_automation'
    relevance_weight = min(max(scores.get(signal_key, 0), 1), 10)
    normalized_title = title or f'Sinal assistido · {MARKET_SIGNALS[signal_key].label}'
    source = source_name or (urlparse(source_url).netloc if source_url else 'manual-assistido') or 'manual-assistido'
    summary = raw_text.strip()[:500] or MARKET_SIGNALS[signal_key].description

    alternatives = [
        SignalSuggestion(
            signal_key=key,
            label=MARKET_SIGNALS[key].label,
            score=score,
            reasons=reasons_map[key] or [MARKET_SIGNALS[key].description],
        )
        for key, score in ranked[:3]
        if score > 0
    ]
    primary_reasons = reasons_map[signal_key] or [MARKET_SIGNALS[signal_key].description]

    return AssistedSignalSuggestion(
        primary=ExternalMarketSignalCreate(
            signal_key=signal_key,
            title=normalized_title,
            source_name=source,
            source_url=source_url,
            summary=summary,
            relevance_weight=relevance_weight,
            active=True,
        ),
        alternatives=alternatives,
        reasons=primary_reasons,
    )
