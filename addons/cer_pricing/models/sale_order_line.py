# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    cer_auto_qty = fields.Boolean(string="CER - Qty automática", default=True)
    cer_apply_discount = fields.Boolean(string="CER - Aplica descuento", default=True)

    cer_participants = fields.Integer(string="Cantidad de Personas", default=0)

    cer_nights = fields.Integer(string="CER - Noches", readonly=True, copy=False)
    cer_days = fields.Integer(string="CER - Días", readonly=True, copy=False)
    cer_qty_computed = fields.Float(string="CER - Cantidad calculada", readonly=True, copy=False)

    cer_duration_display = fields.Char(string="Noches y/o Días", compute="_compute_cer_duration_display", store=False)
    cer_price_unit_excl_tax = fields.Monetary(
        string="Precio unitario",
        compute="_compute_cer_price_unit_excl_tax",
        store=True,
        readonly=True,
        currency_field="currency_id",
    )

    cer_season_id = fields.Many2one(
        "cer.pricing.season",
        string="CER - Temporada aplicada",
        readonly=True,
        copy=False,
        check_company=True,
    )

    cer_charge_mode = fields.Selection(related="product_id.product_tmpl_id.cer_charge_mode", store=True, readonly=True)
    cer_min_people = fields.Integer(related="product_id.product_tmpl_id.cer_min_people", store=True, readonly=True)

    @api.depends("cer_charge_mode", "order_id.cer_date_from", "order_id.cer_date_to", "order_id.cer_stay_nights", "order_id.cer_stay_days", "cer_nights", "cer_days")
    def _compute_cer_duration_display(self):
        for line in self:
            if not (line.order_id.cer_date_from and line.order_id.cer_date_to):
                line.cer_duration_display = ""
                continue

            # Camping por día: mostrar días
            if line.product_id and line.product_id.default_code == "CAMP_DAY":
                days = line.order_id.cer_stay_days or line.cer_days or 0
                line.cer_duration_display = str(int(max(1, days)))
                continue

            if line.cer_charge_mode == "room_person_night":
                nights = line.order_id.cer_stay_nights or line.cer_nights or 0
                line.cer_duration_display = str(int(max(1, nights)))
            elif line.cer_charge_mode == "day":
                days = line.order_id.cer_stay_days or line.cer_days or 0
                line.cer_duration_display = str(int(max(1, days)))
            else:
                line.cer_duration_display = ""


    @api.depends("price_subtotal", "product_uom_qty", "currency_id")
    def _compute_cer_price_unit_excl_tax(self):
        for line in self:
            qty = float(line.product_uom_qty or 0.0)
            unit = (line.price_subtotal / qty) if qty else 0.0
            line.cer_price_unit_excl_tax = line.currency_id.round(unit) if line.currency_id else unit

    @api.onchange("product_id")
    def _onchange_product_id_cer_defaults(self):
        for line in self:
            if not line.product_id or line.display_type:
                continue
            # Por defecto, si es fixed, no recalcula qty
            if (line.cer_charge_mode or "fixed") == "fixed":
                line.cer_auto_qty = False

    @api.onchange("cer_participants", "cer_auto_qty")
    def _onchange_cer_participants_recompute(self):
        for line in self:
            if line.order_id:
                line.order_id._cer_sync_lines()
