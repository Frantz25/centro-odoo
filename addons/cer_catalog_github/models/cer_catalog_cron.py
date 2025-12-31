# -*- coding: utf-8 -*-
from odoo import models, fields


class CERCatalogCron(models.TransientModel):
    _name = "cer.catalog.cron"
    _description = "CER Catalog Cron Entrypoint"

    def _cron_run(self):
        icp = self.env["ir.config_parameter"].sudo()
        enabled = (icp.get_param("cer_catalog_github.cron_enabled", default="False") or "False") == "True"
        if not enabled:
            return True

        Source = self.env["cer.catalog.source"].sudo()
        service = self.env["cer.catalog.service"].sudo()

        sources = Source.search([
            ("active", "=", True),
            ("mode", "=", "cron"),
            ("source_type", "=", "github_raw"),
        ], limit=50)

        for src in sources:
            if not src.github_raw_url:
                continue
            if src.last_sync_at and (fields.Datetime.now() - src.last_sync_at).total_seconds() < 1800:
                continue
            service.with_company(src.company_id).run_sync_from_url(src, initiated_by="cron:cer_catalog")
        return True
