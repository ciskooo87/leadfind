# LeadFind

Radar de Empresas com Necessidade de Capital de Giro.

## Objetivo
Detectar empresas brasileiras com alta probabilidade de necessidade de capital de giro, antecipação de recebíveis, fomento mercantil, reestruturação financeira, troca de ERP financeiro e ganho de eficiência operacional.

## MVP inicial
Este repositório começa com um backend FastAPI focado em:
- cadastro e enriquecimento de empresas
- ingestão de sinais públicos
- motor de score explicável
- priorização de oportunidades
- geração de lead estruturado

## Stack
- Python 3.12+
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite para desenvolvimento inicial

## Estrutura
- `app/api`: rotas HTTP
- `app/core`: configuração
- `app/db`: modelos e sessão
- `app/services`: regra de negócio
- `app/schemas`: contratos da API
- `app/data`: taxonomias e pesos iniciais

## Rodando localmente
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Endpoints iniciais
- `GET /health`
- `POST /companies`
- `POST /signals`
- `POST /leads/generate/{company_id}`
- `GET /leads/{company_id}`

## Próximos passos
1. adicionar migrações
2. conectar fontes reais
3. criar deduplicação por CNPJ raiz/domínio
4. criar fila de coleta
5. exportação para CRM/webhooks
