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
- Alembic para migrações

## Estrutura
- `app/api`: rotas HTTP
- `app/core`: configuração
- `app/db`: modelos e sessão
- `app/services`: regra de negócio
- `app/schemas`: contratos da API
- `app/data`: taxonomias e pesos iniciais
- `alembic`: migrações de banco

## Rodando localmente
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/migrate.py
uvicorn app.main:app --reload
```

## Endpoints atuais
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
- aplica bônus multi-fonte entre jobs, notícias e jurídico
- resolve empresa por CNPJ, domínio/site, nome e contexto geográfico

## Endpoints adicionais
- `POST /companies/match`
- `GET /leads/ranking`
- `GET /leads/ranking/export`
- `GET /leads/{company_id}/executive/export`
- `POST /providers/generic-html-jobs/collect`
- `POST /providers/gupy-jobs/collect`
- `POST /providers/greenhouse-jobs/collect`
- `POST /providers/json-jobs/collect`
- `POST /providers/jsonld-jobs/collect`
- `POST /providers/generic-html-news/collect`
- `POST /providers/generic-html-legal/collect`
- `GET /watchlists`
- `POST /watchlists`
- `POST /watchlists/{id}/run`
- `GET /watchlists/{id}/runs`
- `POST /watchlists/run-due`

## Coleta via provider HTML genérico
Esse provider permite apontar para uma página HTML com vagas e informar seletores CSS para extrair:
- bloco da vaga
- título
- conteúdo
- empresa
- cidade/UF
- link da vaga
- site da empresa

## Coleta via adapter Gupy
Esse adapter faz uma leitura mais específica de páginas de vagas em padrão Gupy/semelhante, servindo como primeiro passo para conectores menos genéricos e mais precisos.

Endpoint:
- `POST /providers/gupy-jobs/collect`

## Coleta via adapter Greenhouse
Esse adapter faz leitura específica de páginas no padrão Greenhouse/boards corporativos, com extração básica de vaga e localização.

Endpoint:
- `POST /providers/greenhouse-jobs/collect`

## Coleta via adapter Lever
Esse adapter faz leitura específica de páginas no padrão Lever, com extração básica de vaga, localização e identificação da empresa pela URL.

Endpoint:
- `POST /providers/lever-jobs/collect`

## Coleta via adapter Workday
Esse adapter faz leitura específica de páginas no padrão Workday-like, com extração básica de vaga, localização e identificação da empresa pela URL.

Endpoint:
- `POST /providers/workday-jobs/collect`

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

## Coleta via provider JSON-LD
Esse provider extrai vagas de páginas que publicam `JobPosting` em `application/ld+json`, comum em páginas corporativas de carreira.

## Coleta via provider de notícias
Esse provider permite capturar notícias em HTML e transformá-las em sinais operacionais, como:
- nova filial
- novo centro de distribuição
- expansão geográfica
- crescimento acelerado
- ampliação de frota

## Coleta via provider jurídico
Esse provider permite capturar eventos jurídicos em HTML e transformá-los em sinais como:
- execução
- ação de cobrança
- trabalhistas
- recuperação judicial
- reestruturação financeira

Útil para enriquecer o radar além de vagas.

## Watchlists
O sistema suporta watchlists persistidas para salvar configurações de coleta e executá-las sob demanda.

Cada watchlist guarda:
- tipo de fonte
- nome da fonte
- configuração JSON do coletor
- status ativo/inativo
- frequência em minutos (`schedule_minutes`)
- timestamp da última execução

Ao executar uma watchlist, o sistema agora:
1. coleta eventos
2. normaliza os sinais
3. identifica empresas impactadas
4. gera snapshots de lead automaticamente
5. atualiza o ranking operacional
6. grava histórico de execução com status, eventos, leads e empresas impactadas

Para execução operacional fora da API:
```bash
python scripts/run_due_watchlists.py
bash scripts/run_due_watchlists_once.sh
```

Exemplo de cron:
```bash
cat deploy/cron.example
```

## Exportação
O sistema suporta exportação de:
- ranking em JSON/CSV
- lead executivo em JSON/CSV

Via scripts:
```bash
python scripts/export_ranking.py --format csv --output exports/ranking.csv
python scripts/export_executive_lead.py 1 --format json --output exports/lead-1.json
```

## Webhooks
O sistema suporta targets de webhook para entrega automática ou manual de leads priorizados.

Quando um novo lead snapshot é gerado, o sistema tenta entregar automaticamente para webhook targets ativos e elegíveis pelo critério de score/tier.

Endpoints:
- `GET /webhooks`
- `POST /webhooks`
- `GET /webhooks/{id}/deliveries`
- `POST /webhooks/{id}/dispatch-latest`
- `POST /webhooks/{id}/dispatch/{company_id}`

## Migrações
O schema agora é gerido por Alembic.

Aplicar migrações:
```bash
python scripts/migrate.py
```

Validar schema local:
```bash
python scripts/check_migrations.py
```

Sempre que novas tabelas/colunas forem adicionadas ao domínio, uma nova revisão Alembic deve acompanhar a mudança.

## Testes
Rodar a suíte inicial:
```bash
pytest -q
```

Cobertura inicial inclui:
- geração de lead executivo e ranking
- watchlists com geração automática de leads
- auto-dispatch de webhooks
- adapter Gupy básico
- adapters Greenhouse, Lever e Workday

## Próximos passos
1. criar adapters específicos adicionais por fonte real
2. ampliar entity resolution com similaridade/fuzzy score
3. painel operacional de monitoramento
4. testes automatizados mais abrangentes
5. observabilidade e alertas operacionais
6. retry/idempotência de webhook
