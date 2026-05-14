from unittest.mock import patch


def test_lever_provider_collects_events(client):
    client.post('/companies', json={
        'legal_name': 'Distribuidora Modelo S/A',
        'trade_name': 'Distribuidora Modelo',
        'sector': 'distribuidora',
        'city': 'Contagem',
        'state': 'MG',
        'estimated_size': 'medium',
        'website': 'https://distribuidoramodelo.com.br'
    })

    html = '''
    <html><body>
      <div class="posting">
        <a href="https://jobs.lever.co/distribuidoramodelo/abc123">Especialista em Implantação de ERP</a>
        <span>Contagem, MG</span>
      </div>
    </body></html>
    '''

    with patch('app.collectors.lever_jobs_provider.fetch_text', return_value=html):
        resp = client.post('/providers/lever-jobs/collect', json={
            'url': 'https://jobs.lever.co/distribuidoramodelo',
            'source_name': 'Lever',
            'confidence': 0.85,
            'normalize_after_insert': True
        })

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]['company_name_raw'] == 'distribuidoramodelo'
    assert body[0]['state_raw'] == 'MG'
