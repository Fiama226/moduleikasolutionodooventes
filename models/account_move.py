from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    DEFAULT_NARRATION = "<p>Toute réclamation concernant la conformité des produits doit être formulée par écrit (de préférence par lettre recommandée avec accusé de réception ou e-mail), dans un délai de deux ans à compter de la délivrance du bien.</p>"

    fac_number = fields.Char(
        string="N° Facture Acompte",
        readonly=True,
        copy=False,
        help="Numero FAC/YYYY/NNNN attribue a la validation de la facture d'acompte.",
    )
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Commande source",
        compute="_compute_sale_order_id",
        store=True,
    )
    is_downpayment = fields.Boolean(
        string="Acompte",
        default=False,
        copy=False,
    )
    invoice_type = fields.Selection(
        [
            ("normal", "Facture Normale/Simple"),
            ("downpayment", "Facture d'Acompte"),
        ],
        string="Type de Facture",
        default="normal",
        tracking=True,
        help="Type de facture choisi via le popup de selection",
    )
    downpayment_sequence_number = fields.Integer(
        string="N° Acompte",
        default=0,
        copy=False,
        help="0 si facture normale, 1+ si acompte",
    )
    previous_downpayments_count = fields.Integer(
        string="Acomptes precedents",
        compute="_compute_previous_downpayments_count",
    )
    total_downpayments_paid = fields.Monetary(
        string="Total acomptes payes",
        compute="_compute_total_downpayments_paid",
        currency_field="currency_id",
    )
    is_final_payment = fields.Boolean(
        string="Dernier paiement",
        compute="_compute_is_final_payment",
    )
    custom_report_template = fields.Selection(
        [
            ("simple_invoice_1", "Facture Simple"),
            ("final_invoice", "Facture Solde"),
            ("first_down_payment_invoice_1", "1er Acompte"),
            ("nth_down_payment_invoice", "Acompte suivant"),
        ],
        string="Template rapport",
        compute="_compute_custom_report_template",
        store=True,
    )
    invoice_type_display = fields.Char(
        string="Type de facture",
        compute="_compute_invoice_type_display",
    )
    narration = fields.Html(
        default=lambda self: self.DEFAULT_NARRATION,
    )
    invoice_object = fields.Char(
        string="Objet",
        copy=True,
        help="Objet de la facture, hérité de la commande source si vide.",
    )

    @api.depends("invoice_line_ids.sale_line_ids.order_id")
    def _compute_sale_order_id(self):
        for move in self:
            sale_orders = move.invoice_line_ids.sale_line_ids.order_id
            move.sale_order_id = sale_orders[:1] if sale_orders else False

    @api.onchange("sale_order_id")
    def _onchange_sale_order_id(self):
        for rec in self:
            if rec.sale_order_id and rec.sale_order_id.proforma_object and not rec.invoice_object:
                rec.invoice_object = rec.sale_order_id.proforma_object

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for move in records:
            so = move._get_source_sale_order()
            if so and so.proforma_object and not move.invoice_object:
                move.invoice_object = so.proforma_object
            if not move.narration:
                move.narration = self.DEFAULT_NARRATION
        return records

    @api.depends("invoice_type", "is_downpayment", "downpayment_sequence_number", "previous_downpayments_count")
    def _compute_custom_report_template(self):
        for rec in self:
            if rec.invoice_type == "downpayment" or rec.is_downpayment:
                if rec.downpayment_sequence_number <= 1:
                    rec.custom_report_template = "first_down_payment_invoice_1"
                else:
                    rec.custom_report_template = "nth_down_payment_invoice"
            elif rec.invoice_type == "normal":
                if rec.previous_downpayments_count > 0:
                    rec.custom_report_template = "final_invoice"
                else:
                    rec.custom_report_template = "simple_invoice_1"
            else:
                rec.custom_report_template = "simple_invoice_1"

    @api.depends("invoice_type", "is_downpayment", "downpayment_sequence_number", "previous_downpayments_count")
    def _compute_invoice_type_display(self):
        for rec in self:
            if rec.invoice_type == "downpayment" or rec.is_downpayment:
                ordinal = self._get_ordinal_number(rec.downpayment_sequence_number or 1)
                rec.invoice_type_display = f"{ordinal} Acompte"
            elif rec.invoice_type == "normal":
                if rec.previous_downpayments_count > 0:
                    rec.invoice_type_display = "Facture Solde"
                else:
                    rec.invoice_type_display = "Facture Simple"
            else:
                rec.invoice_type_display = ""

    @api.depends("sale_order_id", "invoice_type", "is_downpayment", "state")
    def _compute_previous_downpayments_count(self):
        for rec in self:
            so = rec._get_source_sale_order()
            if so:
                domain = [
                    ("sale_order_id", "=", so.id),
                    "|",
                    ("invoice_type", "=", "downpayment"),
                    ("is_downpayment", "=", True),
                    ("state", "=", "posted"),
                ]
                if rec.id:
                    domain.append(("id", "!=", rec.id))
                rec.previous_downpayments_count = self.search_count(domain)
            else:
                rec.previous_downpayments_count = 0

    @api.depends("sale_order_id", "invoice_type", "is_downpayment", "state")
    def _compute_total_downpayments_paid(self):
        for rec in self:
            so = rec._get_source_sale_order()
            if so:
                domain = [
                    ("sale_order_id", "=", so.id),
                    "|",
                    ("invoice_type", "=", "downpayment"),
                    ("is_downpayment", "=", True),
                    ("state", "=", "posted"),
                ]
                if rec.id:
                    domain.append(("id", "!=", rec.id))
                downpayment_invoices = self.search(domain)
                rec.total_downpayments_paid = sum(inv.amount_total for inv in downpayment_invoices)
            else:
                rec.total_downpayments_paid = 0.0

    @api.depends("sale_order_id", "amount_total", "total_downpayments_paid", "invoice_type")
    def _compute_is_final_payment(self):
        for rec in self:
            so = rec._get_source_sale_order()
            if so and rec.invoice_type == "normal":
                rec.is_final_payment = (
                    abs((rec.total_downpayments_paid + rec.amount_total) - so.amount_total) < 0.01
                )
            else:
                rec.is_final_payment = False

    def _get_source_sale_order(self):
        self.ensure_one()
        if self.sale_order_id:
            return self.sale_order_id
        if self.invoice_origin:
            so = self.env["sale.order"].search([("name", "=", self.invoice_origin)], limit=1)
            if so:
                return so
        return False

    @staticmethod
    def _get_ordinal_number(num):
        if num == 1:
            return "1er"
        elif num == 2:
            return "2eme"
        elif num == 3:
            return "3eme"
        else:
            return f"{num}eme"

    def _get_previous_downpayments(self, only_posted=True):
        self.ensure_one()
        so = self._get_source_sale_order()
        if not so:
            return []
        domain = [
            ("sale_order_id", "=", so.id),
            "|",
            ("invoice_type", "=", "downpayment"),
            ("is_downpayment", "=", True),
            ("id", "!=", self.id),
        ]
        if only_posted:
            domain.append(("state", "=", "posted"))
        downpayments = self.search(domain, order="date asc")
        result = []
        for idx, dp in enumerate(downpayments, 1):
            result.append({
                "sequence": idx,
                "invoice_name": dp.fac_number or dp.name or "",
                "invoice_date": dp.invoice_date.strftime("%d/%m/%Y") if dp.invoice_date else "",
                "amount_total": dp.amount_total,
                "amount_untaxed": dp.amount_untaxed,
            })
        return result

    def action_show_invoice_type_dialog(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move.invoice.type.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_move_id": self.id,
                "default_sale_order_id": self.sale_order_id.id if self.sale_order_id else False,
            },
        }

    @api.onchange("invoice_type")
    def _onchange_invoice_type(self):
        if self.invoice_type == "normal":
            self.downpayment_sequence_number = 0
            self.is_downpayment = False
        elif self.invoice_type == "downpayment":
            self.is_downpayment = True
            self.downpayment_sequence_number = self.previous_downpayments_count + 1

    def action_post(self):
        res = super().action_post()
        for move in self:
            if move.is_downpayment or move.invoice_type == "downpayment":
                if not move.fac_number:
                    move.fac_number = (
                        self.env["ir.sequence"]
                        .with_company(move.company_id)
                        .next_by_code("account.move.seq_fac")
                    )
                if not move.is_downpayment:
                    move.is_downpayment = True
                if move.invoice_type != "downpayment":
                    move.invoice_type = "downpayment"
                so = move._get_source_sale_order()
                if so and not move.downpayment_sequence_number:
                    existing_count = self.env["account.move"].search_count([
                        ("sale_order_id", "=", so.id),
                        ("invoice_type", "=", "downpayment"),
                        ("state", "=", "posted"),
                        ("id", "!=", move.id),
                    ])
                    move.downpayment_sequence_number = existing_count + 1
                elif not move.downpayment_sequence_number:
                    move.downpayment_sequence_number = 1
            move._compute_custom_report_template()
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_downpayment_deduction = fields.Boolean(
        string="Deduction acompte",
        default=False,
        copy=False,
    )
    down_payment_invoice_id = fields.Many2one(
        "account.move",
        string="Facture d'acompte source",
    )
