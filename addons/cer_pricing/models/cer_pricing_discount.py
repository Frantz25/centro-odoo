# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CERPricingDiscount(models.Model):
    _name = "cer.pricing.discount"
    _description = "CER Pricing Discount"
    _order = "company_id, name, id"
    _check_company_auto = True

    active = fields.Boolean(default=True)
    name = fields.Char(required=True, index=True)
    code = fields.Char(index=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)

    discount_percent = fields.Float(string="Descuento (%)", required=True, default=0.0)

    note = fields.Text()

    @api.constrains("discount_percent")
    def _check_percent(self):
        for rec in self:
            if rec.discount_percent < 0 or rec.discount_percent > 100:
                raise ValidationError(_("El descuento debe estar entre 0% y 100%."))

    @api.constrains("company_id", "code")
    def _check_unique_code(self):
        for rec in self:
            if not rec.code:
                continue
            dup = self.search([
                ("id", "!=", rec.id),
                ("company_id", "=", rec.company_id.id),
                ("code", "=", rec.code),
            ], limit=1)
            if dup:
                raise ValidationError(_("El código de descuento debe ser único por compañía."))
