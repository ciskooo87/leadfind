from unittest.mock import patch


def test_reclame_aqui_like_provider_collects_events(client):
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
      <article class="complaint-card">
        <a href="https://reputacao.example.com/reclamacao/1">Abrir</a>
        <h2>Atraso de entrega e problema no faturamento</h2>
        <p>Cliente relata atraso na entrega, erro no faturamento e não responde no atendimento.</p>
        <div class="company">Trans Exemplo</div>
        <div class="city">Campinas</div>
        <div class="state">SP</div>
      </article>
    </body></html>
    '''

    with patch('app.collectors.reclame_aqui_provider.fetch_text', return_value=html):
        resp = client.post('/providers/reclame-aqui/collect', json={
            'url': 'https://reputacao.example.com/trans-exemplo',
            'source_name': 'Reclamações Operacionais',
            'confidence': 0.8,
            'normalize_after_insert': True
        })

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]['normalized_status'] in {'signal_created', 'normalized', 'ignored'}
