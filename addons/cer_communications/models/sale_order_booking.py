# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

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
