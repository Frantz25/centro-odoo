# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cer_document_count = fields.Integer(compute="_compute_cer_document_count", string="Docs CER", store=False)

    def _compute_cer_document_count(self):
        Doc = self.env["cer.document"]
        for order in self:
            order.cer_document_count = Doc.search_count([("res_model", "=", "sale.order"), ("res_id", "=", order.id)])

    def action_view_cer_documents(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Documentos CER"),
            "res_model": "cer.document",
            "view_mode": "list,form",
            "domain": [("res_model", "=", "sale.order"), ("res_id", "=", self.id)],
            "context": {"default_res_model": "sale.order", "default_res_id": self.id},
        }

    def action_open_cer_document_create_wizard(self):
        self.ensure_one()
        ctx = dict(self.env.context or {})
        ctx.update({
            "default_res_model": "sale.order",
            "default_res_id": self.id,
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Creador Documento CER"),
            "res_model": "cer.document.create.wizard",
            "view_mode": "form",
            "target": "new",
            "context": ctx,
        }
