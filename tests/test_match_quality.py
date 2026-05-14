def test_low_match_quality_penalizes_lead_score(client):
    company = client.post('/companies', json={
        'legal_name': 'Baixa Qualidade Match Ltda',
        'trade_name': 'Baixa Match',
        'sector': 'transportadora',
        'city': 'Campinas',
        'state': 'SP',
        'estimated_size': 'medium',
        'website': 'https://baixamatch.com.br'
    }).json()
    company_id = company['id']

    raw_event = client.post('/raw-events', json={
        'source_name': 'Notícias Regionais',
        'source_url': 'https://portal-externo.com/noticia-1',
        'title': 'Baixa Operações expande operação',
        'content': 'Empresa expande operação em Campinas.',
        'company_name_raw': 'Baixa Operações',
        'company_website_raw': 'https://portal-externo.com',
        'city_raw': 'Campinas',
        'state_raw': 'SP',
        'confidence': 0.8
    }).json()

    normalized = client.post(f"/raw-events/{raw_event['id']}/normalize")
    assert normalized.status_code == 200
    assert normalized.json()['match_confidence'] is not None
    assert normalized.json()['match_confidence'] < 1.0

    for signal in [
        {'company_id': company_id, 'category': 'operations', 'signal_type': 'new_branch', 'source_name': 'Notícias Regionais', 'source_url': 'https://news/1', 'excerpt': 'nova filial', 'confidence': 0.88},
        {'company_id': company_id, 'category': 'finance', 'signal_type': 'treasury_hiring', 'source_name': 'LinkedIn Jobs', 'source_url': 'https://jobs/1', 'excerpt': 'tesouraria', 'confidence': 0.83},
    ]:
        assert client.post('/signals', json=signal).status_code == 200

    lead = client.post(f'/leads/generate/{company_id}')
    assert lead.status_code == 200
    body = lead.json()
    assert 'match_adjustment=' in body['score_explanation']
    assert 'match_quality=medium' in body['score_explanation'] or 'match_quality=low' in body['score_explanation']
