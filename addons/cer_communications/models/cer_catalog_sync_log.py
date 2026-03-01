# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import models


class CERCatalogSyncLog(models.Model):
    _inherit = "cer.catalog.sync.log"

    def write(self, vals):
        prev = {rec.id: rec.state for rec in self}
        res = super().write(vals)

        if "state" in vals:
            for rec in self:
                before = prev.get(rec.id)
                after = rec.state
                if before == after:
                    continue
                if after == "success":
                    self.env["cer.communication.service"].trigger("catalog_sync_success", rec)
                elif after == "failed":
                    self.env["cer.communication.service"].trigger("catalog_sync_failed", rec)
        return res
