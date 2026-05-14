from sqlalchemy import text


def test_executive_endpoint_accepts_legacy_payload(client):
    company = client.post('/companies', json={
        'legal_name': 'Legacy Payload S/A',
        'trade_name': 'Legacy Payload',
        'sector': 'distribuidora',
        'city': 'Belo Horizonte',
        'state': 'MG',
        'estimated_size': 'medium',
        'website': 'https://legacypayload.com.br'
    }).json()
    company_id = company['id']

    client.post('/signals', json={
        'company_id': company_id,
        'category': 'operations',
        'signal_type': 'new_branch',
        'source_name': 'Notícias Regionais',
        'source_url': 'https://news/legacy',
        'excerpt': 'nova filial',
        'confidence': 0.9
    })
    client.post(f'/leads/generate/{company_id}')

    legacy_json = '{"company_id": %d, "empresa": "Legacy Payload", "setor": "distribuidora", "localizacao": "Belo Horizonte/MG", "porte_estimado": "medium", "score_necessidade_capital": 70.0, "probabilidade_conversao": "alta", "score_bucket": "alta probabilidade", "principais_sinais_detectados": ["new_branch"], "contexto_operacional": "ctx", "hipotese_de_dor": "dor", "melhor_abordagem_comercial": "abordagem", "produto_mais_indicado": "produto", "timing_ideal_de_abordagem": "agora", "risco": "médio", "contatos_encontrados": [], "fontes_utilizadas": ["Notícias Regionais"], "confianca_do_lead": "média", "evidencias": ["ev1"], "resumo_executivo": "resumo", "criado_em": "2026-05-14T12:00:00"}' % company_id

    client.app.dependency_overrides = getattr(client.app, 'dependency_overrides', {})
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        db.execute(text("UPDATE lead_snapshots SET executive_payload = :payload WHERE company_id = :company_id"), {"payload": legacy_json, "company_id": company_id})
        db.commit()
    finally:
        db.close()

    executive = client.get(f'/leads/{company_id}/executive')
    assert executive.status_code == 200
    body = executive.json()
    assert body['empresa'] == 'Legacy Payload'
    assert body['eixos_de_evidencia'] == []
    assert body['motivos_do_score'] == []
    assert body['qualidade_match'] == 'desconhecida'
