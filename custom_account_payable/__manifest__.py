{
    "name": "Account Payable",
    "summary": "Payable titles, installments, schedules and payments",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "license": "LGPL-3",
    "author": "Sursum Corda",
    "depends": [
        "custom_financial_base",
        "custom_treasury",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/payable_title_views.xml",
        "views/payable_installment_views.xml",
        "views/payable_payment_views.xml",
        "views/payable_schedule_views.xml",
    ],
    "installable": True,
    "application": False,
}
