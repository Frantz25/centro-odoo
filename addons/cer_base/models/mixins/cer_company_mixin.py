# -*- coding: utf-8 -*-
from odoo import fields, models


class CERCompanyMixin(models.AbstractModel):
    """Mixin estándar CER para modelos multi-compañía."""

    _name = "cer.company.mixin"
    _description = "CER Company Mixin"
    _check_company_auto = True

    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        check_company=True,
    )

