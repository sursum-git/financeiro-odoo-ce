{
    "name": "Treasury Reconciliation",
    "summary": "Bank statement reconciliation against treasury movements",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "license": "LGPL-3",
    "author": "Sursum Corda",
    "depends": [
        "custom_treasury",
        "custom_treasury_bank",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/treasury_reconciliation_views.xml",
    ],
    "installable": True,
    "application": False,
}
