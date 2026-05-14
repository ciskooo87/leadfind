SIGNAL_WEIGHTS = {
    "finance": {
        "controller_hiring": 8,
        "treasury_hiring": 8,
        "collections_hiring": 7,
        "accounts_receivable_hiring": 7,
        "financial_restructuring": 15,
        "explicit_credit_search": 20,
        "billing_delay_complaints": 7,
        "payment_delay_complaints": 8,
        "legal_collection_growth": 12,
        "capital_increase_signal": 9,
        "credit_bureau_negative_signal": 15,
        "credit_score_drop_signal": 11,
        "overdue_debt_signal": 14,
    },
    "operations": {
        "new_branch": 10,
        "new_distribution_center": 10,
        "fleet_expansion": 9,
        "logistics_hiring": 8,
        "geographic_expansion": 8,
        "accelerated_growth_news": 7,
        "delivery_delay_complaints": 8,
        "service_breakdown_complaints": 7,
        "logistics_complaints": 7,
        "corporate_change_signal": 6,
    },
    "digital": {
        "erp_change": 10,
        "erp_implementation": 10,
        "bpo_finance": 8,
        "financial_bi": 6,
        "system_implementation_hiring": 7,
    },
    "legal": {
        "labor_claim_growth": 8,
        "execution_process": 12,
        "judicial_recovery_signal": 18,
    },
}

PRIORITY_SECTORS = {
    "transportadora": 10,
    "distribuidora": 10,
    "atacadista": 10,
    "industria leve": 8,
    "operador logistico": 9,
}
