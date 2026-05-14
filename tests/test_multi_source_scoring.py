def test_multi_source_scoring_with_reputation_legal_news(client):
    company = client.post('/companies', json={
        'legal_name': 'Trans Exemplo Ltda',
        'trade_name': 'Trans Exemplo',
        'sector': 'transportadora',
        'city': 'Campinas',
        'state': 'SP',
        'estimated_size': 'medium',
        'website': 'https://transexemplo.com.br'
    }).json()
    company_id = company['id']

    for signal in [
        {'company_id': company_id, 'category': 'operations', 'signal_type': 'delivery_delay_complaints', 'source_name': 'Reclamações Operacionais', 'source_url': 'https://complaints/1', 'excerpt': 'atraso de entrega', 'confidence': 0.9},
        {'company_id': company_id, 'category': 'finance', 'signal_type': 'billing_delay_complaints', 'source_name': 'Reclamações Operacionais', 'source_url': 'https://complaints/2', 'excerpt': 'problema no faturamento', 'confidence': 0.88},
        {'company_id': company_id, 'category': 'legal', 'signal_type': 'execution_process', 'source_name': 'JusBrasil', 'source_url': 'https://legal/1', 'excerpt': 'execucao', 'confidence': 0.92},
        {'company_id': company_id, 'category': 'operations', 'signal_type': 'new_branch', 'source_name': 'Notícias Regionais', 'source_url': 'https://news/1', 'excerpt': 'nova filial', 'confidence': 0.87},
    ]:
        assert client.post('/signals', json=signal).status_code == 200

    lead = client.post(f'/leads/generate/{company_id}')
    assert lead.status_code == 200
    body = lead.json()
    assert body['score'] >= 70
    assert body['lead_tier'] in {'A', 'B'}
    assert 'cross_source_bonus' in body['score_explanation']
