from unittest.mock import patch


def test_greenhouse_provider_collects_events(client):
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
      <section class="opening">
        <a href="https://boards.greenhouse.io/distribuidoramodelo/jobs/98765">Especialista em Implantação de ERP</a>
        <span class="location">Contagem, MG</span>
      </section>
    </body></html>
    '''

    with patch('app.collectors.greenhouse_jobs_provider.fetch_text', return_value=html):
        resp = client.post('/providers/greenhouse-jobs/collect', json={
            'url': 'https://boards.greenhouse.io/distribuidoramodelo',
            'source_name': 'Greenhouse',
            'confidence': 0.85,
            'normalize_after_insert': True
        })

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]['company_name_raw'] == 'distribuidoramodelo'
    assert body[0]['state_raw'] == 'MG'
