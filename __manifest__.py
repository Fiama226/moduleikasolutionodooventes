{
    "name": "Landry IKA Odoo Module",
    "version": "18.0.1.0.0",
    "category": "Sales/Sales",
    "summary": "Proforma (PF) and Bon de Commande (BC) numbering with custom reports",
    "description": """
        This module provides:
        - Automatic PF/YYYY/NNNN numbering on sale order creation (no reset)
        - Automatic BC/YYYY/NNNN numbering on sale order confirmation (annual reset)
        - Proforma number preserved for reference after confirmation
        - Custom header/footer for all reports
        - Proforma report template
    """,
    "author": "IKASolution 20",
    "website": "https://www.ikasolution.com",
    "license": "LGPL-3",
    "depends": ["sale", "web"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence_data.xml",
        "views/sale_order_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "layouts.xml",
        "reports/proforma_report.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
}
