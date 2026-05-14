FORMAL_SIGNAL_RULES = {
    'abertura de filial': ('operations', 'new_branch', 0.92),
    'nova filial': ('operations', 'new_branch', 0.9),
    'novo centro de distribuicao': ('operations', 'new_distribution_center', 0.9),
    'novo centro de distribuição': ('operations', 'new_distribution_center', 0.9),
    'aumento de capital': ('finance', 'capital_increase_signal', 0.86),
    'alteracao contratual': ('operations', 'corporate_change_signal', 0.78),
    'alteração contratual': ('operations', 'corporate_change_signal', 0.78),
    'expansao operacional': ('operations', 'geographic_expansion', 0.82),
    'expansão operacional': ('operations', 'geographic_expansion', 0.82),
    'novo estabelecimento': ('operations', 'new_branch', 0.86),
}
