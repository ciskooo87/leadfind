# Leadfind

Engine de inteligência de oportunidades para encontrar caminhos assimétricos de crescimento com pouco capital, baixo tempo operacional e forte alavancagem via automação, IA e recorrência.

## Objetivo atual
Transformar um briefing como:
- capital disponível
- meta financeira
- limite diário de tempo
- preferência por recorrência e automação
- aversão a ideias saturadas

em uma análise estruturada com:
- 20 oportunidades resumidas
- filtragem rápida de ideias ruins
- top 5 oportunidades com análise profunda
- matriz de risco × escala
- recomendação final única de melhor assimetria

## Produto atual no repo
O repositório agora entrega um MVP híbrido:

### 1. Strategy engine
Camada nova orientada à ideia original do projeto.

Endpoints:
- `GET /` → UI principal do motor estratégico
- `GET /strategy/ui` → alias da UI
- `POST /strategy/analyze` → análise estruturada em JSON

### 2. Legacy lead radar
O backend antigo de radar B2B foi preservado como base técnica e legado útil.
Ele continua existindo com recursos de:
- ingestão de sinais públicos
- scoring explicável
- ranking de leads
- watchlists
- webhooks

Isso permite reaproveitamento futuro de:
- coleta de sinais externos
- ranking
- exportação
- infraestrutura de backend

## Stack
- Python 3.12+
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite para desenvolvimento inicial
- Alembic para migrações

## Estrutura principal
- `app/api`: rotas HTTP
- `app/core`: configuração
- `app/db`: modelos e sessão
- `app/schemas`: contratos da API
- `app/services/strategy_engine.py`: motor estratégico
- `app/services`: serviços legados e utilidades

## Rodando localmente
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/migrate.py
uvicorn app.main:app --reload
```

## Exemplo de uso da análise estratégica
```bash
curl -X POST http://127.0.0.1:8000/strategy/analyze \
  -H 'content-type: application/json' \
  -d '{
    "available_capital_brl": 2500,
    "target_brl": 20000,
    "max_hours_per_day": 2,
    "market_scope": "Brasil + global",
    "profile": "executor solo orientado a ativos"
  }'
```

## O que a resposta entrega
- framing econômico da análise
- ideias priorizadas por assimetria
- top 5 detalhado
- projeção de receita por janela
- riscos e kill criteria
- matriz estratégica
- uma única recomendação vencedora

## Endpoints legados preservados
- `GET /health`
- `GET /sources`
- `POST /companies`
- `POST /signals`
- `POST /raw-events`
- `POST /raw-events/batch`
- `POST /raw-events/{raw_event_id}/normalize`
- `POST /leads/generate/{company_id}`
- `GET /leads/{company_id}`
- `GET /leads/{company_id}/executive`
- `GET /leads/ranking`
- `GET /leads/ranking/export`
- `GET /watchlists`
- `POST /watchlists`
- `GET /webhooks`
- `POST /webhooks`

## Estratégia de evolução
Próximos passos coerentes com a ideia original:
1. suportar perfis e teses por usuário
2. enriquecer oportunidades com sinais reais de mercado
3. criar templates por perfil (solo, consultor, operador, técnico)
4. conectar sinais externos para oportunidades em tempo real
5. transformar as melhores teses em playbooks executáveis
6. adicionar comparação lado a lado entre análises salvas

## Testes
Rodar a suíte:
```bash
pytest -q
```

Inclui agora cobertura do strategy engine.
des em tempo real
6. transformar as melhores teses em playbooks executáveis

## Testes
Rodar a suíte:
```bash
pytest -q
```

Inclui agora cobertura do strategy engine.
