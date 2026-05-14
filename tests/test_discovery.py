def test_discovery_run_aggregates_multi_provider_results(client):
    company = client.post('/companies', json={
        'legal_name': 'Discovery Real Ltda',
        'trade_name': 'Discovery Real',
        'sector': 'distribuidora',
        'city': 'Campinas',
        'state': 'SP',
        'estimated_size': 'medium',
        'website': 'https://discovery-real.com.br'
    }).json()

    payload = {
        'providers': [
            {
                'kind': 'generic_html_news',
                'payload': {
                    'url': 'https://discovery-real.com.br/news',
                    'source_name': 'Notícias Regionais',
                    'item_selector': 'article',
                    'title_selector': 'h2',
                    'content_selector': 'p',
                    'company_selector': '.company',
                    'city_selector': '.city',
                    'state_selector': '.state',
                    'link_selector': 'a[href]',
                    'website_selector': '.company-site',
                    'confidence': 0.82,
                    'normalize_after_insert': True
                }
            }
        ],
        'generate_leads': True,
        'ranking_limit': 10
    }

    from unittest.mock import patch
    html = '''
    <html><body>
      <article>
        <a href="https://news.example.com/1">Abrir</a>
        <h2>Nova filial</h2>
        <p>Discovery Real anuncia nova filial em Campinas.</p>
        <div class="company">Discovery Real</div>
        <div class="city">Campinas</div>
        <div class="state">SP</div>
      </article>
    </body></html>
    '''
    with patch('app.collectors.news_html_provider.fetch_text', return_value=html):
        resp = client.post('/discovery/run', json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body['generated_leads'] == 1
    assert body['impacted_company_ids'] == [company['id']]
    assert body['providers'][0]['kind'] == 'generic_html_news'
    assert body['providers'][0]['created_events'] == 1
