def test_normalization_enriches_company_aliases_and_domains(client):
    company = client.post('/companies', json={
        'legal_name': 'Logistica Forte Ltda',
        'trade_name': 'Log Forte',
        'city': 'Campinas',
        'state': 'SP',
        'website': 'https://logforte.com.br'
    }).json()

    raw_event = client.post('/raw-events', json={
        'source_name': 'Notícias Regionais',
        'source_url': 'https://expansao.logfortejobs.com/noticia-1',
        'title': 'Logística Forte abre nova base',
        'content': 'Logística Forte confirma nova filial e expansão operacional em Campinas.',
        'company_name_raw': 'Logística Forte Brasil',
        'company_website_raw': 'https://carreiras.logfortejobs.com.br',
        'city_raw': 'Campinas',
        'state_raw': 'SP',
        'confidence': 0.82
    }).json()

    normalized = client.post(f"/raw-events/{raw_event['id']}/normalize")
    assert normalized.status_code == 200

    matched = client.post('/companies/match', json={
        'company_name': 'Logística Forte Brasil',
        'city': 'Campinas',
        'state': 'SP'
    })
    assert matched.status_code == 200
    matched_body = matched.json()
    assert matched_body['id'] == company['id']
    assert 'Logística Forte Brasil' in matched_body['aliases']
    assert 'carreiras.logfortejobs.com.br' in matched_body['domains']
