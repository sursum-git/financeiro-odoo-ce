{
    "name": "Financial Base",
    "summary": "Base cadastros and parameters for financial modules",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "license": "LGPL-3",
    "author": "OpenAI",
    "depends": [
        "base",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/financial_portador_views.xml",
        "views/financial_payment_method_views.xml",
        "views/financial_modality_views.xml",
        "views/financial_history_views.xml",
        "views/financial_movement_reason_views.xml",
        "views/financial_parameter_views.xml",
    ],
    "installable": True,
    "application": False,
}
