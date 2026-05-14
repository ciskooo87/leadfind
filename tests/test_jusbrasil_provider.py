from unittest.mock import patch


def test_jusbrasil_like_provider_collects_events(client):
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
      <article class="legal-card">
        <a href="https://legal.example.com/processo/1">Abrir</a>
        <h2>Execução e ação de cobrança contra Trans Exemplo</h2>
        <p>Processo indica execução, ação de cobrança e indícios de pressão financeira.</p>
        <div class="company">Trans Exemplo</div>
        <div class="city">Campinas</div>
        <div class="state">SP</div>
      </article>
    </body></html>
    '''

    with patch('app.collectors.jusbrasil_provider.fetch_text', return_value=html):
        resp = client.post('/providers/jusbrasil/collect', json={
            'url': 'https://legal.example.com/trans-exemplo',
            'source_name': 'JusBrasil',
            'confidence': 0.84,
            'normalize_after_insert': True
        })

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]['normalized_status'] in {'signal_created', 'normalized', 'ignored'}
    assert 'execution_process' in (body[0]['normalized_signal_type'] or '') or 'legal_collection_growth' in (body[0]['normalized_signal_type'] or '')
