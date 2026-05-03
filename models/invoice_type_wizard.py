from odoo import _, api, fields, models


class InvoiceTypeWizard(models.TransientModel):
    _name = "account.move.invoice.type.wizard"
    _description = "Invoice Type Selection Dialog"

    move_id = fields.Many2one(
        "account.move",
        string="Facture",
        required=True,
        ondelete="cascade",
    )
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Commande source",
    )

    invoice_type = fields.Selection(
        [
            ("normal", "Facture Normale/Simple"),
            ("downpayment", "Facture d'Acompte"),
        ],
        string="Type de Facture",
        required=True,
        default="normal",
    )

    message = fields.Html(
        string="Information",
        compute="_compute_message",
    )

    @api.depends("sale_order_id", "move_id")
    def _compute_message(self):
        for rec in self:
            so = rec.sale_order_id or rec.move_id.sale_order_id
            message = "<h4>Selectionnez le type de facture :</h4>"
            message += "<ul>"
            message += "<li><b>Facture Normale</b> : Facture complete ou facture solde</li>"
            message += "<li><b>Facture d'Acompte</b> : Paiement partiel</li>"
            message += "</ul>"

            if so:
                existing_count = self.env["account.move"].search_count([
                    ("sale_order_id", "=", so.id),
                    ("invoice_type", "=", "downpayment"),
                    ("state", "=", "posted"),
                ])
                if existing_count > 0:
                    message += (
                        f"<br/><p style='color:blue;'>"
                        f"Attention : {existing_count} acompte(s) deja paye(s) sur cette commande."
                        f"</p>"
                    )
            rec.message = message

    def action_confirm(self):
        self.ensure_one()
        move = self.move_id
        vals = {"invoice_type": self.invoice_type}

        if self.invoice_type == "downpayment":
            vals["is_downpayment"] = True
            so = move._get_source_sale_order()
            if so:
                existing_count = self.env["account.move"].search_count([
                    ("sale_order_id", "=", so.id),
                    ("invoice_type", "=", "downpayment"),
                    ("state", "=", "posted"),
                    ("id", "!=", move.id),
                ])
                vals["downpayment_sequence_number"] = existing_count + 1
            else:
                vals["downpayment_sequence_number"] = 1
        else:
            vals["is_downpayment"] = False
            vals["downpayment_sequence_number"] = 0

        move.write(vals)
        move._compute_custom_report_template()
        move._compute_previous_downpayments_count()
        move._compute_total_downpayments_paid()
        move._compute_invoice_type_display()

        return {"type": "ir.actions.act_window_close"}
