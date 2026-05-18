def test_create_and_fetch_strategy_run(client):
    payload = {
        'title': 'Teste assimetria',
        'request': {
            'available_capital_brl': 2500,
            'target_brl': 20000,
            'max_hours_per_day': 2,
            'market_scope': 'Brasil + global',
            'profile': 'executor solo orientado a ativos',
        },
    }

    created = client.post('/strategy/runs', json=payload)
    assert created.status_code == 200, created.text
    body = created.json()
    assert body['title'] == 'Teste assimetria'
    assert body['winner_name'] == 'Agente de cobrança preventiva para PMEs'
    run_id = body['id']

    listed = client.get('/strategy/runs')
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) == 1
    assert items[0]['id'] == run_id

    fetched = client.get(f'/strategy/runs/{run_id}')
    assert fetched.status_code == 200
    detail = fetched.json()
    assert detail['response']['winner']['name'] == 'Agente de cobrança preventiva para PMEs'
    assert len(detail['response']['top5']) == 5
