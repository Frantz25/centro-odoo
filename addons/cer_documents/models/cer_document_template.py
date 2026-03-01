# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CERDocumentTemplate(models.Model):
    _name = "cer.document.template"
    _description = "CER Document Template"
    _order = "company_id, name, id"
    _check_company_auto = True

    active = fields.Boolean(default=True)
    name = fields.Char(required=True, index=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    model_id = fields.Many2one(
        "ir.model",
        string="Modelo",
        required=True,
        ondelete="cascade",
        index=True,
    )

    # HTML con placeholders tipo {{ field }} (soporta dot: partner_id.name)
    body_html = fields.Html(string="Contenido (HTML)", sanitize=False, translate=False)

    note = fields.Text(string="Notas internas")

    @api.constrains("name")
    def _check_name(self):
        for rec in self:
            if rec.name and len(rec.name.strip()) < 2:
                raise ValidationError(_("El nombre de la plantilla es demasiado corto."))
