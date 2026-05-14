from unittest.mock import patch


def test_workday_provider_collects_events(client):
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
      <li>
        <a href="https://wd3.myworkdaysite.com/en-US/recruiting/distribuidoramodelo/job/Contagem-MG/Especialista-em-Implantao-de-ERP_JR-12345">Especialista em Implantação de ERP</a>
        <div>Contagem, MG</div>
      </li>
    </body></html>
    '''

    with patch('app.collectors.workday_jobs_provider.fetch_text', return_value=html):
        resp = client.post('/providers/workday-jobs/collect', json={
            'url': 'https://wd3.myworkdaysite.com/en-US/recruiting/distribuidoramodelo/jobs',
            'source_name': 'Workday',
            'confidence': 0.85,
            'normalize_after_insert': True
        })

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]['company_name_raw'] == 'distribuidoramodelo'
    assert body[0]['state_raw'] == 'MG'
