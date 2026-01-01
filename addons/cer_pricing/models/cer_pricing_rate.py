# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CERPricingRate(models.Model):
    _name = "cer.pricing.rate"
    _description = "CER Pricing Rate"
    _order = "company_id, season_id, product_tmpl_id"
    _check_company_auto = True

    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    season_id = fields.Many2one("cer.pricing.season", required=True, ondelete="cascade", check_company=True, index=True)

    product_tmpl_id = fields.Many2one(
        "product.template",
        required=True,
        ondelete="cascade",
        check_company=True,
        index=True,
        domain="[('sale_ok','=',True)]",
    )

    currency_id = fields.Many2one("res.currency", related="company_id.currency_id", store=True, readonly=True)
    price = fields.Float(required=True)

    @api.constrains("price")
    def _check_price(self):
        for rec in self:
            if rec.price < 0:
                raise ValidationError(_("El precio no puede ser negativo."))

    @api.constrains("company_id", "season_id", "product_tmpl_id")
    def _check_unique_rate(self):
        for rec in self:
            if not rec.season_id or not rec.product_tmpl_id:
                continue
            dup = self.search([
                ("id", "!=", rec.id),
                ("company_id", "=", rec.company_id.id),
                ("season_id", "=", rec.season_id.id),
                ("product_tmpl_id", "=", rec.product_tmpl_id.id),
            ], limit=1)
            if dup:
                raise ValidationError(_("Ya existe una tarifa para ese producto y temporada."))
