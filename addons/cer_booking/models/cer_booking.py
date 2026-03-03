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
    qr_url = fields.Char(string="URL QR", compute="_compute_qr_url", store=True)

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

    request_line_ids = fields.One2many("cer.booking.request.line", "booking_id", string="Solicitudes")
    unit_line_ids = fields.One2many("cer.booking.unit.line", "booking_id", string="Unidades asignadas")

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

        booking._build_request_lines_from_sale_order()
        booking._auto_assign_units()

        order.message_post(
            body=_(
                "Reserva CER creada automáticamente: <b>%(code)s</b> (offline: %(offline)s). QR: %(url)s"
            )
            % {"code": booking.booking_code, "offline": booking.offline_access_code, "url": booking.qr_url or "-"}
        )
        return booking

    @api.model
    @api.depends("offline_access_code")
    def _compute_qr_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        for rec in self:
            if rec.offline_access_code:
                rec.qr_url = f"{base_url}/cer/checkin/{rec.offline_access_code}"
            else:
                rec.qr_url = False

    def _generate_offline_access_code(self):
        # Token corto, no predecible, apto para QR offline
        return secrets.token_urlsafe(8)

    def _build_request_lines_from_sale_order(self):
        for booking in self:
            booking.request_line_ids.unlink()
            request_vals = []
            for line in booking.sale_order_id.order_line.filtered(lambda l: not l.display_type and l.product_id):
                tmpl = line.product_id.product_tmpl_id
                if not tmpl.cer_reservable or not tmpl.cer_unit_type:
                    continue
                request_vals.append(
                    {
                        "booking_id": booking.id,
                        "product_tmpl_id": tmpl.id,
                        "unit_type": tmpl.cer_unit_type,
                        "qty_requested": int(line.cer_units_qty or 1),
                        "persons_estimated": int(booking.participants or 0),
                    }
                )
            if request_vals:
                self.env["cer.booking.request.line"].create(request_vals)

    def _auto_assign_units(self):
        """Asignación básica tipo+cantidad a unidades disponibles (issue #14)."""
        Unit = self.env["cer.unit"]
        UnitLine = self.env["cer.booking.unit.line"]

        for booking in self:
            booking.unit_line_ids.unlink()
            if not booking.request_line_ids:
                continue

            used_unit_ids = self._get_overlapping_used_unit_ids(booking)
            messages = []

            for req in booking.request_line_ids:
                # Pool (camping): asignación por cantidad, sin unit_id
                pool = Unit.search(
                    [
                        ("company_id", "=", booking.company_id.id),
                        ("unit_type", "=", req.unit_type),
                        ("is_pool", "=", True),
                        ("active", "=", True),
                    ],
                    limit=1,
                )
                if pool:
                    UnitLine.create(
                        {
                            "booking_id": booking.id,
                            "unit_type": req.unit_type,
                            "qty_assigned": int(req.qty_requested or 0),
                        }
                    )
                    messages.append(_("Pool %(type)s asignado: %(qty)s") % {"type": req.unit_type, "qty": req.qty_requested})
                    continue

                # Unidades reales (habitaciones / espacios)
                available = Unit.search(
                    [
                        ("company_id", "=", booking.company_id.id),
                        ("unit_type", "=", req.unit_type),
                        ("is_pool", "=", False),
                        ("active", "=", True),
                        ("id", "not in", used_unit_ids),
                    ],
                    order="id asc",
                    limit=int(req.qty_requested or 0),
                )

                for u in available:
                    UnitLine.create(
                        {
                            "booking_id": booking.id,
                            "unit_id": u.id,
                            "unit_type": req.unit_type,
                            "qty_assigned": 1,
                        }
                    )
                    used_unit_ids.add(u.id)

                if len(available) < int(req.qty_requested or 0):
                    messages.append(
                        _("Asignación parcial %(type)s: solicitado %(req)s, asignado %(ok)s")
                        % {"type": req.unit_type, "req": req.qty_requested, "ok": len(available)}
                    )

            if messages:
                booking.message_post(body="<br/>".join(messages))

    def _get_overlapping_used_unit_ids(self, booking):
        if not booking.check_in or not booking.check_out:
            return set()

        lines = self.env["cer.booking.unit.line"].search(
            [
                ("booking_id", "!=", booking.id),
                ("unit_id", "!=", False),
                ("state", "=", "confirmed"),
                ("check_in", "<", booking.check_out),
                ("check_out", ">", booking.check_in),
            ]
        )
        return set(lines.mapped("unit_id").ids)
