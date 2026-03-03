# -*- coding: utf-8 -*-
from __future__ import annotations

from urllib.parse import quote

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cer_checkin_qr_img_url = fields.Char(string="QR Check-in URL (img)", compute="_compute_cer_checkin_qr_img_url")

    @api.depends("cer_booking_qr_url")
    def _compute_cer_checkin_qr_img_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        for order in self:
            if order.cer_booking_qr_url and base_url:
                encoded = quote(order.cer_booking_qr_url, safe="")
                order.cer_checkin_qr_img_url = f"{base_url}/report/barcode/QR/{encoded}?width=220&height=220"
            else:
                order.cer_checkin_qr_img_url = False

    def action_cer_send_checkin_pass(self):
        template = self.env.ref("cer_communications.mail_template_cer_booking_checkin_pass", raise_if_not_found=False)
        if not template:
            raise UserError(_("No existe la plantilla de Pase Check-in CER."))

        for order in self:
            if not order.cer_is_booking:
                raise UserError(_("La orden %s no está marcada como reserva CER.") % (order.name or "-"))
            if not order.partner_id.email:
                raise UserError(_("El cliente de %s no tiene email configurado.") % (order.name or "-"))

            template.send_mail(
                order.id,
                force_send=True,
                email_values={
                    "email_to": order.partner_id.email,
                    "recipient_ids": [(6, 0, [order.partner_id.id])],
                },
            )
            order.message_post(body=_("Pase individual de check-in enviado a <b>%s</b>.") % order.partner_id.email)
        return True

    def action_cer_booking_reserve(self):
        res = super().action_cer_booking_reserve()
        self.env["cer.communication.service"].trigger("booking_reserved", self.filtered("cer_is_booking"))
        return res

    def action_cer_booking_confirm(self):
        res = super().action_cer_booking_confirm()
        self.env["cer.communication.service"].trigger("booking_confirmed", self.filtered("cer_is_booking"))
        return res

    def action_cer_booking_cancel(self):
        res = super().action_cer_booking_cancel()
        self.env["cer.communication.service"].trigger("booking_cancelled", self.filtered("cer_is_booking"))
        return res
