# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    cer_units_qty = fields.Integer(
        string="Unidades Reserva",
        default=0,
        help="Cantidad de unidades del recurso reservable a bloquear (ej: 1 habitación, 1 capilla, etc.). "
             "Para camping grande puedes dejar 0 (sin control por capacidad) o un número si deseas cupos.",
    )
    cer_apply_discount = fields.Boolean(
        string="Aplicar descuento CER",
        default=True,
        help="Si está activo, al cambiar el cliente se aplicará el descuento fijo CER (cer_pricing) a esta línea.",
    )

    cer_is_reservable = fields.Boolean(
        string="Es reservable",
        related="product_id.product_tmpl_id.cer_reservable",
        store=True,
        readonly=True,
    )

    @api.onchange("product_id")
    def _onchange_product_id_cer_booking_defaults(self):
        for line in self:
            if not line.product_id or line.display_type:
                continue
            tmpl = line.product_id.product_tmpl_id
            line.cer_units_qty = 1 if tmpl.cer_reservable else 0
