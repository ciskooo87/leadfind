def test_external_market_signals_feed_strategy_analysis(client):
    created = client.post('/strategy/signals/external', json={
        'signal_key': 'doc_generation',
        'title': 'Novo ciclo de automação documental',
        'source_name': 'manual',
        'source_url': 'https://example.com/signal',
        'summary': 'Empresas acelerando documentação automática.',
        'relevance_weight': 4,
        'active': True,
    })
    assert created.status_code == 200, created.text
    signal = created.json()
    assert signal['signal_key'] == 'doc_generation'

    listed = client.get('/strategy/signals/external?active_only=true')
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) == 1

    analyzed = client.post('/strategy/analyze', json={
        'available_capital_brl': 2500,
        'target_brl': 20000,
        'max_hours_per_day': 2,
        'market_scope': 'Brasil + global',
        'profile': 'executor solo orientado a ativos'
    })
    assert analyzed.status_code == 200, analyzed.text
    body = analyzed.json()
    assert 'Sinais aplicados:' in body['framing']
    assert any('documentação' in item['name'].lower() or 'cobrança' in item['name'].lower() for item in body['top5'])
