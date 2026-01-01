# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    cer_discount_id = fields.Many2one(
        "cer.pricing.discount",
        string="CER - Descuento por defecto",
        help="Descuento fijo (porcentaje) que se propone automáticamente en las cotizaciones del cliente.",
    )
