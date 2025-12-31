# -*- coding: utf-8 -*-
from odoo import fields, models


class CERCatalogSyncLog(models.Model):
    _name = "cer.catalog.sync.log"
    _description = "CER Catalog Sync Log"
    _order = "create_date desc, id desc"
    _check_company_auto = True

    name = fields.Char(required=True, index=True)

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    source_id = fields.Many2one(
        "cer.catalog.source",
        required=True,
        ondelete="cascade",
        index=True,
    )

    initiated_by = fields.Char(index=True)

    state = fields.Selection(
        [("success", "Success"), ("failed", "Failed"), ("skipped", "Skipped")],
        required=True,
        default="success",
        index=True,
    )

    started_at = fields.Datetime(readonly=True)
    finished_at = fields.Datetime(readonly=True)
    duration_ms = fields.Integer(readonly=True)

    created_count = fields.Integer(readonly=True)
    updated_count = fields.Integer(readonly=True)
    skipped_count = fields.Integer(readonly=True)

    message = fields.Text(readonly=True)
    error_message = fields.Text(readonly=True)
    error_trace = fields.Text(readonly=True)

    url = fields.Char(readonly=True)
    filename = fields.Char(readonly=True)
