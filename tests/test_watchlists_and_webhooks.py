from unittest.mock import patch


def test_watchlist_run_generates_leads_and_logs(client):
    client.post('/companies', json={
        'legal_name': 'Distribuidora Modelo S/A',
        'trade_name': 'Distribuidora Modelo',
        'sector': 'distribuidora',
        'city': 'Contagem',
        'state': 'MG',
        'estimated_size': 'medium',
        'website': 'https://distribuidoramodelo.com.br'
    })

    payload = {
        'name': 'Indeed Feed Test',
        'source_kind': 'json_jobs',
        'source_name': 'Indeed',
        'config_json': '{"url":"http://example.test/feed.json","source_name":"Indeed","items_path":"jobs","title_path":"title","content_path":"description","company_path":"company.name","city_path":"location.city","state_path":"location.state","link_path":"url","website_path":"company.website","external_id_path":"id","confidence":0.82,"normalize_after_insert":true}',
        'active': True,
        'schedule_minutes': 1
    }
    watchlist = client.post('/watchlists', json=payload).json()

    fake_feed = {
        'jobs': [
            {
                'id': 'feed-001',
                'title': 'Especialista em Implantação de ERP',
                'description': 'Distribuidora busca profissional para implantação de ERP com integração financeira e tesouraria.',
                'company': {'name': 'Distribuidora Modelo', 'website': 'https://distribuidoramodelo.com.br'},
                'location': {'city': 'Contagem', 'state': 'MG'},
                'url': 'https://feed.example.com/jobs/1'
            }
        ]
    }

    with patch('app.collectors.json_jobs_provider.fetch_text', return_value=__import__('json').dumps(fake_feed)):
        run = client.post(f"/watchlists/{watchlist['id']}/run")

    assert run.status_code == 200
    body = run.json()
    assert body['generated_leads'] == 1
    assert body['impacted_company_ids'] == [1]

    logs = client.get(f"/watchlists/{watchlist['id']}/runs")
    assert logs.status_code == 200
    assert logs.json()[0]['status'] == 'success'


def test_auto_dispatch_webhook_on_lead_generation(client):
    with patch('app.services.webhooks.httpx.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = 'OK'

        target = client.post('/webhooks', json={
            'name': 'CRM Auto',
            'target_url': 'http://example.test/hook',
            'active': True,
            'min_score': 60,
            'lead_tiers': 'A,B'
        })
        assert target.status_code == 200

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
        ]:
            client.post('/signals', json=signal)

        lead = client.post(f'/leads/generate/{company_id}')
        assert lead.status_code == 200
        assert mock_post.called

        deliveries = client.get('/webhooks/1/deliveries')
        assert deliveries.status_code == 200
        assert deliveries.json()[0]['status'] == 'success'
