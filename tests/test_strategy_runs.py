def _payload(title: str, capital: int = 2500, target: int = 20000):
    return {
        'title': title,
        'request': {
            'available_capital_brl': capital,
            'target_brl': target,
            'max_hours_per_day': 2,
            'market_scope': 'Brasil + global',
            'profile': 'executor solo orientado a ativos',
        },
    }


def test_create_and_fetch_strategy_run(client):
    created = client.post('/strategy/runs', json=_payload('Teste assimetria'))
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


def test_compare_and_export_strategy_runs(client):
    first = client.post('/strategy/runs', json=_payload('Rodada 1')).json()
    second = client.post('/strategy/runs', json=_payload('Rodada 2', capital=3000, target=30000)).json()

    compare = client.get(f"/strategy/compare?run_ids={first['id']}&run_ids={second['id']}")
    assert compare.status_code == 200, compare.text
    items = compare.json()['items']
    assert len(items) == 2
    assert items[0]['winner_name'] == 'Agente de cobrança preventiva para PMEs'

    exported_json = client.get(f"/strategy/runs/{first['id']}/export?format=json")
    assert exported_json.status_code == 200
    assert exported_json.json()['id'] == first['id']

    exported_md = client.get(f"/strategy/runs/{second['id']}/export?format=md")
    assert exported_md.status_code == 200
    assert 'Top 5' in exported_md.text
    assert 'Rodada 2' in exported_md.text
