from unittest.mock import patch


def test_regional_news_provider_collects_events(client):
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
      <article class="news-card">
        <a href="https://regional.example.com/noticia/1">Abrir</a>
        <h2>Trans Exemplo anuncia nova filial em Campinas</h2>
        <p>Empresa confirma abertura de nova filial, expansão operacional e reforço logístico na região.</p>
        <div class="company">Trans Exemplo</div>
        <div class="city">Campinas</div>
        <div class="state">SP</div>
        <a class="company-site" href="https://transexemplo.com.br">Site</a>
      </article>
    </body></html>
    '''

    with patch('app.collectors.regional_news_provider.fetch_text', return_value=html):
        resp = client.post('/providers/regional-news/collect', json={
            'url': 'https://regional.example.com/trans-exemplo',
            'source_name': 'Notícias Regionais',
            'confidence': 0.78,
            'normalize_after_insert': True
        })

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]['normalized_status'] in {'signal_created', 'normalized', 'ignored'}
    assert 'new_branch' in (body[0]['normalized_signal_type'] or '') or 'geographic_expansion' in (body[0]['normalized_signal_type'] or '')
