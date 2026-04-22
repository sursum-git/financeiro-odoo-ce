{
    "name": "Integracao Financeira",
    "summary": "Integracao central entre tesouraria, receber e pagar",
    "version": "19.0.1.0.0",
    "category": "Financeiro",
    "license": "LGPL-3",
    "author": "Sursum Corda",
    "depends": [
        "custom_treasury",
        "custom_account_receivable",
        "custom_account_payable",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/financial_integration_event_views.xml",
        "views/financial_integration_log_views.xml",
    ],
    "installable": True,
    "application": False,
}
