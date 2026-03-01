# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class CERPricingApplyWizard(models.TransientModel):
    _name = "cer.pricing.apply.wizard"
    _description = "CER Pricing Apply Wizard"

    order_id = fields.Many2one("sale.order", required=True, ondelete="cascade")
    date_from = fields.Date(string="Fecha Entrada", required=True)
    date_to = fields.Date(string="Fecha Salida", required=True)
    participants = fields.Integer(string="Participantes", default=1, required=True)
    inclusive_days = fields.Boolean(string="Días inclusivos (salones/capilla)", default=True)

    def action_apply(self):
        self.ensure_one()
        if self.participants < 0:
            raise UserError(_("Participantes no puede ser negativo."))
        if self.date_to < self.date_from:
            raise UserError(_("La Fecha Salida no puede ser menor que la Fecha Entrada."))

        self.order_id.cer_apply_pricing(
            date_from=self.date_from,
            date_to=self.date_to,
            participants=int(self.participants or 0),
            inclusive_days=bool(self.inclusive_days),
        )
        return {"type": "ir.actions.act_window_close"}
