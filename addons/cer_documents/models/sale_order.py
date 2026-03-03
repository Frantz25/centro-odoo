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

    def _cer_document_wizard_action(self, context_updates=None, title=None):
        self.ensure_one()
        ctx = dict(self.env.context or {})
        ctx.update({
            "default_res_model": "sale.order",
            "default_res_id": self.id,
        })
        if context_updates:
            ctx.update(context_updates)
        return {
            "type": "ir.actions.act_window",
            "name": title or _("Creador Documento CER"),
            "res_model": "cer.document.create.wizard",
            "view_mode": "form",
            "target": "new",
            "context": ctx,
        }

    def action_open_cer_document_create_wizard(self):
        return self._cer_document_wizard_action()

    def action_open_cer_acta_create_wizard(self):
        self.ensure_one()
        template = self.env.ref("cer_documents.cer_document_template_acta_aceptacion", raise_if_not_found=False)
        updates = {"default_template_id": template.id} if template else {}
        return self._cer_document_wizard_action(updates, _("Crear Acta de Aceptación"))
