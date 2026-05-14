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

    for signal in [
        {'company_id': company_id, 'category': 'finance', 'signal_type': 'financial_restructuring', 'source_name': 'JusBrasil', 'source_url': 'https://legal/1', 'excerpt': 'reestruturacao', 'confidence': 0.92},
        {'company_id': company_id, 'category': 'legal', 'signal_type': 'judicial_recovery_signal', 'source_name': 'JusBrasil', 'source_url': 'https://legal/2', 'excerpt': 'rj', 'confidence': 0.95},
        {'company_id': company_id, 'category': 'operations', 'signal_type': 'new_distribution_center', 'source_name': 'Notícias Regionais', 'source_url': 'https://news/1', 'excerpt': 'novo cd', 'confidence': 0.88},
    ]:
        assert client.post('/signals', json=signal).status_code == 200

    lead = client.post(f'/leads/generate/{company_id}')
    assert lead.status_code == 200
    assert lead.json()['lead_tier'] == 'A'

    executive = client.get(f'/leads/{company_id}/executive')
    assert executive.status_code == 200
    body = executive.json()
    assert body['empresa'] == 'Distribuidora Modelo'
    assert body['produto_mais_indicado']
    assert body['eixos_de_evidencia']
    assert 'legal' in body['eixos_de_evidencia']
    assert body['motivos_do_score']

    ranking = client.get('/leads/ranking?min_score=60')
    assert ranking.status_code == 200
    assert ranking.json()['total'] == 1
    assert ranking.json()['items'][0]['company_id'] == company_id
