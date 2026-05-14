def test_raw_event_normalization_persists_match_audit(client):
    company = client.post('/companies', json={
        'legal_name': 'Operadora Match Audit Ltda',
        'trade_name': 'Match Audit',
        'city': 'Campinas',
        'state': 'SP',
        'website': 'https://matchaudit.com.br',
        'aliases': ['Operadora MA'],
        'domains': ['careers.matchaudit.com.br']
    }).json()

    raw_event = client.post('/raw-events', json={
        'source_name': 'Notícias Regionais',
        'source_url': 'https://careers.matchaudit.com.br/noticia/1',
        'title': 'Operadora MA amplia operação',
        'content': 'Operadora MA anuncia nova filial e expansão operacional em Campinas.',
        'company_name_raw': 'Operadora MA',
        'company_website_raw': 'https://careers.matchaudit.com.br',
        'city_raw': 'Campinas',
        'state_raw': 'SP',
        'confidence': 0.81
    }).json()

    normalized = client.post(f"/raw-events/{raw_event['id']}/normalize")
    assert normalized.status_code == 200
    body = normalized.json()
    assert body['company_id'] == company['id']
    assert body['match_confidence'] is not None
    assert body['match_confidence'] >= 1.0
    assert body['match_explanation']
    assert 'domain_exact' in body['match_explanation'] or 'alias:' in body['match_explanation']
