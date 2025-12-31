# -*- coding: utf-8 -*-
import os
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CERCatalogSource(models.Model):
    _name = "cer.catalog.source"
    _description = "CER Catalog Source"
    _order = "company_id, name"
    _check_company_auto = True

    active = fields.Boolean(default=True)
    name = fields.Char(required=True, index=True)

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    mode = fields.Selection(
        selection=[
            ("install", "Modo A: Deploy-time (CSV local)"),
            ("cron", "Modo B: Sync automático (cron)"),
        ],
        required=True,
        default="cron",
        index=True,
    )

    source_type = fields.Selection(
        selection=[
            ("local", "CSV local del módulo"),
            ("github_raw", "GitHub RAW / URL HTTP"),
        ],
        required=True,
        default="github_raw",
        index=True,
    )

    github_raw_url = fields.Char(
        string="URL RAW CSV",
        help="URL directa a un CSV (GitHub raw.githubusercontent.com u otra URL HTTP).",
    )

    github_token = fields.Char(
        string="Token (opcional)",
        help="Token para repos privados. Se envía como header Authorization.",
        groups="cer_base.group_cer_manager",
    )

    last_sync_at = fields.Datetime(string="Última sincronización", readonly=True)
    last_sync_state = fields.Selection(
        [("success", "Success"), ("failed", "Failed"), ("skipped", "Skipped")],
        string="Estado última sync",
        readonly=True,
    )
    last_sync_log_id = fields.Many2one("cer.catalog.sync.log", string="Último log", readonly=True)

    sync_log_count = fields.Integer(compute="_compute_sync_log_count")

    def _compute_sync_log_count(self):
        Log = self.env["cer.catalog.sync.log"]
        grouped = Log.read_group([("source_id", "in", self.ids)], ["source_id"], ["source_id"])
        mapped = {g["source_id"][0]: g["source_id_count"] for g in grouped if g.get("source_id")}
        for rec in self:
            rec.sync_log_count = mapped.get(rec.id, 0)

    def action_open_logs(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Logs de sincronización"),
            "res_model": "cer.catalog.sync.log",
            "view_mode": "list,form",
            "domain": [("source_id", "=", self.id)],
            "context": {"default_source_id": self.id},
        }

    def action_sync_from_local_file(self, local_path, initiated_by="manual"):
        self.ensure_one()
        service = self.env["cer.catalog.service"]
        return service.with_company(self.company_id).run_sync_from_local_path(self, local_path, initiated_by=initiated_by)

    def _get_local_seed_path(self):
        # Path estable relativo al módulo (permite editar el CSV en el servidor y re-sincronizar)
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "catalog_seed.csv"))

    def action_sync_now(self):
        for rec in self:
            service = rec.env["cer.catalog.service"]
            if rec.source_type == "local":
                local_path = rec._get_local_seed_path()
                if not os.path.exists(local_path):
                    raise UserError(_("No se encontró el CSV local del módulo: %s") % (local_path,))
                service.with_company(rec.company_id).run_sync_from_local_path(rec, local_path, initiated_by=f"manual-local:{rec.env.user.id}")
                continue

            if not rec.github_raw_url:
                raise UserError(_("Debes configurar la URL RAW CSV en la fuente."))
            service.with_company(rec.company_id).run_sync_from_url(rec, initiated_by=f"manual:{rec.env.user.id}")
        return True

    @api.constrains("github_raw_url", "source_type")
    def _check_url_required(self):
        for rec in self:
            if rec.source_type == "github_raw" and not rec.github_raw_url:
                raise UserError(_("La URL RAW es obligatoria para fuentes GitHub/HTTP."))
