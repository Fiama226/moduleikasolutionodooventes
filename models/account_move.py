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
    advance_payment_method = fields.Char(
        string="Méthode de paiement",
        copy=False,
        help="Méthode de paiement utilisée pour créer cette facture (percentage, fixed, delivered)",
    )
    downpayment_sequence = fields.Integer(
        string="Séquence d'acompte",
        default=0,
        copy=False,
        help="Numéro de séquence de l'acompte (0 si facture normale)",
    )
    downpayment_sequence_number = fields.Integer(
        string="N° Acompte",
        compute="_compute_downpayment_sequence_number",
        store=True,
        help="0 si facture normale, 1+ si acompte (pour rapport avec séquence)",
    )
    invoice_type = fields.Selection(
        [
            ("simple", "Facture Simple"),
            ("first_dp", "1er Acompte"),
            ("nth_dp", "Acompte suivant"),
            ("balance", "Facture de Solde"),
        ],
        string="Type de Facture",
        compute="_compute_invoice_type",
        store=True,
        tracking=True,
        help="Type de facture calculé à partir de advance_payment_method",
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
        store=False,
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

    @api.depends("advance_payment_method", "downpayment_sequence")
    def _compute_custom_report_template(self):
        for rec in self:
            apm = rec.advance_payment_method or ""
            seq = rec.downpayment_sequence or 0
            if apm in ("percentage", "fixed"):
                if seq <= 1:
                    rec.custom_report_template = "first_down_payment_invoice_1"
                else:
                    rec.custom_report_template = "nth_down_payment_invoice"
            elif apm == "delivered":
                rec.custom_report_template = "final_invoice"
            else:
                rec.custom_report_template = "simple_invoice_1"

    @api.depends("advance_payment_method", "downpayment_sequence")
    def _compute_invoice_type_display(self):
        for rec in self:
            apm = rec.advance_payment_method or ""
            seq = rec.downpayment_sequence or 0
            if apm in ("percentage", "fixed"):
                if seq == 1:
                    rec.invoice_type_display = "Premier acompte"
                elif seq == 2:
                    rec.invoice_type_display = "Deuxième acompte"
                elif seq == 3:
                    rec.invoice_type_display = "Troisième acompte"
                elif seq == 4:
                    rec.invoice_type_display = "Quatrième acompte"
                elif seq > 4:
                    rec.invoice_type_display = f"{seq}ème acompte"
                else:
                    rec.invoice_type_display = "Acompte"
            elif apm == "delivered":
                rec.invoice_type_display = "Facture de Solde"
            else:
                rec.invoice_type_display = "Facture Standard"

    @api.depends("downpayment_sequence")
    def _compute_downpayment_sequence_number(self):
        for rec in self:
            rec.downpayment_sequence_number = rec.downpayment_sequence or 0

    @api.depends("advance_payment_method", "downpayment_sequence")
    def _compute_invoice_type(self):
        for rec in self:
            apm = rec.advance_payment_method or ""
            seq = rec.downpayment_sequence or 0
            if apm in ("percentage", "fixed"):
                rec.invoice_type = "first_dp" if seq <= 1 else "nth_dp"
            elif apm == "delivered":
                rec.invoice_type = "balance"
            else:
                rec.invoice_type = "simple"

    @api.depends("sale_order_id", "is_downpayment", "state")
    def _compute_previous_downpayments_count(self):
        for rec in self:
            so = rec._get_source_sale_order()
            if so:
                domain = [
                    ("sale_order_id", "=", so.id),
                    ("is_downpayment", "=", True),
                    ("state", "=", "posted"),
                ]
                if rec.id:
                    domain.append(("id", "!=", rec.id))
                rec.previous_downpayments_count = self.search_count(domain)
            else:
                rec.previous_downpayments_count = 0

    @api.depends("sale_order_id", "advance_payment_method", "is_downpayment", "state")
    def _compute_is_final_payment(self):
        for rec in self:
            so = rec._get_source_sale_order()
            if so and rec.advance_payment_method == "delivered":
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

    def _compute_invoice_type_from_dp_method(self, advance_payment_method, sale_order=None):
        self.ensure_one()
        so = sale_order or self._get_source_sale_order()
        self.advance_payment_method = advance_payment_method
        if advance_payment_method in ("percentage", "fixed"):
            existing_dp = 0
            if so:
                existing_dp = self.env["account.move"].search_count([
                    ("sale_order_id", "=", so.id),
                    ("is_downpayment", "=", True),
                    ("state", "=", "posted"),
                    ("id", "!=", self.id),
                ])
            self.is_downpayment = True
            self.downpayment_sequence = existing_dp + 1
        elif advance_payment_method == "delivered":
            self.is_downpayment = False
            self.downpayment_sequence = 0
        self._compute_invoice_type_display()
        self._compute_custom_report_template()

    def action_post(self):
        res = super().action_post()
        for move in self:
            if move.is_downpayment or move.advance_payment_method in ("percentage", "fixed"):
                if not move.fac_number:
                    move.fac_number = (
                        self.env["ir.sequence"]
                        .with_company(move.company_id)
                        .next_by_code("account.move.seq_fac")
                    )
                if not move.is_downpayment:
                    move.is_downpayment = True
                if not move.downpayment_sequence:
                    so = move._get_source_sale_order()
                    if so:
                        existing_count = self.env["account.move"].search_count([
                            ("sale_order_id", "=", so.id),
                            ("is_downpayment", "=", True),
                            ("state", "=", "posted"),
                            ("id", "!=", move.id),
                        ])
                    move.downpayment_sequence = existing_count + 1
                else:
                    move.downpayment_sequence = 1
            elif move.advance_payment_method == "delivered":
                move.is_downpayment = False
                move.downpayment_sequence = 0
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
