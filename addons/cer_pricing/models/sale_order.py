# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cer_date_from = fields.Date(string="Fecha Entrada")
    cer_date_to = fields.Date(string="Fecha Salida")
    cer_participants = fields.Integer(string="Participantes", default=0)

    cer_discount_id = fields.Many2one("cer.pricing.discount", string="Descuento CER")

    cer_stay_nights = fields.Integer(string="Noches", compute="_compute_cer_stay", store=True, readonly=True)
    cer_stay_days = fields.Integer(string="Días", compute="_compute_cer_stay", store=True, readonly=True)
    cer_stay_display = fields.Char(string="Estadía", compute="_compute_cer_stay_display", store=True, readonly=True)

    @api.depends("cer_date_from", "cer_date_to")
    def _compute_cer_stay(self):
        for order in self:
            if order.cer_date_from and order.cer_date_to:
                nights = max(0, int((order.cer_date_to - order.cer_date_from).days))
                days = max(1, nights + 1)
            else:
                nights = 0
                days = 0
            order.cer_stay_nights = nights
            order.cer_stay_days = days

    @api.depends("cer_stay_days")
    def _compute_cer_stay_display(self):
        for order in self:
            order.cer_stay_display = (_("%s día(s)") % order.cer_stay_days) if order.cer_stay_days else ""

    @api.constrains("cer_date_from", "cer_date_to")
    def _check_cer_dates(self):
        for order in self:
            if order.cer_date_from and order.cer_date_to and order.cer_date_to < order.cer_date_from:
                raise ValidationError(_("La Fecha Salida no puede ser menor que la Fecha Entrada."))

    @api.onchange("partner_id")
    def _onchange_partner_id_cer_discount(self):
        for order in self:
            if order.partner_id and not order.cer_discount_id:
                # Proponer descuento por defecto del cliente
                order.cer_discount_id = order.partner_id.cer_discount_id

    @api.onchange("cer_date_from", "cer_date_to", "cer_participants", "cer_discount_id")
    def _onchange_cer_header_recompute(self):
        for order in self:
            order._cer_sync_lines()

    def _cer_find_season(self):
        self.ensure_one()
        Season = self.env["cer.pricing.season"]
        if not self.cer_date_from:
            return Season.browse()
        return Season.search([
            ("active", "=", True),
            ("company_id", "=", self.company_id.id),
            ("date_from", "<=", self.cer_date_from),
            ("date_to", ">=", self.cer_date_from),
        ], order="priority desc, id desc", limit=1)

    def _cer_sync_lines(self):
        """Recalcula (en memoria) cantidades CER y aplica tarifa/temporada + descuento a las líneas."""
        Engine = self.env["cer.pricing.engine"]
        Rate = self.env["cer.pricing.rate"]

        for order in self:
            # no hacer nada sin líneas
            lines = order.order_line.filtered(lambda l: not l.display_type and l.product_id)
            if not lines:
                continue

            season = order._cer_find_season()
            rate_map = {}
            if season:
                tmpl_ids = list(set(lines.mapped("product_id.product_tmpl_id").ids))
                rates = Rate.search([
                    ("active", "=", True),
                    ("company_id", "=", order.company_id.id),
                    ("season_id", "=", season.id),
                    ("product_tmpl_id", "in", tmpl_ids),
                ])
                rate_map = {r.product_tmpl_id.id: r.price for r in rates}

            discount_pct = float(order.cer_discount_id.discount_percent) if order.cer_discount_id else 0.0

            for line in lines:
                # Aplica precio temporada si existe
                if season:
                    rp = rate_map.get(line.product_id.product_tmpl_id.id)
                    if rp is not None:
                        line.price_unit = rp
                    line.cer_season_id = season.id

                # Aplica descuento fijo a la línea (porcentaje)
                if line.cer_apply_discount:
                    line.discount = discount_pct

                # Recalcula cantidad interna según modo (sin necesidad de wizard)
                if line.cer_auto_qty and order.cer_date_from and order.cer_date_to:
                    participants = int(line.cer_participants or order.cer_participants or 0)
                    charge_mode = line.cer_charge_mode or "fixed"
                    if (line.product_id and line.product_id.default_code == "CAMP_DAY" and charge_mode in ("person", "fixed")):
                        # Camping: cobra por persona x día y muestra duración (días) en la grilla
                        charge_mode = "person_day"
                    payload = Engine.compute_line_payload(
                        charge_mode=charge_mode,
                        participants=participants,
                        min_people=line.cer_min_people or 0,
                        date_from=order.cer_date_from,
                        date_to=order.cer_date_to,
                    )
                    line.product_uom_qty = payload.get("qty", line.product_uom_qty)
                    line.cer_qty_computed = payload.get("qty", 0.0)
                    line.cer_nights = payload.get("nights", 0)
                    line.cer_days = payload.get("days", 0)
                    line.cer_participants = payload.get("participants", participants)

    def write(self, vals):
        res = super().write(vals)
        # Recalcular al guardar si cambian campos CER clave (sin wizard)
        if set(vals).intersection({"cer_date_from", "cer_date_to", "cer_participants", "cer_discount_id", "partner_id"}):
            for order in self:
                # Evitar recursión si write viene desde sync
                if self.env.context.get("cer_skip_sync"):
                    continue
                order.with_context(cer_skip_sync=True)._cer_sync_lines()
        return res
