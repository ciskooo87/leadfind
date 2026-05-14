from unittest.mock import patch


def test_reputation_provider_collects_events(client):
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
        <a class="complaint-link" href="https://complaints.example.com/1">Ver</a>
        <h2 class="complaint-title">Atraso de entrega e problema no faturamento</h2>
        <div class="complaint-content">Cliente relata atraso na entrega, erro no faturamento e atendimento ruim da Trans Exemplo.</div>
        <div class="complaint-company">Trans Exemplo</div>
        <div class="complaint-city">Campinas</div>
        <div class="complaint-state">SP</div>
        <a class="company-site" href="https://transexemplo.com.br">Site</a>
      </article>
    </body></html>
    '''

    with patch('app.collectors.reputation_html_provider.fetch_text', return_value=html):
        resp = client.post('/providers/generic-html-reputation/collect', json={
            'url': 'https://complaints.example.com/trans-exemplo',
            'source_name': 'Reclamações Operacionais',
            'item_selector': '.complaint-card',
            'title_selector': '.complaint-title',
            'content_selector': '.complaint-content',
            'company_selector': '.complaint-company',
            'city_selector': '.complaint-city',
            'state_selector': '.complaint-state',
            'link_selector': '.complaint-link',
            'website_selector': '.company-site',
            'confidence': 0.8,
            'normalize_after_insert': True
        })

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]['normalized_status'] in {'signal_created', 'normalized', 'ignored'}
    assert 'billing_delay_complaints' in (body[0]['normalized_signal_type'] or '') or 'delivery_delay_complaints' in (body[0]['normalized_signal_type'] or '')
