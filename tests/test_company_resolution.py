def test_match_company_by_exact_domain(client):
    created = client.post('/companies', json={
        'legal_name': 'Distribuidora Modelo S/A',
        'trade_name': 'Distribuidora Modelo',
        'city': 'Contagem',
        'state': 'MG',
        'website': 'https://distribuidoramodelo.com.br'
    }).json()

    matched = client.post('/companies/match', json={
        'website': 'https://www.distribuidoramodelo.com.br/vagas'
    })

    assert matched.status_code == 200
    assert matched.json()['id'] == created['id']


def test_match_company_by_partial_name_and_location(client):
    created = client.post('/companies', json={
        'legal_name': 'Transportes Exemplo Logistica Ltda',
        'trade_name': 'Trans Exemplo',
        'city': 'Campinas',
        'state': 'SP',
        'website': 'https://transexemplo.com.br'
    }).json()

    matched = client.post('/companies/match', json={
        'company_name': 'Transporte Exemplo',
        'city': 'Campinas',
        'state': 'SP'
    })

    assert matched.status_code == 200
    assert matched.json()['id'] == created['id']


def test_match_company_prefers_location_when_names_are_similar(client):
    wrong_city = client.post('/companies', json={
        'legal_name': 'Alpha Distribuicao Ltda',
        'trade_name': 'Alpha Distribuição',
        'city': 'Betim',
        'state': 'MG',
        'website': 'https://alpha-betim.com.br'
    }).json()
    right_city = client.post('/companies', json={
        'legal_name': 'Alpha Distribuicao Campinas Ltda',
        'trade_name': 'Alpha Distribuição',
        'city': 'Campinas',
        'state': 'SP',
        'website': 'https://alpha-campinas.com.br'
    }).json()

    matched = client.post('/companies/match', json={
        'company_name': 'Alpha Distribuicao',
        'city': 'Campinas',
        'state': 'SP'
    })

    assert matched.status_code == 200
    assert matched.json()['id'] == right_city['id']
    assert matched.json()['id'] != wrong_city['id']


def test_match_company_returns_none_when_similarity_is_too_low(client):
    client.post('/companies', json={
        'legal_name': 'Beta Industrial Ltda',
        'trade_name': 'Beta Industrial',
        'city': 'Jundiai',
        'state': 'SP',
        'website': 'https://betaindustrial.com.br'
    })

    matched = client.post('/companies/match', json={
        'company_name': 'Gamma Finance',
        'city': 'Curitiba',
        'state': 'PR'
    })

    assert matched.status_code == 200
    assert matched.json() is None


def test_create_company_and_match_by_alias(client):
    created = client.post('/companies', json={
        'legal_name': 'Companhia Brasileira de Logistica Integrada S/A',
        'trade_name': 'CB Log',
        'city': 'Barueri',
        'state': 'SP',
        'website': 'https://cblog.com.br',
        'aliases': ['Companhia Brasileira Logística', 'CBL', 'Log Integrada Brasil']
    })

    assert created.status_code == 200
    body = created.json()
    assert 'CBL' in body['aliases']

    matched = client.post('/companies/match', json={
        'company_name': 'Companhia Brasileira Logistica',
        'city': 'Barueri',
        'state': 'SP'
    })

    assert matched.status_code == 200
    assert matched.json()['id'] == body['id']


def test_create_company_and_match_by_alternate_domain(client):
    created = client.post('/companies', json={
        'legal_name': 'Operadora X Logistica Ltda',
        'trade_name': 'Operadora X',
        'city': 'Osasco',
        'state': 'SP',
        'website': 'https://operadorax.com.br',
        'domains': ['careers.operadorax.com.br', 'jobs.operadorax.com', 'portal.operadorax.com.br']
    })

    assert created.status_code == 200
    body = created.json()
    assert 'jobs.operadorax.com' in body['domains']

    matched = client.post('/companies/match', json={
        'website': 'https://jobs.operadorax.com/vagas/analista-financeiro'
    })

    assert matched.status_code == 200
    assert matched.json()['id'] == body['id']
