{
    "name": "Caixa da Tesouraria",
    "summary": "Sessoes de caixa, suprimento, sangria e prestacao de contas",
    "version": "19.0.1.0.0",
    "category": "Financeiro",
    "license": "LGPL-3",
    "author": "Sursum Corda",
    "depends": [
        "custom_treasury",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/treasury_cash_box_views.xml",
        "views/treasury_cash_session_views.xml",
        "views/treasury_cash_accountability_views.xml",
        "views/treasury_cash_operation_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
}
