{
    "name": "Treasury Bank",
    "summary": "Banks, bank accounts and statement import",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "license": "LGPL-3",
    "author": "Sursum Corda",
    "depends": [
        "custom_treasury",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/treasury_bank_views.xml",
        "views/treasury_bank_account_views.xml",
        "views/treasury_bank_account_modality_views.xml",
        "views/treasury_bank_statement_import_views.xml",
    ],
    "installable": True,
    "application": False,
}
