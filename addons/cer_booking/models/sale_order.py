# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import defaultdict

from urllib.parse import quote

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

ICP_DEPOSIT_PERCENT_KEY = "cer_base.default_deposit_percent"
ICP_POLICY_MANDATORY_KEY = "cer_base.policy_mandatory"


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cer_is_booking = fields.Boolean(string="Es Reserva CER", default=False, index=True)

    cer_booking_state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("reserved", "Reservada"),
            ("confirmed", "Confirmada"),
            ("cancelled", "Cancelada"),
        ],
        string="Estado Reserva",
        default="draft",
        copy=False,
        index=True,
    )

    cer_booking_name = fields.Char(string="N° Reserva", copy=False, readonly=True, index=True)
    cer_booking_id = fields.Many2one("cer.booking", string="Reserva CER", copy=False, readonly=True)
    cer_booking_offline_code = fields.Char(related="cer_booking_id.offline_access_code", string="Código Offline", readonly=True)
    cer_booking_qr_url = fields.Char(related="cer_booking_id.qr_url", string="URL QR", readonly=True)
    cer_booking_qr_html = fields.Html(string="QR Check-in", compute="_compute_cer_booking_qr_html", sanitize=False)

    cer_booking_overbooking = fields.Boolean(
        string="Permitir sobre-reserva",
        default=False,
        help="Si está activo, permite reservar aunque la disponibilidad esté excedida (solo managers).",
    )

    cer_policy_accepted = fields.Boolean(string="Políticas aceptadas", copy=False, default=False)
    cer_policy_accepted_at = fields.Datetime(string="Fecha aceptación políticas", copy=False, readonly=True)
    cer_policy_accepted_by_partner_id = fields.Many2one("res.partner", string="Aceptado por", copy=False, readonly=True)

    @api.depends("cer_booking_qr_url")
    def _compute_cer_booking_qr_html(self):
        for order in self:
            if order.cer_booking_qr_url:
                encoded = quote(order.cer_booking_qr_url, safe="")
                order.cer_booking_qr_html = (
                    f"<img src='/report/barcode/QR/{encoded}?width=180&height=180' "
                    "style='max-width:180px;max-height:180px;'/>"
                )
            else:
                order.cer_booking_qr_html = False

    def _cer_booking_require_dates(self):
        for order in self:
            if not order.cer_date_from or not order.cer_date_to:
                raise UserError(_("Debes indicar Fecha Entrada y Fecha Salida para reservar."))
            if order.cer_date_to < order.cer_date_from:
                raise ValidationError(_("La Fecha Salida no puede ser menor que la Fecha Entrada."))

    def _cer_get_deposit_percent_required(self):
        self.ensure_one()
        icp = self.env["ir.config_parameter"].sudo()
        scoped = icp.get_param(f"{ICP_DEPOSIT_PERCENT_KEY}__company_{self.company_id.id}", default=None)
        if scoped not in (None, ""):
            return float(scoped or 0.0)
        return float(icp.get_param(ICP_DEPOSIT_PERCENT_KEY, 50.0) or 50.0)

    def _cer_get_paid_amount(self):
        self.ensure_one()
        paid = 0.0
        invoices = self.invoice_ids.filtered(lambda m: m.state == "posted")
        for inv in invoices:
            current_paid = max((inv.amount_total or 0.0) - (inv.amount_residual or 0.0), 0.0)
            if inv.move_type in ("out_invoice", "out_receipt"):
                paid += current_paid
            elif inv.move_type == "out_refund":
                paid -= current_paid
        return max(paid, 0.0)

    def _cer_assert_minimum_deposit_for_reservation(self):
        for order in self:
            if not order.cer_is_booking:
                continue
            required_percent = order._cer_get_deposit_percent_required()
            required_amount = (order.amount_total or 0.0) * (required_percent / 100.0)
            paid_amount = order._cer_get_paid_amount()
            if paid_amount + 1e-6 < required_amount:
                raise UserError(
                    _("No se puede reservar sin abono mínimo. Requerido: %(pct)s%% (%(req).2f). Pagado: %(paid).2f")
                    % {"pct": required_percent, "req": required_amount, "paid": paid_amount}
                )

    def _cer_is_policy_mandatory(self):
        val = self.env["ir.config_parameter"].sudo().get_param(ICP_POLICY_MANDATORY_KEY, "False")
        return str(val).lower() in ("1", "true", "yes", "on")

    def _cer_assert_policy_accepted(self):
        if not self._cer_is_policy_mandatory():
            return True
        for order in self:
            if order.cer_is_booking and not order.cer_policy_accepted:
                raise UserError(_("Debes aceptar las políticas del recinto antes de reservar/confirmar."))
        return True

    def _cer_booking_overlap_domain(self, date_from, date_to):
        # Overlap: other_from < date_to AND other_to > date_from
        return [
            ("cer_is_booking", "=", True),
            ("cer_booking_state", "in", ["reserved", "confirmed"]),
            ("cer_date_from", "<", date_to),
            ("cer_date_to", ">", date_from),
        ]

    def _cer_check_availability(self):
        """Valida disponibilidad por producto reservable según cer_capacity_units."""
        Sol = self.env["sale.order.line"]

        for order in self:
            if not order.cer_is_booking:
                continue

            order._cer_booking_require_dates()
            date_from = order.cer_date_from
            date_to = order.cer_date_to

            wanted_by_tmpl = defaultdict(int)
            for line in order.order_line.filtered(lambda l: not l.display_type and l.product_id and l.cer_units_qty):
                tmpl = line.product_id.product_tmpl_id
                if not tmpl.cer_reservable:
                    continue
                if tmpl.cer_capacity_units and tmpl.cer_capacity_units > 0:
                    wanted_by_tmpl[tmpl.id] += int(line.cer_units_qty or 0)

            if not wanted_by_tmpl:
                continue

            tmpl_ids = list(wanted_by_tmpl.keys())

            other_lines = Sol.search([
                ("order_id", "!=", order.id),
                ("product_id.product_tmpl_id", "in", tmpl_ids),
                ("cer_units_qty", ">", 0),
                ("order_id.company_id", "=", order.company_id.id),
                *order._cer_booking_overlap_domain(date_from, date_to),
            ])

            used_by_tmpl = defaultdict(int)
            for l in other_lines:
                used_by_tmpl[l.product_id.product_tmpl_id.id] += int(l.cer_units_qty or 0)

            problems = []
            tmpls = self.env["product.template"].browse(tmpl_ids)
            for tmpl in tmpls:
                cap = int(tmpl.cer_capacity_units or 0)
                if cap <= 0:
                    continue
                used = int(used_by_tmpl.get(tmpl.id, 0))
                wanted = int(wanted_by_tmpl.get(tmpl.id, 0))
                if used + wanted > cap:
                    problems.append(
                        _("%(prod)s: capacidad %(cap)s, ya reservado %(used)s, intentas %(wanted)s (exceso %(over)s).") % {
                            "prod": tmpl.display_name,
                            "cap": cap,
                            "used": used,
                            "wanted": wanted,
                            "over": (used + wanted - cap),
                        }
                    )

            if problems:
                raise UserError(_("No hay disponibilidad para esas fechas:\n- %s") % "\n- ".join(problems))

    def _cer_apply_partner_discount_to_lines(self, partner):
        """Aplica descuento CER (porcentaje) a líneas marcadas con cer_apply_discount."""
        # Dependemos de cer_pricing: partner.cer_discount_id.discount_percent
        disc = 0.0
        if partner and partner._fields.get("cer_discount_id") and partner.cer_discount_id:
            disc = float(getattr(partner.cer_discount_id, "discount_percent", 0.0) or 0.0)

        for order in self:
            for line in order.order_line.filtered(lambda l: not l.display_type and l.cer_apply_discount and l.product_id):
                # No forzamos si ya editaron el descuento manualmente.
                if not line.discount:
                    line.discount = disc

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order, vals in zip(orders, vals_list):
            if vals.get("cer_is_booking"):
                order._cer_booking_assign_number()
        return orders

    def write(self, vals):
        res = super().write(vals)

        if "partner_id" in vals:
            for order in self:
                order._cer_apply_partner_discount_to_lines(order.partner_id)

        # Si ya está reservada/confirmada y cambian fechas/líneas, validamos disponibilidad
        if any(k in vals for k in ("cer_date_from", "cer_date_to", "order_line", "cer_is_booking", "cer_booking_state")):
            for order in self:
                if order.cer_is_booking and order.cer_booking_state in ("reserved", "confirmed") and not order.cer_booking_overbooking:
                    order._cer_check_availability()

        return res

    def _cer_ensure_booking_created(self):
        """Crea reserva CER al confirmar (idempotente)."""
        Booking = self.env["cer.booking"]
        for order in self:
            if not order.cer_is_booking:
                continue
            booking = Booking.create_from_sale_order(order)
            order.cer_booking_id = booking.id
            if not order.cer_booking_name:
                order.cer_booking_name = booking.booking_code

    def action_confirm(self):
        booking_orders = self.filtered("cer_is_booking")

        # A1: validaciones previas obligatorias para evitar confirmar ventas inválidas.
        for order in booking_orders:
            order._cer_assert_policy_accepted()
            order._cer_assert_minimum_deposit_for_reservation()
            if not order.cer_booking_overbooking:
                order._cer_check_availability()

        res = super().action_confirm()

        for order in booking_orders:
            order._cer_ensure_booking_created()
            if order.cer_booking_state != "cancelled":
                order.cer_booking_state = "confirmed"

        return res

    def action_quotation_accept(self):
        res = super().action_quotation_accept()
        booking_orders = self.filtered("cer_is_booking")
        if booking_orders and "cer.communication.service" in self.env:
            self.env["cer.communication.service"].trigger("sale_portal_accepted", booking_orders)
        for order in booking_orders:
            partner = self.env.user.partner_id if self.env.user else False
            order.write({
                "cer_policy_accepted": True,
                "cer_policy_accepted_at": fields.Datetime.now(),
                "cer_policy_accepted_by_partner_id": partner.id if partner else False,
            })
            try:
                order._cer_assert_policy_accepted()
                order._cer_assert_minimum_deposit_for_reservation()
                order._cer_ensure_booking_created()
                if order.cer_booking_state != "cancelled":
                    order.cer_booking_state = "confirmed"
            except UserError as e:
                order.message_post(body=_("Cotización aceptada, pero reserva CER pendiente: %s") % e.args[0])
        return res

    def _cer_booking_assign_number(self):
        for order in self:
            if not order.cer_booking_name:
                order.cer_booking_name = self.env["ir.sequence"].next_by_code("cer.booking") or _("RESERVA")

    def action_cer_mark_as_booking(self):
        for order in self:
            if order.state not in ("draft", "sent"):
                raise UserError(_("Solo puedes marcar como Reserva CER una cotización en borrador/enviada."))
            order.cer_is_booking = True
            order.cer_booking_state = "draft"
            order._cer_booking_assign_number()
            order.message_post(body=_("Marcada como **Reserva CER** (%s).") % (order.cer_booking_name or ""))

    def action_cer_unmark_booking(self):
        for order in self:
            if order.cer_booking_state in ("reserved", "confirmed"):
                raise UserError(_("No puedes desmarcar una reserva ya reservada/confirmada. Cancélala primero."))
            order.cer_is_booking = False
            order.cer_booking_state = "draft"
            order.message_post(body=_("Desmarcada como Reserva CER."))

    def action_cer_booking_reserve(self):
        for order in self:
            if not order.cer_is_booking:
                raise UserError(_("Esta orden no está marcada como Reserva CER."))
            if order.cer_booking_state not in ("draft",):
                raise UserError(_("Solo puedes reservar desde estado Borrador."))

            order._cer_assert_policy_accepted()
            order._cer_assert_minimum_deposit_for_reservation()
            order._cer_check_availability()

            order.cer_booking_state = "reserved"
            order.message_post(body=_("Reserva **reservada** para %(from)s → %(to)s.") % {
                "from": order.cer_date_from,
                "to": order.cer_date_to,
            })

    def action_cer_booking_confirm(self):
        for order in self:
            if not order.cer_is_booking:
                raise UserError(_("Esta orden no está marcada como Reserva CER."))
            if order.cer_booking_state != "reserved":
                raise UserError(_("Primero debes dejar la reserva en estado Reservada."))

            order._cer_assert_policy_accepted()
            order._cer_assert_minimum_deposit_for_reservation()
            # Confirmar venta estándar
            order.action_confirm()
            order.cer_booking_state = "confirmed"
            order.message_post(body=_("Reserva **confirmada** (venta confirmada)."))

    def action_cer_booking_cancel(self):
        for order in self:
            if not order.cer_is_booking:
                continue
            if order.cer_booking_state == "confirmed" and order.state not in ("cancel",):
                # opcionalmente podrías cancelar la venta, pero lo dejamos explícito
                raise UserError(_("Para cancelar una reserva confirmada, primero cancela el pedido de venta."))
            order.cer_booking_state = "cancelled"
            order.message_post(body=_("Reserva **cancelada**."))

    def action_cancel(self):
        res = super().action_cancel()
        for order in self.filtered("cer_is_booking"):
            # Si cancelan el sale.order, marcamos booking cancelado
            order.cer_booking_state = "cancelled"
        return res
