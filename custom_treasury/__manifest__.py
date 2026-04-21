{
    "name": "Treasury",
    "summary": "Core treasury movements, accounts and transfers",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "license": "LGPL-3",
    "author": "OpenAI",
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
        "views/treasury_transfer_views.xml",
    ],
    "installable": True,
    "application": False,
}
