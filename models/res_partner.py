from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    sd_reports_history_count = fields.Integer(
        string="History Items",
        compute="_compute_sd_reports_history_count",
    )

    def _compute_sd_reports_history_count(self):
        SaleOrder = self.env["sale.order"]
        for partner in self:
            partner.sd_reports_history_count = SaleOrder.search_count(
                [("partner_id", "child_of", partner.id)]
            )

    def action_open_sd_reports_history(self):
        self.ensure_one()
        wizard = self.env["sd.reports.history.wizard"].create_from_partner(self)
        return {
            "type": "ir.actions.act_window",
            "name": "Reports History",
            "res_model": "sd.reports.history.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }
