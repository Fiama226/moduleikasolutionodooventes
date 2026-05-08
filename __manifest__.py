{
    "name": "Landry IKA Odoo Module",
    "version": "18.0.1.0.0",
    "category": "Sales/Sales",
    "summary": "Proforma, Bon de Commande, and dynamic invoice report personalization",
    "description": """
This module provides:
- Automatic PF/YYYY/NNNN numbering on sale order creation (no reset)
- Automatic BC/YYYY/NNNN numbering on sale order confirmation (annual reset)
- Proforma number preserved for reference after confirmation
- Custom header/footer for all reports
- Proforma report template
- Dynamic invoice report selection based on invoice type (simple/first_dp/nth_dp/balance)
- Invoice type set automatically via sale.advance.payment.inv wizard
- 4 invoice templates: simple, final (solde), first down payment, nth down payment
- Automatic down payment percentage calculation
- Previous down payments tracking and display
""",
    "author": "KABORE Pawendtaore Landry",
    "website": "https://www.ikasolution.com",
    "license": "LGPL-3",
    "depends": ["sale", "web", "account", "sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence_data.xml",
        "views/sale_order_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/account_move_views.xml",
        "layouts.xml",
        "reports/templates/proforma_report.xml",
        "reports/templates/proforma_signature_report.xml",
        "reports/templates/bon_commande_report.xml",
        "reports/sale_order_report.xml",
        "reports/invoice_report.xml",
        "reports/templates/simple_invoice_1.xml",
        "reports/templates/final_invoice.xml",
        "reports/templates/first_down_payment_invoice_1.xml",
        "reports/templates/nth_down_payment_invoice.xml",
    ],
    "post_init_hook": "post_init_hook",
    "application": True,
    "installable": True,
    "auto_install": False,
}
