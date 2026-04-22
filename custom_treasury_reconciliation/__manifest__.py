{
    "name": "Conciliacao de Tesouraria",
    "summary": "Conciliacao de extrato bancario com movimentos de tesouraria",
    "version": "19.0.1.0.0",
    "category": "Financeiro",
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
