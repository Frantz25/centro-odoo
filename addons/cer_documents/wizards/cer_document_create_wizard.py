# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CERDocumentCreateWizard(models.TransientModel):
    _name = "cer.document.create.wizard"
    _description = "CER Document Create Wizard"

    res_model = fields.Char(required=True)
    res_id = fields.Integer(required=True)

    template_id = fields.Many2one("cer.document.template", string="Plantilla", required=True)

    def _get_record(self):
        self.ensure_one()
        rec = self.env[self.res_model].browse(self.res_id).exists()
        if not rec:
            raise UserError(_("El registro origen ya no existe."))
        return rec

    @api.onchange("res_model")
    def _onchange_res_model(self):
        # filtra plantillas por modelo
        if self.res_model:
            model = self.env["ir.model"].sudo().search([("model", "=", self.res_model)], limit=1)
            return {"domain": {"template_id": [("model_id", "=", model.id)]}}
        return {}

    def action_create_document(self):
        self.ensure_one()
        record = self._get_record()
        doc = self.env["cer.document"].create({
            "name": "%s - %s" % (self.template_id.name, getattr(record, "name", record.display_name)),
            "company_id": getattr(record, "company_id", self.env.company).id if hasattr(record, "company_id") else self.env.company.id,
            "template_id": self.template_id.id,
            "res_model": self.res_model,
            "res_id": self.res_id,
        })
        doc.action_generate()
        return {
            "type": "ir.actions.act_window",
            "res_model": "cer.document",
            "res_id": doc.id,
            "view_mode": "form",
        }
