def test_generate_executive_lead_and_ranking(client):
    company = client.post('/companies', json={
        'legal_name': 'Distribuidora Modelo S/A',
        'trade_name': 'Distribuidora Modelo',
        'sector': 'distribuidora',
        'city': 'Contagem',
        'state': 'MG',
        'estimated_size': 'medium',
        'website': 'https://distribuidoramodelo.com.br'
    }).json()
    company_id = company['id']

    raw_event = client.post('/raw-events', json={
        'source_name': 'Notícias Regionais',
        'source_url': 'https://distribuidoramodelo.com.br/expansao',
        'title': 'Distribuidora Modelo expande CD',
        'content': 'Distribuidora Modelo anuncia novo centro de distribuição em Contagem.',
        'company_name_raw': 'Distribuidora Modelo',
        'company_website_raw': 'https://distribuidoramodelo.com.br',
        'city_raw': 'Contagem',
        'state_raw': 'MG',
        'confidence': 0.9
    }).json()
    normalized = client.post(f"/raw-events/{raw_event['id']}/normalize")
    assert normalized.status_code == 200
    assert normalized.json()['match_confidence'] is not None

    for signal in [
        {'company_id': company_id, 'category': 'finance', 'signal_type': 'financial_restructuring', 'source_name': 'JusBrasil', 'source_url': 'https://legal/1', 'excerpt': 'reestruturacao', 'confidence': 0.92},
        {'company_id': company_id, 'category': 'legal', 'signal_type': 'judicial_recovery_signal', 'source_name': 'JusBrasil', 'source_url': 'https://legal/2', 'excerpt': 'rj', 'confidence': 0.95},
        {'company_id': company_id, 'category': 'operations', 'signal_type': 'new_distribution_center', 'source_name': 'Notícias Regionais', 'source_url': 'https://news/1', 'excerpt': 'novo cd', 'confidence': 0.88},
    ]:
        assert client.post('/signals', json=signal).status_code == 200

    lead = client.post(f'/leads/generate/{company_id}')
    assert lead.status_code == 200
    assert lead.json()['lead_tier'] == 'A'
    assert 'match_adjustment=' in lead.json()['score_explanation']

    executive = client.get(f'/leads/{company_id}/executive')
    assert executive.status_code == 200
    body = executive.json()
    assert body['empresa'] == 'Distribuidora Modelo'
    assert body['produto_mais_indicado']
    assert body['eixos_de_evidencia']
    assert 'legal' in body['eixos_de_evidencia']
    assert body['motivos_do_score']
    assert body['qualidade_match'] in {'alta', 'média', 'baixa', 'desconhecida'}

    ranking = client.get('/leads/ranking?min_score=60')
    assert ranking.status_code == 200
    assert ranking.json()['total'] == 1
    assert ranking.json()['items'][0]['company_id'] == company_id
    assert ranking.json()['items'][0]['qualidade_match'] in {'alta', 'média', 'baixa', 'desconhecida'}
