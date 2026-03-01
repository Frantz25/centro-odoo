# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

EVENT_SELECTION = [
    ("booking_reserved", "Reserva - Reservada"),
    ("booking_confirmed", "Reserva - Confirmada"),
    ("booking_cancelled", "Reserva - Cancelada"),
    ("catalog_sync_success", "Catálogo - Sync OK"),
    ("catalog_sync_failed", "Catálogo - Sync Falló"),
    ("document_finalized", "Documento - Finalizado"),
    ("sale_validity_reminder", "Cotización - Recordatorio Vigencia"),
    ("sale_portal_accepted", "Portal - Aceptada"),
    ("sale_portal_rejected", "Portal - Rechazada"),
]

RECIPIENT_MODE = [
    ("customer", "Cliente (partner_id)"),
    ("salesperson", "Vendedor (user_id)"),
    ("followers", "Seguidores (followers)"),
    ("company", "Correo de Compañía"),
    ("custom", "Emails personalizados"),
]


class CERCommunicationRule(models.Model):
    _name = "cer.communication.rule"
    _description = "CER - Regla de comunicación"
    _order = "sequence asc, id asc"
    _check_company_auto = True

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    name = fields.Char(required=True)

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        check_company=True,
        index=True,
    )

    # Odoo 19: ir.model NO soporta ondelete='restrict' aquí.
    model_id = fields.Many2one(
        "ir.model",
        string="Modelo",
        required=True,
        index=True,
        ondelete="cascade",
    )
    event_code = fields.Selection(EVENT_SELECTION, string="Evento", required=True, index=True)

    channel_email = fields.Boolean(string="Enviar Email", default=True)
    channel_chatter = fields.Boolean(string="Publicar en Chatter", default=True)

    template_id = fields.Many2one(
        "mail.template",
        string="Plantilla",
        required=True,
        domain="[('model_id', '=', model_id)]",
        help="Se usa para email y para generar el cuerpo del mensaje en chatter.",
    )

    recipient_mode = fields.Selection(RECIPIENT_MODE, string="Destinatarios", default="customer", required=True)
    custom_emails = fields.Char(
        string="Emails personalizados",
        help="Separados por coma. Solo si Destinatarios = 'Emails personalizados'.",
    )
    extra_partner_ids = fields.Many2many("res.partner", string="Destinatarios adicionales")

    force_send = fields.Boolean(
        string="Enviar inmediatamente",
        default=False,
        help="Si está desmarcado, el correo queda en cola (mail.queue) y lo envía el cron estándar.",
    )

    note = fields.Text(string="Notas")

    @api.constrains("channel_email", "channel_chatter")
    def _check_channels(self):
        for rec in self:
            if not rec.channel_email and not rec.channel_chatter:
                raise ValidationError(_("Debe activar al menos un canal (Email o Chatter)."))

    @api.constrains("recipient_mode", "custom_emails")
    def _check_custom_emails(self):
        for rec in self:
            if rec.recipient_mode == "custom" and not (rec.custom_emails or "").strip():
                raise ValidationError(_("Debe indicar 'Emails personalizados' si el modo de destinatarios es personalizado."))

    @api.constrains("company_id", "model_id", "event_code", "sequence")
    def _check_unique_rule(self):
        for rec in self:
            if not (rec.company_id and rec.model_id and rec.event_code):
                continue
            domain = [
                ("id", "!=", rec.id),
                ("company_id", "=", rec.company_id.id),
                ("model_id", "=", rec.model_id.id),
                ("event_code", "=", rec.event_code),
                ("sequence", "=", rec.sequence),
            ]
            if self.search_count(domain):
                raise ValidationError(_("Ya existe una regla igual (compañía/modelo/evento/secuencia)."))
