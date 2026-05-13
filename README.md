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

## Endpoints atuais
- `GET /health`
- `GET /sources`
- `POST /companies`
- `POST /signals`
- `POST /raw-events`
- `POST /raw-events/{raw_event_id}/normalize`
- `POST /leads/generate/{company_id}`
- `GET /leads/{company_id}`

## Pipeline atual do MVP
1. cadastrar empresa
2. registrar evento bruto vindo de uma fonte pública
3. normalizar o evento bruto
4. inferir um ou mais sinais de intenção
5. gerar lead com score explicável

## Importação em lote de vagas
Via API:
```bash
POST /raw-events/batch
```

Via script:
```bash
python scripts/import_jobs.py sample_jobs.jsonl
```

Formato JSONL esperado: um evento por linha, com pelo menos:
- `source_name`
- `content`

## Regras atuais do pipeline
- evita reimportar `raw_events` duplicados por `source + external_id`
- evita criar `signals` repetidos da mesma evidência
- aplica peso de recência no score
- adiciona bônus por evidência recente cruzada
- resolve empresa por CNPJ, domínio/site, nome e contexto geográfico

## Endpoints adicionais
- `POST /companies/match`
- `POST /providers/generic-html-jobs/collect`
- `POST /providers/json-jobs/collect`

## Coleta via provider HTML genérico
Esse provider permite apontar para uma página HTML com vagas e informar seletores CSS para extrair:
- bloco da vaga
- título
- conteúdo
- empresa
- cidade/UF
- link da vaga
- site da empresa

## Coleta via provider JSON
Esse provider permite consumir feeds estruturados em JSON, informando paths como:
- lista de itens
- título
- descrição
- empresa
- cidade/UF
- URL da vaga
- site da empresa
- ID externo

Útil para integrações mais estáveis do que scraping HTML.

## Próximos passos
1. adicionar migrações
2. criar adapters específicos por fonte real
3. criar fila de coleta e normalização
4. exportação para CRM/webhooks
5. ampliar entity resolution com similaridade/fuzzy score
6. plugar fontes reais de vagas e notícias
