def test_ranking_filters_by_match_quality_and_company_query(client):
    company_a = client.post('/companies', json={
        'legal_name': 'Alta Match S/A',
        'trade_name': 'Alta Match',
        'sector': 'distribuidora',
        'city': 'Contagem',
        'state': 'MG',
        'estimated_size': 'medium',
        'website': 'https://altamatch.com.br'
    }).json()
    company_b = client.post('/companies', json={
        'legal_name': 'Baixa Match Ltda',
        'trade_name': 'Baixa Match',
        'sector': 'transportadora',
        'city': 'Campinas',
        'state': 'SP',
        'estimated_size': 'medium',
        'website': 'https://baixamatch.com.br'
    }).json()

    raw_a = client.post('/raw-events', json={
        'source_name': 'Notícias Regionais',
        'source_url': 'https://altamatch.com.br/news',
        'title': 'Alta Match expande',
        'content': 'Alta Match anuncia nova filial.',
        'company_name_raw': 'Alta Match',
        'company_website_raw': 'https://altamatch.com.br',
        'city_raw': 'Contagem',
        'state_raw': 'MG',
        'confidence': 0.9
    }).json()
    client.post(f"/raw-events/{raw_a['id']}/normalize")

    raw_b = client.post('/raw-events', json={
        'source_name': 'Notícias Regionais',
        'source_url': 'https://portal-external.com/news',
        'title': 'Baixa Operações expande',
        'content': 'Empresa expande operação em Campinas.',
        'company_name_raw': 'Baixa Operações',
        'company_website_raw': 'https://portal-external.com',
        'city_raw': 'Campinas',
        'state_raw': 'SP',
        'confidence': 0.8
    }).json()
    client.post(f"/raw-events/{raw_b['id']}/normalize")

    for company_id, url in [(company_a['id'], 'https://a/1'), (company_b['id'], 'https://b/1')]:
        client.post('/signals', json={
            'company_id': company_id,
            'category': 'operations',
            'signal_type': 'new_branch',
            'source_name': 'Notícias Regionais',
            'source_url': url,
            'excerpt': 'nova filial',
            'confidence': 0.9
        })
        client.post(f'/leads/generate/{company_id}')

    high = client.get('/leads/ranking?match_quality=alta')
    assert high.status_code == 200
    assert high.json()['total'] == 1
    assert high.json()['items'][0]['company_id'] == company_a['id']

    query = client.get('/leads/ranking?company_query=campinas')
    assert query.status_code == 200
    assert query.json()['total'] == 1
    assert query.json()['items'][0]['company_id'] == company_b['id']
