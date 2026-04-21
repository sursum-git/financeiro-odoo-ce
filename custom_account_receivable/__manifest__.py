{
    "name": "Account Receivable",
    "summary": "Receivable titles, installments, settlements and renegotiation",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "license": "LGPL-3",
    "author": "OpenAI",
    "depends": [
        "base",
        "custom_financial_base",
        "custom_treasury",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/receivable_title_views.xml",
        "views/receivable_installment_views.xml",
        "views/receivable_settlement_views.xml",
        "views/receivable_interest_rule_views.xml",
    ],
    "installable": True,
    "application": False,
}
