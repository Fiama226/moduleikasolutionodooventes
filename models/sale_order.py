from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = "res.company"

    proforma_signature_image = fields.Image(
        string="Signature ",
        max_width=500,
        max_height=200,
    )
    proforma_signatory_name = fields.Char(
        string="Nom  Complet",
    )
    proforma_signatory_title = fields.Char(
        string="Titre",
    )


class ResPartner(models.Model):
    _inherit = "res.partner"

    partner_rccm = fields.Char(string="N° RCCM")
    partner_ifu = fields.Char(string="N° IFU")
    partner_division_fiscale = fields.Selection(
        selection=[
            ("cme", "CME - Contribution des Micro Entreprises"),
            ("rsi", "RSI - Régime Simplifié d'Imposition"),
            ("rni", "RNI - Réel Normal d'Imposition"),
        ],
        string="Division Fiscale",
    )
    partner_regime_fiscal = fields.Char(string="Régime Fiscal")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    proforma_number = fields.Char(
        string="N° Proforma",
        readonly=True,
        copy=False,
        help="Original proforma number (PF/YYYY/NNNN), preserved after confirmation.",
    )
    proforma_object = fields.Char(
        string="Objet",
        required=True,
        help="Objet de la proforma (ex: Fourniture de matériel informatique)",
    )
    note = fields.Html(
        default="La présente proforma est établie en vue de la fourniture des produits et/ou services y décrits. "
        "Elle est valable pendant une durée de 30 jours à compter de la date d'émission. "
        "Toute commande résultant de cette proforma sera soumise aux conditions générales de vente de la société.",
    )
    proforma_signed = fields.Selection(
        [
            ("unsigned", "Non signé"),
            ("signed", "Signé"),
        ],
        string="Proforma signée",
        default="unsigned",
        help="Choisir si la proforma doit être imprimée signée ou non.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("proforma_object"):
                vals["name"] = "/"
            else:
                if vals.get("name", "/") == "/" or "name" not in vals:
                    vals["name"] = (
                        self.env["ir.sequence"]
                        .with_company(vals.get("company_id", self.env.company.id))
                        .next_by_code("sale.order.seq_pf")
                    )
                vals["proforma_number"] = vals.get("name", "/")
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        for order in self:
            if order.proforma_object and not order.proforma_number and order.state in ("draft", "sent"):
                if order.name == "/" or not order.name:
                    order.name = (
                        self.env["ir.sequence"]
                        .with_company(order.company_id)
                        .next_by_code("sale.order.seq_pf")
                    )
                    order.proforma_number = order.name
        return res

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            if not order.proforma_number:
                order.proforma_number = order.name
            order.name = (
                self.env["ir.sequence"]
                .with_company(order.company_id)
                .next_by_code("sale.order.seq_bc")
            )
        return res

    def _get_report_bon_commande(self):
        self.ensure_one()
        if self.state not in ("sale", "done"):
            raise UserError(
                _("Le Bon de Commande ne peut être imprimé que pour une commande confirmée (Proforma validée).")
            )

    def action_print_sale_document(self):
        self.ensure_one()
        return self.env.ref("landry_ika_odoo_module.action_report_sale_order").report_action(self)
