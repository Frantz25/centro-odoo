# -*- coding: utf-8 -*-
from datetime import date

from odoo.tests.common import TransactionCase


class TestCERPricingEngine(TransactionCase):
    def setUp(self):
        super().setUp()
        self.engine = self.env["cer.pricing.engine"]

    def test_room_person_night_qty(self):
        payload = self.engine.compute_line_payload(
            charge_mode="room_person_night",
            participants=4,
            min_people=0,
            date_from=date(2026, 3, 10),
            date_to=date(2026, 3, 12),  # 2 noches
        )
        self.assertEqual(payload["qty"], 8.0)

    def test_day_qty(self):
        payload = self.engine.compute_line_payload(
            charge_mode="day",
            participants=0,
            min_people=0,
            date_from=date(2026, 3, 10),
            date_to=date(2026, 3, 13),  # 3 días
        )
        self.assertEqual(payload["qty"], 3.0)

    def test_person_with_minimum_qty(self):
        payload = self.engine.compute_line_payload(
            charge_mode="person",
            participants=10,
            min_people=40,
            date_from=date(2026, 3, 10),
            date_to=date(2026, 3, 11),
        )
        self.assertEqual(payload["qty"], 40.0)
