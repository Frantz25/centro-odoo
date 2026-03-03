# -*- coding: utf-8 -*-
from odoo import fields, models


class CerBookingUnitLine(models.Model):
    _name = "cer.booking.unit.line"
    _description = "CER Booking Unit Line"
    _order = "id"

    booking_id = fields.Many2one("cer.booking", required=True, ondelete="cascade", index=True)
    unit_id = fields.Many2one("cer.unit", string="Unidad", ondelete="restrict")
    unit_type = fields.Selection(
        [
            ("vip_1", "VIP 1 persona"),
            ("vip_2", "VIP 2 personas"),
            ("std_4", "Estándar 4 personas"),
            ("std_5", "Estándar 5 personas"),
            ("camp_slot", "Camping (cupo)"),
            ("event_space", "Espacio de evento"),
        ],
        string="Tipo de unidad",
        required=True,
    )
    qty_assigned = fields.Integer(string="Cantidad asignada", default=1, required=True)
    check_in = fields.Date(related="booking_id.check_in", store=True, readonly=True)
    check_out = fields.Date(related="booking_id.check_out", store=True, readonly=True)
    state = fields.Selection(related="booking_id.state", store=True, readonly=True)
