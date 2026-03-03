# -*- coding: utf-8 -*-
from odoo import fields, models


class CerBookingRequestLine(models.Model):
    _name = "cer.booking.request.line"
    _description = "CER Booking Request Line"
    _order = "id"

    booking_id = fields.Many2one("cer.booking", required=True, ondelete="cascade", index=True)
    product_tmpl_id = fields.Many2one("product.template", string="Producto", ondelete="set null")
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
    qty_requested = fields.Integer(string="Cantidad solicitada", default=1, required=True)
    persons_estimated = fields.Integer(string="Personas estimadas", default=0)
    notes = fields.Char(string="Notas")
