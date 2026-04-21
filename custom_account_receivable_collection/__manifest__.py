{
    "name": "Account Receivable Collection",
    "summary": "Operational collection flow for account receivable",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "license": "LGPL-3",
    "author": "OpenAI",
    "depends": [
        "custom_account_receivable",
        "custom_treasury_cash",
        "custom_financial_integration",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/receivable_collection_agent_views.xml",
        "views/receivable_collection_route_views.xml",
        "views/receivable_collection_assignment_views.xml",
        "views/receivable_collection_accountability_views.xml",
    ],
    "installable": True,
    "application": False,
}
