# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError


_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_\.]+)\s*\}\}")

def _get_attr(obj, path: str):
    # soporta x.y.z
    cur = obj
    for part in path.split("."):
        if cur is None:
            return ""
        # recordset
        if hasattr(cur, "__len__") and hasattr(cur, "ids") and not isinstance(cur, (str, bytes)):
            cur = cur[:1] if len(cur) else None
            if cur is None:
                return ""
        if isinstance(cur, models.BaseModel):
            if part in cur._fields:
                cur = cur[part]
            else:
                # fallback: attribute
                cur = getattr(cur, part, "")
        else:
            cur = getattr(cur, part, "")
    # normaliza
    if isinstance(cur, models.BaseModel):
        return cur.display_name
    if isinstance(cur, (list, tuple)):
        return ", ".join([str(x) for x in cur])
    return "" if cur is None else str(cur)

def render_template(body_html: str, record):
    if not body_html:
        return ""
    def repl(m):
        key = m.group(1)
        try:
            return _get_attr(record, key)
        except Exception:
            return ""
    return _PLACEHOLDER_RE.sub(repl, body_html)


class CERDocument(models.Model):
    _name = "cer.document"
    _description = "CER Document"
    _order = "create_date desc, id desc"
    _check_company_auto = True

    name = fields.Char(required=True, default=lambda self: _("Nuevo documento"))
    number = fields.Char(string="N° Documento", copy=False, readonly=True, index=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)

    template_id = fields.Many2one(
        "cer.document.template",
        string="Plantilla",
        required=True,
        ondelete="restrict",
        check_company=True,
    )

    res_model = fields.Char(string="Modelo origen", required=True, index=True)
    res_id = fields.Integer(string="ID origen", required=True, index=True)
    res_ref = fields.Reference(
        selection=lambda self: self._reference_models(),
        string="Registro",
        compute="_compute_res_ref",
        store=False,
        readonly=True,
    )

    html_content = fields.Html(string="HTML generado", sanitize=False, readonly=True)

    state = fields.Selection([("draft", "Borrador"), ("final", "Final")], default="draft", required=True)

    def _reference_models(self):
        # limita a modelos instalados
        models_list = self.env["ir.model"].sudo().search([]).mapped("model")
        return [(m, m) for m in models_list]

    @api.depends("res_model", "res_id")
    def _compute_res_ref(self):
        for rec in self:
            rec.res_ref = False
            if rec.res_model and rec.res_id:
                rec.res_ref = "%s,%s" % (rec.res_model, rec.res_id)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("number"):
                vals["number"] = self.env["ir.sequence"].next_by_code("cer.document") or "/"
        return super().create(vals_list)

    def action_generate(self):
        for doc in self:
            record = self.env[doc.res_model].browse(doc.res_id).exists()
            if not record:
                raise UserError(_("El registro origen ya no existe (%s,%s).") % (doc.res_model, doc.res_id))
            html = render_template(doc.template_id.body_html or "", record)
            doc.write({"html_content": html, "state": "final"})
        return True

    def _attach_pdf_and_post_trace(self):
        self.ensure_one()
        report = self.env.ref("cer_documents.action_report_cer_document")
        pdf_content, report_type = report._render_qweb_pdf(report.report_name, self.ids)
        filename = "%s.pdf" % (self.number or self.name or "documento_cer")

        origin = self.env[self.res_model].browse(self.res_id).exists()
        if origin and hasattr(origin, "message_post"):
            origin.message_post(
                body=_("Documento CER generado y adjuntado: <b>%s</b>") % filename,
                attachments=[(filename, pdf_content)],
                subtype_xmlid="mail.mt_note",
            )

        if self.res_model == "sale.order" and origin and getattr(origin, "cer_booking_id", False):
            booking = origin.cer_booking_id
            booking.message_post(
                body=_("Se generó documento CER desde pedido <b>%s</b>.") % (origin.name or "-"),
                attachments=[(filename, pdf_content)],
                subtype_xmlid="mail.mt_note",
            )

        return True

    def action_print_pdf(self):
        self.ensure_one()
        if self.state != "final":
            self.action_generate()
        self._attach_pdf_and_post_trace()
        return self.env.ref("cer_documents.action_report_cer_document").report_action(self)
