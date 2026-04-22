{
    "name": "Tesouraria",
    "summary": "Movimentos, contas e transferencias de tesouraria",
    "version": "19.0.1.0.0",
    "category": "Financeiro",
    "license": "LGPL-3",
    "author": "Sursum Corda",
    "depends": [
        "custom_financial_base",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/treasury_account_views.xml",
        "views/treasury_account_modality_views.xml",
        "views/treasury_movement_views.xml",
        "views/treasury_intercompany_loan_views.xml",
        "views/treasury_transfer_views.xml",
    ],
    "installable": True,
    "application": False,
}
