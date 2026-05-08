from odoo import models, api


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _create_invoice(self, order, so_line, amount):
        invoice = super()._create_invoice(order, so_line, amount)
        if invoice and invoice.move_type == "out_invoice":
            invoice.is_downpayment = True
            so = order or invoice._get_source_sale_order()
            invoice._compute_invoice_type_from_dp_method(
                self.advance_payment_method, sale_order=so
            )
        return invoice

    def _create_invoices(self, orders):
        invoices = super()._create_invoices(orders)
        for invoice in invoices:
            if invoice.move_type == "out_invoice":
                so = invoice._get_source_sale_order()
                invoice._compute_invoice_type_from_dp_method(
                    self.advance_payment_method, sale_order=so
                )
                if self.advance_payment_method != "delivered":
                    invoice.is_downpayment = True
        return invoices
