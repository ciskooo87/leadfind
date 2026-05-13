from unittest.mock import patch


def test_gupy_provider_collects_events(client):
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
      <a data-testid="job-list-item" href="https://portal.gupy.io/jobs/12345">Vaga Especialista em Implantação de ERP - Distribuidora Modelo Contagem MG</a>
    </body></html>
    '''

    with patch('app.collectors.gupy_jobs_provider.fetch_text', return_value=html):
        resp = client.post('/providers/gupy-jobs/collect', json={
            'url': 'https://portal.gupy.io/jobs',
            'source_name': 'Gupy',
            'confidence': 0.84,
            'normalize_after_insert': True
        })

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]['normalized_status'] in {'signal_created', 'normalized', 'ignored'}
