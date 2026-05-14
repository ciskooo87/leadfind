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


def test_multi_source_scoring_with_credit_legal_reputation(client):
    company = client.post('/companies', json={
        'legal_name': 'Carga Forte Ltda',
        'trade_name': 'Carga Forte',
        'sector': 'transportadora',
        'city': 'Guarulhos',
        'state': 'SP',
        'estimated_size': 'medium',
        'website': 'https://cargaforte.com.br'
    }).json()
    company_id = company['id']

    for signal in [
        {'company_id': company_id, 'category': 'finance', 'signal_type': 'credit_bureau_negative_signal', 'source_name': 'Serasa', 'source_url': 'https://serasa/1', 'excerpt': 'negativacao', 'confidence': 0.93},
        {'company_id': company_id, 'category': 'finance', 'signal_type': 'overdue_debt_signal', 'source_name': 'Serasa', 'source_url': 'https://serasa/2', 'excerpt': 'divida vencida', 'confidence': 0.9},
        {'company_id': company_id, 'category': 'legal', 'signal_type': 'execution_process', 'source_name': 'JusBrasil', 'source_url': 'https://legal/1', 'excerpt': 'execucao', 'confidence': 0.91},
        {'company_id': company_id, 'category': 'operations', 'signal_type': 'delivery_delay_complaints', 'source_name': 'Reclamações Operacionais', 'source_url': 'https://complaints/1', 'excerpt': 'atraso', 'confidence': 0.87},
    ]:
        assert client.post('/signals', json=signal).status_code == 200

    lead = client.post(f'/leads/generate/{company_id}')
    assert lead.status_code == 200
    body = lead.json()
    assert body['lead_tier'] == 'A'
    assert 'credit+legal' in body['score_explanation']
    assert 'credit+legal+reputation' in body['score_explanation']

    executive = client.get(f'/leads/{company_id}/executive')
    assert executive.status_code == 200
    assert executive.json()['produto_mais_indicado']


def test_multi_source_scoring_with_formal_and_jobs(client):
    company = client.post('/companies', json={
        'legal_name': 'Expansao Rapida S/A',
        'trade_name': 'Expansão Rápida',
        'sector': 'distribuidora',
        'city': 'Sorocaba',
        'state': 'SP',
        'estimated_size': 'medium',
        'website': 'https://expansaorapida.com.br'
    }).json()
    company_id = company['id']

    for signal in [
        {'company_id': company_id, 'category': 'finance', 'signal_type': 'capital_increase_signal', 'source_name': 'Atos Formais', 'source_url': 'https://formal/1', 'excerpt': 'aumento de capital', 'confidence': 0.88},
        {'company_id': company_id, 'category': 'operations', 'signal_type': 'new_branch', 'source_name': 'Atos Formais', 'source_url': 'https://formal/2', 'excerpt': 'nova filial', 'confidence': 0.9},
        {'company_id': company_id, 'category': 'digital', 'signal_type': 'erp_implementation', 'source_name': 'Workday', 'source_url': 'https://jobs/1', 'excerpt': 'implantacao erp', 'confidence': 0.86},
    ]:
        assert client.post('/signals', json=signal).status_code == 200

    lead = client.post(f'/leads/generate/{company_id}')
    assert lead.status_code == 200
    body = lead.json()
    assert body['score'] >= 70
    assert 'formal+jobs' in body['score_explanation']
    assert 'capital_increase+erp_implementation' in body['score_explanation']
