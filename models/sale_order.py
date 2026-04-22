from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    proforma_signature_image = fields.Image(
        string="Signature Signataire",
        max_width=500,
        max_height=200,
    )
    proforma_signatory_name = fields.Char(
        string="Nom du Signataire",
    )
    proforma_signatory_title = fields.Char(
        string="Poste du Signataire",
    )


class SaleOrder(models.Model):
    _inherit = "sale.order"

    proforma_number = fields.Char(
        string="N° Proforma",
        readonly=True,
        copy=False,
        help="Original proforma number (PF/YYYY/NNNN), preserved after confirmation.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/" or "name" not in vals:
                vals["name"] = (
                    self.env["ir.sequence"]
                    .with_company(vals.get("company_id", self.env.company.id))
                    .next_by_code("sale.order.seq_pf")
                )
            vals["proforma_number"] = vals.get("name", "/")
        return super().create(vals_list)

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
