# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CERPricingSeason(models.Model):
    _name = "cer.pricing.season"
    _description = "CER Pricing Season"
    _order = "company_id, priority desc, date_from asc, id asc"
    _check_company_auto = True

    active = fields.Boolean(default=True)
    name = fields.Char(required=True, index=True)
    code = fields.Char(required=True, index=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)

    date_from = fields.Date(required=True, index=True)
    date_to = fields.Date(required=True, index=True)
    priority = fields.Integer(default=10)
    note = fields.Text()

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise ValidationError(_("La fecha final no puede ser menor que la fecha inicial."))

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
                raise ValidationError(_("El código de temporada debe ser único por compañía."))
