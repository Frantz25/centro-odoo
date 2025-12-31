# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    cer_catalog_source_id = fields.Many2one(
        "cer.catalog.source",
        string="Fuente de catálogo CER",
        domain="[('company_id', '=', id)]",
        help="Fuente por defecto para sincronizaciones manuales desde Ajustes CER.",
    )

    cer_catalog_default_sale_tax_id = fields.Many2one(
        "account.tax",
        string="Impuesto venta por defecto",
        domain="[('type_tax_use', '=', 'sale')]",
        help="Se usa cuando el CSV no trae columna 'tax' o viene vacía.",
    )

    cer_catalog_allow_create_categories = fields.Boolean(
        string="Crear categorías automáticamente",
        default=True,
        help="Si está activo, se crean categorías faltantes a partir de la columna 'categ'.",
    )

    cer_catalog_allow_create_uom = fields.Boolean(
        string="Permitir fallback UoM (no crea UoM)",
        default=False,
        help="Si está activo y el UoM no existe, se usa 'Units' y se registra en log (no crea UoM).",
    )
