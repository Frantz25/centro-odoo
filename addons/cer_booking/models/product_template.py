# -*- coding: utf-8 -*-
from odoo import fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    cer_reservable = fields.Boolean(
        string="CER - Reservable",
        help="Si está activo, este producto se considera un recurso reservable para control de disponibilidad (habitaciones, capilla, salón, etc.).",
    )
    cer_capacity_units = fields.Integer(
        string="CER - Capacidad (unidades)",
        default=0,
        help="Capacidad máxima de reservas simultáneas para este recurso. "
             "Ej: Habitación VIP baño=4, VIP sin baño=2, Salón=1, Capilla=1. "
             "0 = sin límite (no valida disponibilidad).",
    )
