from unittest.mock import patch


def test_serasa_provider_collects_events(client):
    client.post('/companies', json={
        'legal_name': 'Trans Exemplo Ltda',
        'trade_name': 'Trans Exemplo',
        'sector': 'transportadora',
        'city': 'Campinas',
        'state': 'SP',
        'estimated_size': 'medium',
        'website': 'https://transexemplo.com.br'
    })

    html = '''
    <html><body>
      <article class="credit-card">
        <a href="https://serasa.example.com/empresa/1">Abrir</a>
        <h2>Negativação e dívida vencida</h2>
        <p>Empresa apresenta negativação, dívida vencida e restrição financeira.</p>
        <div class="company">Trans Exemplo</div>
        <div class="city">Campinas</div>
        <div class="state">SP</div>
      </article>
    </body></html>
    '''

    with patch('app.collectors.serasa_provider.fetch_text', return_value=html):
        resp = client.post('/providers/serasa/collect', json={
            'url': 'https://serasa.example.com/trans-exemplo',
            'source_name': 'Serasa',
            'confidence': 0.84,
            'normalize_after_insert': True
        })

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert 'credit_bureau_negative_signal' in (body[0]['normalized_signal_type'] or '') or 'overdue_debt_signal' in (body[0]['normalized_signal_type'] or '')
