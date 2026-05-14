from unittest.mock import patch


def test_formal_acts_provider_collects_events(client):
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
      <article class="formal-card">
        <a href="https://formal.example.com/ato/1">Abrir</a>
        <h2>Abertura de filial e aumento de capital</h2>
        <p>Empresa aprova abertura de filial e aumento de capital para expansão operacional.</p>
        <div class="company">Trans Exemplo</div>
        <div class="city">Campinas</div>
        <div class="state">SP</div>
      </article>
    </body></html>
    '''

    with patch('app.collectors.formal_acts_provider.fetch_text', return_value=html):
        resp = client.post('/providers/formal-acts/collect', json={
            'url': 'https://formal.example.com/trans-exemplo',
            'source_name': 'Atos Formais',
            'confidence': 0.82,
            'normalize_after_insert': True
        })

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert 'new_branch' in (body[0]['normalized_signal_type'] or '') or 'capital_increase_signal' in (body[0]['normalized_signal_type'] or '')
