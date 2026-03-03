# -*- coding: utf-8 -*-
from __future__ import annotations

import secrets

from odoo import api, fields, models, _


class CerBooking(models.Model):
    _name = "cer.booking"
    _description = "CER Booking"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Cotización/Pedido",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        related="sale_order_id.partner_id",
        string="Cliente",
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        related="sale_order_id.company_id",
        store=True,
        readonly=True,
    )

    booking_code = fields.Char(
        string="Código Reserva",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        tracking=True,
    )
    offline_access_code = fields.Char(
        string="Código Acceso Offline",
        required=True,
        copy=False,
        readonly=True,
        index=True,
    )

    check_in = fields.Date(related="sale_order_id.cer_date_from", store=True, readonly=True)
    check_out = fields.Date(related="sale_order_id.cer_date_to", store=True, readonly=True)
    participants = fields.Integer(related="sale_order_id.cer_participants", store=True, readonly=True)

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("confirmed", "Confirmada"),
            ("cancelled", "Cancelada"),
        ],
        string="Estado",
        default="confirmed",
        required=True,
        tracking=True,
    )

    _sql_constraints = [
        ("cer_booking_sale_order_unique", "unique(sale_order_id)", "Ya existe una reserva CER para esta cotización/pedido."),
        ("cer_booking_code_unique", "unique(booking_code)", "El código de reserva debe ser único."),
        ("cer_booking_offline_code_unique", "unique(offline_access_code)", "El código de acceso offline debe ser único."),
    ]

    @api.model
    def create_from_sale_order(self, order):
        """Crea (idempotente) una reserva CER desde sale.order."""
        self = self.sudo()
        existing = self.search([("sale_order_id", "=", order.id)], limit=1)
        if existing:
            return existing

        booking = self.create(
            {
                "sale_order_id": order.id,
                "booking_code": self.env["ir.sequence"].next_by_code("cer.booking") or _("RESERVA"),
                "offline_access_code": self._generate_offline_access_code(),
                "state": "confirmed",
            }
        )

        order.message_post(
            body=_(
                "Reserva CER creada automáticamente: <b>%(code)s</b> (offline: %(offline)s)."
            )
            % {"code": booking.booking_code, "offline": booking.offline_access_code}
        )
        return booking

    @api.model
    def _generate_offline_access_code(self):
        # Token corto, no predecible, apto para QR offline
        return secrets.token_urlsafe(8)
