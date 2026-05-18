from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.strategy import (
    DeepOpportunity,
    OpportunityIdea,
    OpportunityMatrix,
    StrategyAnalysisRequest,
    StrategyAnalysisResponse,
    StrategyWinner,
)


@dataclass(frozen=True)
class MarketSignal:
    key: str
    label: str
    weight: int
    description: str


@dataclass(frozen=True)
class IdeaSeed:
    name: str
    summary: str
    category: str
    speed: int
    ease: int
    scale: int
    risk: int
    barrier: int
    automation: int
    realism: int
    hidden: bool
    why_now: str
    execution_hint: str
    tags: tuple[str, ...] = field(default_factory=tuple)
    asymmetry_bonus: int = 0
    eliminate_reason: str | None = None


MARKET_SIGNALS: dict[str, MarketSignal] = {
    'ai_local': MarketSignal('ai_local', 'IA local e privacidade', 2, 'Times sensíveis a dados tendem a comprar eficiência sem mandar tudo para SaaS externo.'),
    'ops_automation': MarketSignal('ops_automation', 'Automação operacional', 3, 'PMEs e times enxutos estão cortando trabalho manual e headcount.'),
    'team_reduction': MarketSignal('team_reduction', 'Redução de equipe', 2, 'Empresas querem ferramentas que substituam coordenação humana repetitiva.'),
    'doc_generation': MarketSignal('doc_generation', 'Documentação automática', 3, 'Documentos, checklists e dossiês são gargalos quentes e fáceis de provar ROI.'),
    'bi_simplified': MarketSignal('bi_simplified', 'BI simplificado', 2, 'Negócios envelhecidos precisam de visibilidade operacional sem virar data team.'),
    'creator_ai': MarketSignal('creator_ai', 'Creators usando IA', 1, 'A dor real do creator não é conteúdo, é operação, cobrança e entrega.'),
    'aged_niches': MarketSignal('aged_niches', 'Nichos envelhecidos e mal digitalizados', 2, 'Mercados tradicionais ainda pagam por software invisível e utilitário.'),
    'cash_pressure': MarketSignal('cash_pressure', 'Pressão de caixa', 3, 'Quando caixa aperta, soluções que recuperam dinheiro ou reduzem fuga vendem melhor.'),
}


IDEA_SEEDS: list[IdeaSeed] = [
    IdeaSeed('Agente de compliance documental para pequenas factoring/FIDC', 'Sistema que transforma contratos, comprovantes e documentos soltos em pacotes auditáveis prontos para operação.', 'infraestrutura invisível', 6, 6, 8, 3, 7, 9, 8, True, 'Operações financeiras pequenas seguem quebradas em WhatsApp, PDF e planilha.', 'Vender como implantação + mensalidade por mesa operacional.', ('doc_generation', 'cash_pressure', 'aged_niches'), 8),
    IdeaSeed('Radar de editais e compras recorrentes ultra-nicho', 'Motor que detecta licitações repetitivas e gera alertas acionáveis para fornecedores de nicho.', 'dados + recorrência', 7, 7, 8, 3, 6, 8, 8, True, 'Muitos fornecedores perdem receita por não monitorar fontes fragmentadas.', 'Cobrar assinatura mensal por vertical específica.', ('ops_automation', 'aged_niches'), 7),
    IdeaSeed('Copiloto de propostas B2B técnicas', 'Ferramenta que monta proposta, escopo e precificação para empresas técnicas que ainda vendem no improviso.', 'IA B2B', 8, 7, 7, 3, 5, 8, 8, False, 'Empresas pequenas estão cortando equipe comercial e precisam padronizar venda consultiva.', 'Começar por um nicho: energia solar, TI gerenciada, manutenção industrial.', ('ops_automation', 'team_reduction'), 6),
    IdeaSeed('Agente de cobrança preventiva para PMEs', 'Sistema que analisa carteira, gera follow-ups, segmenta risco e produz régua de cobrança automática.', 'automação operacional', 8, 8, 8, 4, 5, 9, 9, False, 'Fluxo de caixa apertado aumenta demanda por eficiência em contas a receber.', 'Cobrança setup + assinatura mensal pequena.', ('cash_pressure', 'ops_automation', 'team_reduction'), 9),
    IdeaSeed('Micro-SaaS de dossiê financeiro para M&A de pequeno porte', 'Gera data room mínimo e leitura executiva a partir de extratos, DRE e contratos.', 'micro SaaS', 5, 5, 9, 5, 7, 8, 7, True, 'Pequenos deals precisam de organização e ninguém quer pagar boutique cara no começo.', 'Produto com onboarding assistido e exportação PDF/XLSX.', ('doc_generation', 'bi_simplified'), 7),
    IdeaSeed('Normalizador de cadastros e documentos para revendas B2B', 'Toma formulários, certidões e dados fiscais caóticos e devolve cadastro limpo e pronto para ERP/CRM.', 'backoffice invisível', 8, 8, 7, 2, 4, 9, 8, True, 'Revendas e distribuidores sofrem com retrabalho cadastral.', 'Entrar via operação de crédito, supply ou vendas internas.', ('doc_generation', 'ops_automation', 'aged_niches'), 7),
    IdeaSeed('Motor de pricing e margem para distribuidores pequenos', 'Planilha inteligente/API leve que recalcula preço ideal, margem mínima e alerta erosão.', 'ferramenta financeira', 6, 6, 8, 4, 6, 8, 7, True, 'Distribuidores têm preço ruim e pouca inteligência operacional.', 'Vender como consultoria-produto com assinatura de atualização.', ('cash_pressure', 'bi_simplified', 'aged_niches'), 6),
    IdeaSeed('Agente de onboarding documental para creators/agências UGC', 'Organiza briefing, contrato, entrega, aceite e cobrança com forte automação.', 'creator infrastructure', 7, 8, 7, 4, 4, 9, 7, False, 'Creators usando IA precisam mais operação do que conteúdo.', 'Distribuição via comunidades de creators e assessorias.', ('creator_ai', 'ops_automation', 'doc_generation'), 5),
    IdeaSeed('Curadoria automatizada de oportunidades fiscais/financeiras por CNAE', 'Entrega alertas por setor sobre benefícios, mudanças e riscos operacionais.', 'inteligência setorial', 5, 7, 8, 3, 7, 8, 7, True, 'Setores envelhecidos continuam desinformados e mal digitalizados.', 'Começar com 1-2 CNAEs onde a dor é financeira.', ('aged_niches', 'cash_pressure'), 6),
    IdeaSeed('Sistema white-label de intake para escritórios consultivos', 'Portal + automação para captar dados do cliente sem retrabalho de WhatsApp.', 'white-label B2B', 7, 7, 7, 2, 5, 9, 8, False, 'Todo escritório pequeno quer parecer software sem desenvolver software.', 'Cobrar setup e mensalidade por carteira.', ('ops_automation', 'doc_generation', 'team_reduction'), 7),
    IdeaSeed('Observabilidade de SLA para micro operadores logísticos', 'Painel que puxa planilhas/emails e mostra gargalos por cliente, atraso e margem.', 'BI simplificado', 6, 5, 7, 4, 6, 8, 6, True, 'Transportadoras pequenas ainda operam sem visibilidade.', 'Produto semi-serviço com templates por operação.', ('bi_simplified', 'aged_niches', 'ops_automation'), 5),
    IdeaSeed('Revenda técnica de IA local para times sensíveis a dados', 'Empacotar LM Studio/Ollama/flows locais para jurídico, financeiro e RH.', 'IA local', 4, 4, 9, 6, 8, 7, 6, True, 'A demanda existe, mas vendas são mais lentas e consultivas.', 'Entrar com pacote fechado e caso de uso restrito.', ('ai_local', 'team_reduction'), 5),
    IdeaSeed('Mercado de datasets operacionais ultra-nicho', 'Coletar e estruturar bases pouco exploradas para times comerciais/financeiros.', 'dados', 5, 5, 9, 5, 8, 8, 6, True, 'Dados fragmentados ainda valem dinheiro quando entregues prontos.', 'Começar com uma base que resolva lead, risco ou monitoramento.', ('bi_simplified', 'ops_automation'), 6),
    IdeaSeed('Agente de renovação e reajuste contratual', 'Lê contratos recorrentes e avisa janelas de reajuste, vencimento e cláusulas perdidas.', 'recorrência B2B', 7, 7, 8, 3, 6, 9, 8, True, 'Empresas perdem margem por não executar reajustes.', 'Setup rápido com importação manual de contratos-chave.', ('cash_pressure', 'doc_generation', 'ops_automation'), 8),
    IdeaSeed('Motor de documentação automática para operações de crédito/serviços', 'Gera minuta, checklist, aceite e dossiê com base em formulários simples.', 'document automation', 8, 7, 8, 3, 6, 9, 9, False, '2026 tende a premiar automação documental e eficiência com time reduzido.', 'Produto estreito por vertical, cobrando mensalidade.', ('doc_generation', 'ops_automation', 'team_reduction', 'cash_pressure'), 9),
    IdeaSeed('Dropshipping genérico', 'Modelo saturado de catálogo indiferenciado.', 'genérico', 5, 6, 5, 8, 1, 3, 2, False, 'Concorrência brutal e dependência de mídia.', 'Não recomendado.', tuple(), 0, 'Saturado, baixo moat, margem apertada e dependente de tráfego pago.'),
    IdeaSeed('PLR genérico + afiliado comum', 'Empilhar infoproduto genérico sem vantagem real.', 'genérico', 6, 7, 4, 8, 1, 5, 2, False, 'Mercado cansado e pouca diferenciação.', 'Não recomendado.', tuple(), 0, 'Baixa barreira, oferta cansada e retenção fraca.'),
    IdeaSeed('Agência de social media comum', 'Serviço operacional sem alavancagem suficiente.', 'serviço tradicional', 7, 5, 4, 6, 2, 4, 3, False, 'Troca direta de tempo por dinheiro.', 'Não recomendado.', tuple(), 0, 'Escala ruim para 2h/dia e difícil chegar a semi-passivo.'),
    IdeaSeed('POD básico', 'Produto comoditizado sem distribuição forte.', 'genérico', 4, 8, 4, 7, 1, 4, 2, False, 'Concorrência alta e LTV fraco.', 'Não recomendado.', tuple(), 0, 'Baixo efeito multiplicador e pouco controle de demanda.'),
    IdeaSeed('Arbitragem de revenda técnica de templates operacionais com automação', 'Pacotes prontos de operação para nichos que precisam de proposta, cobrança, intake e documentos.', 'arbitragem digital', 8, 8, 7, 2, 5, 9, 8, True, 'Pequenas empresas compram aceleração operacional se economizar retrabalho.', 'Vender asset + setup leve + upsell recorrente.', ('ops_automation', 'doc_generation', 'aged_niches'), 8),
]


def infer_market_signals(request: StrategyAnalysisRequest) -> list[str]:
    inferred: list[str] = []
    profile = request.profile.lower()
    scope = request.market_scope.lower()
    if request.prioritize_automation:
        inferred.append('ops_automation')
    if request.prioritize_recurrence:
        inferred.append('cash_pressure')
    if 'creator' in profile:
        inferred.append('creator_ai')
    if any(word in profile for word in ('finance', 'financeiro', 'cobran', 'caixa', 'bpo')):
        inferred.append('cash_pressure')
        inferred.append('doc_generation')
    if any(word in profile for word in ('consult', 'solo', 'executor')):
        inferred.append('team_reduction')
    if any(word in scope for word in ('brasil', 'b2b', 'industrial', 'tradicional')):
        inferred.append('aged_niches')
    return list(dict.fromkeys(inferred))


def _signal_bonus(seed: IdeaSeed, active_signals: list[str]) -> int:
    bonus = 0
    for signal_key in active_signals:
        signal = MARKET_SIGNALS.get(signal_key)
        if signal and signal_key in seed.tags:
            bonus += signal.weight
    return bonus


def _asymmetry_score(seed: IdeaSeed, active_signals: list[str] | None = None, request: StrategyAnalysisRequest | None = None) -> int:
    active_signals = active_signals or []
    request = request or StrategyAnalysisRequest()
    score = (seed.speed * 0.16) + (seed.ease * 0.12) + (seed.scale * 0.2) + ((10 - seed.risk) * 0.18) + (seed.automation * 0.18) + (seed.realism * 0.16) + seed.asymmetry_bonus
    if request.prioritize_automation and 'ops_automation' in seed.tags:
        score += 1.4
    if request.prioritize_recurrence and ('cash_pressure' in seed.tags or 'doc_generation' in seed.tags):
        score += 1.1
    if request.max_hours_per_day <= 2 and seed.ease >= 7:
        score += 1.2
    score += _signal_bonus(seed, active_signals)
    return int(round(score))


def _idea_to_schema(seed: IdeaSeed, active_signals: list[str], request: StrategyAnalysisRequest) -> OpportunityIdea:
    return OpportunityIdea(
        name=seed.name,
        summary=seed.summary,
        speed_of_return=seed.speed,
        operational_ease=seed.ease,
        scale_potential=seed.scale,
        risk_level=seed.risk,
        barrier_to_entry=seed.barrier,
        automation_fit=seed.automation,
        realistic_20k_score=seed.realism,
        asymmetry_score=_asymmetry_score(seed, active_signals, request),
        hidden=seed.hidden,
        category=seed.category,
        why_now=seed.why_now,
        execution_hint=seed.execution_hint,
        eliminate_reason=seed.eliminate_reason,
    )


def _top5(active_signals: list[str], request: StrategyAnalysisRequest) -> list[IdeaSeed]:
    viable = [seed for seed in IDEA_SEEDS if seed.eliminate_reason is None]
    return sorted(viable, key=lambda item: (_asymmetry_score(item, active_signals, request), item.realism, item.automation), reverse=True)[:5]


def _deep(seed: IdeaSeed, rank: int, active_signals: list[str]) -> DeepOpportunity:
    signal_labels = [MARKET_SIGNALS[key].label for key in active_signals if key in seed.tags and key in MARKET_SIGNALS]
    signal_suffix = f" Sinais puxando esta tese agora: {', '.join(signal_labels)}." if signal_labels else ''
    start_map = {
        'Agente de cobrança preventiva para PMEs': [
            'Reservar ~R$700 para landing simples, domínio e stack.',
            'Usar ~R$600 para outreach altamente segmentado e prospecção assistida.',
            'Usar ~R$1.200 como caixa de runway, demos e pequenos ajustes de implantação.',
        ],
        'Motor de documentação automática para operações de crédito/serviços': [
            'Separar R$500 para identidade e página clara da oferta.',
            'Investir R$700 em stack/no-code/API e assinatura curta de OCR/automação.',
            'Preservar o resto como caixa para iterações e aquisição de primeiros clientes.',
        ],
        'Agente de compliance documental para pequenas factoring/FIDC': [
            'Validar com 5 operações pequenas antes de codar demais.',
            'Montar MVP com formulários, parsing, checklist e geração de dossiê.',
            'Guardar parte do caixa para ajustes por cliente e assinatura de OCR/LLM.',
        ],
    }
    generic_start = [
        'Gastar pouco em estética e muito em prova de valor.',
        'Comprar apenas stack essencial e preservar caixa para distribuição.',
        'Fechar primeiro cliente antes de ampliar escopo do produto.',
    ]
    first_customers = {
        'Agente de cobrança preventiva para PMEs': ['contadores com carteira PME', 'consultores financeiros fracionados', 'pequenas distribuidoras', 'escritórios BPO financeiro'],
        'Motor de documentação automática para operações de crédito/serviços': ['factoring pequenas', 'correspondentes bancários', 'consultorias financeiras', 'empresas de serviços recorrentes com onboarding pesado'],
        'Agente de compliance documental para pequenas factoring/FIDC': ['FIDCs pequenos', 'fundos boutique', 'factorings regionais', 'operações de crédito privado enxutas'],
        'Arbitragem de revenda técnica de templates operacionais com automação': ['consultorias nichadas', 'revendas B2B', 'escritórios financeiros', 'times comerciais técnicos'],
        'Agente de renovação e reajuste contratual': ['BPOs', 'software houses pequenas', 'escritórios de facilities', 'prestadores com contratos anuais'],
    }
    revenue = {
        'Agente de cobrança preventiva para PMEs': ('R$2k–5k', 'R$5k–9k', 'R$9k–15k', 'R$18k–35k'),
        'Motor de documentação automática para operações de crédito/serviços': ('R$1k–4k', 'R$4k–8k', 'R$8k–14k', 'R$16k–30k'),
        'Agente de compliance documental para pequenas factoring/FIDC': ('R$0–3k', 'R$4k–8k', 'R$8k–16k', 'R$20k–40k'),
        'Arbitragem de revenda técnica de templates operacionais com automação': ('R$2k–4k', 'R$4k–8k', 'R$8k–12k', 'R$12k–22k'),
        'Agente de renovação e reajuste contratual': ('R$1k–3k', 'R$3k–6k', 'R$6k–11k', 'R$12k–24k'),
    }
    r30, r60, r90, r180 = revenue.get(seed.name, ('R$0–2k', 'R$2k–5k', 'R$5k–10k', 'R$10k–20k'))
    return DeepOpportunity(
        rank=rank,
        name=seed.name,
        thesis=f'{seed.summary} A tese é vender redução de caos operacional, não tecnologia pela tecnologia.{signal_suffix}',
        why_it_wins='Combina dor financeira clara, alto potencial de automação e possibilidade real de recorrência com pouco capital.',
        how_to_start_with_2500=start_map.get(seed.name, generic_start),
        structure_needed=['oferta estreita por nicho', 'landing objetiva com promessa mensurável', 'workflow automatizado mínimo', 'playbook de onboarding e entrega'],
        tools=['FastAPI', 'SQLite/Postgres', 'n8n ou scripts Python', 'OCR/LLM quando necessário', 'email outbound e planilha CRM enxuta'],
        daily_time_real='60–120 min/dia: 30–45 min distribuição, 30 min melhoria do motor, 15–30 min suporte/onboarding.',
        where_the_money_is='No ganho de eficiência mensurável, no setup inicial e na assinatura mensal de continuidade.',
        how_to_scale='Transformar serviço inicial em fluxo padronizado, reduzir customização, empacotar por vertical e aumentar distribuição via parceiros.',
        main_risks=['falar com nicho errado', 'customização excessiva', 'ciclo comercial mais longo que o caixa suporta'],
        risk_reduction=['focar vertical com dor financeira aguda', 'vender escopo fechado', 'validar 5 conversas antes de expandir funcionalidades'],
        first_customers=first_customers.get(seed.name, ['consultores nichados', 'operadores financeiros pequenos', 'BPOs', 'times comerciais enxutos']),
        revenue_30d=r30,
        revenue_60d=r60,
        revenue_90d=r90,
        revenue_180d=r180,
        automate_first=['qualificação inbound/outbound', 'geração de proposta', 'onboarding inicial', 'relatórios e entregáveis repetitivos'],
        kill_fast_if=['ninguém pagar pelo setup', 'dor percebida sem urgência financeira', 'cada cliente pedir um produto diferente', 'ciclo de venda exigir presença comercial pesada'],
    )


def analyze_strategy(request: StrategyAnalysisRequest) -> StrategyAnalysisResponse:
    active_signals = list(dict.fromkeys((request.market_signals or []) + infer_market_signals(request)))
    ideas = [_idea_to_schema(seed, active_signals, request) for seed in IDEA_SEEDS]
    top5_seeds = _top5(active_signals, request)
    top5 = [_deep(seed, index + 1, active_signals) for index, seed in enumerate(top5_seeds)]
    matrix = OpportunityMatrix(
        low_risk_high_scale=['Agente de cobrança preventiva para PMEs', 'Motor de documentação automática para operações de crédito/serviços', 'Agente de renovação e reajuste contratual'],
        low_risk_low_scale=['Normalizador de cadastros e documentos para revendas B2B', 'Copiloto de propostas B2B técnicas'],
        high_risk_high_scale=['Revenda técnica de IA local para times sensíveis a dados', 'Mercado de datasets operacionais ultra-nicho', 'Micro-SaaS de dossiê financeiro para M&A de pequeno porte'],
        hidden_opportunities=['Agente de compliance documental para pequenas factoring/FIDC', 'Radar de editais e compras recorrentes ultra-nicho', 'Arbitragem de revenda técnica de templates operacionais com automação'],
    )
    winner_seed = top5_seeds[0]
    winner = StrategyWinner(
        name=winner_seed.name,
        why_it_wins=f'Vence nesta configuração porque combina melhor score assimétrico com os sinais ativos: {", ".join(MARKET_SIGNALS[key].label for key in active_signals if key in winner_seed.tags) or "nenhum sinal específico"}.',
        why_others_lose=[
            'IA local pode ser ótima, mas costuma exigir venda mais lenta e mais confiança técnica.',
            'Datasets têm potencial, porém distribuição e monetização inicial costumam demorar mais.',
            'Templates puros podem vender rápido, mas perdem força se o nicho não tiver dor financeira explícita.',
            'Teses boas demais para compliance/financeiro podem travar quando o comprador é excessivamente conservador.',
        ],
        best_execution_path=[
            'Escolher 1 vertical onde os sinais ativos são mais fortes.',
            'Construir oferta estreita com promessa econômica explícita.',
            'Fechar pilotos pagos antes de sofisticar demais o produto.',
            'Padronizar onboarding e entrega logo após os 2-3 primeiros clientes.',
            'Aumentar distribuição via parceiros do nicho, não via volume genérico.',
        ],
        real_bottleneck='Distribuição qualificada em cima de dor econômica atual, não engenharia.',
        common_mistakes=['vender ferramenta em vez de ganho', 'ignorar sinais do mercado na escolha do nicho', 'customizar antes de validar', 'misturar muitas verticais cedo demais'],
        operating_in_2h=['trabalhar um nicho por vez', 'usar outreach curto e repetível', 'automatizar proposta/onboarding/relatório primeiro', 'revisar semanalmente sinais que alteram a prioridade'],
    )
    implementation_plan = [
        'Semana 1: travar nicho, promessa e sinais que justificam a tese.',
        'Semana 2: lançar landing, demo e endpoint de análise com sinais explícitos.',
        'Semana 3: prospectar 30-50 contas/parceiros do nicho priorizado.',
        'Semana 4: fechar 1-2 pilotos pagos e medir fricção real.',
        'Mês 2: padronizar entrega e reduzir customização.',
        'Mês 3+: transformar setup em produto recorrente e abrir segundo canal de distribuição.',
    ]
    signal_labels = [MARKET_SIGNALS[key].label for key in active_signals if key in MARKET_SIGNALS]
    framing = (
        f'Análise construída para sair de R${request.available_capital_brl:,.0f} para pelo menos '
        f'R${request.target_brl:,.0f} {request.end_horizon}, com no máximo {request.max_hours_per_day:g}h/dia, '
        f'priorizando ativos, automação, recorrência e nichos não óbvios. Sinais aplicados: {", ".join(signal_labels) or "nenhum"}.'
    ).replace(',', '.')
    return StrategyAnalysisResponse(
        framing=framing,
        ideas=sorted(ideas, key=lambda item: (item.eliminate_reason is None, item.asymmetry_score), reverse=True),
        top5=top5,
        matrix=matrix,
        winner=winner,
        implementation_plan=implementation_plan,
    )
