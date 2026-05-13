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
- aplica bônus multi-fonte entre jobs, notícias e jurídico
- resolve empresa por CNPJ, domínio/site, nome e contexto geográfico

## Endpoints adicionais
- `POST /companies/match`
- `GET /leads/ranking`
- `POST /providers/generic-html-jobs/collect`
- `POST /providers/json-jobs/collect`
- `POST /providers/jsonld-jobs/collect`
- `POST /providers/generic-html-news/collect`
- `POST /providers/generic-html-legal/collect`
- `GET /watchlists`
- `POST /watchlists`
- `POST /watchlists/{id}/run`

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
- timestamp da última execução

Ao executar uma watchlist, o sistema agora:
1. coleta eventos
2. normaliza os sinais
3. identifica empresas impactadas
4. gera snapshots de lead automaticamente
5. atualiza o ranking operacional

## Próximos passos
1. adicionar migrações
2. criar adapters específicos por fonte real
3. criar fila/agenda de execução automática
4. exportação para CRM/webhooks
5. ampliar entity resolution com similaridade/fuzzy score
6. painel operacional de monitoramento
