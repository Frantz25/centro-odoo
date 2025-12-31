# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cer_catalog_cron_enabled = fields.Boolean(
        string="Habilitar cron de sincronización de catálogo",
        config_parameter="cer_catalog_github.cron_enabled",
    )

    cer_catalog_source_id = fields.Many2one(
        related="company_id.cer_catalog_source_id",
        readonly=False,
    )

    cer_catalog_default_sale_tax_id = fields.Many2one(
        related="company_id.cer_catalog_default_sale_tax_id",
        readonly=False,
    )

    cer_catalog_allow_create_categories = fields.Boolean(
        related="company_id.cer_catalog_allow_create_categories",
        readonly=False,
    )

    cer_catalog_allow_create_uom = fields.Boolean(
        related="company_id.cer_catalog_allow_create_uom",
        readonly=False,
    )

    def action_cer_catalog_sync_now(self):
        self.ensure_one()
        source = self.company_id.cer_catalog_source_id
        if source:
            source.action_sync_now()
        return True
