{
    "name": "Treasury Cash",
    "summary": "Cash sessions, supply, withdrawal and accountability",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "license": "LGPL-3",
    "author": "OpenAI",
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
    ],
    "installable": True,
    "application": False,
}
