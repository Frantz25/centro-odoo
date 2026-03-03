# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    cer_sku = fields.Char(
        string="CER - SKU",
        index=True,
        help="Identificador estable CER para sincronización de catálogo (idempotencia).",
    )

    cer_charge_mode = fields.Selection(
        selection=[
            ("room_person_night", "Habitación: persona x noche"),
            ("day", "Salón/Capilla: por día (grupo)"),
            ("person", "Actividad/Servicio: por persona"),
            ("fixed", "Fijo"),
        ],
        string="CER - Modo de cobro",
        default="fixed",
        help="Cómo CER convierte fechas/personas en cantidad (qty) para cotizaciones/reservas.",
    )

    cer_min_people = fields.Integer(
        string="CER - Mínimo personas",
        default=0,
        help="Mínimo de personas cuando el modo de cobro es por persona (person). 0 = sin mínimo.",
    )

    cer_activity_kind = fields.Selection(
        selection=[
            ("canopy", "Canopy"),
            ("arborismo", "Arborismo"),
            ("trekking", "Trekking"),
            ("other", "Otra"),
        ],
        string="CER - Tipo de actividad",
        help="Clasificación de actividad para productos con cobro por persona.",
    )

