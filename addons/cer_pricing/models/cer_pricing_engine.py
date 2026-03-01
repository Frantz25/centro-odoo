# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date
from odoo import api, models, _
from odoo.exceptions import UserError


class CERPricingEngine(models.AbstractModel):
    _name = "cer.pricing.engine"
    _description = "CER Pricing Engine"

    @api.model
    def compute_nights(self, date_from: date, date_to: date) -> int:
        if not date_from or not date_to:
            return 0
        return max(0, int((date_to - date_from).days))

    @api.model
    def compute_days(self, date_from: date, date_to: date, inclusive: bool = False) -> int:
        if not date_from or not date_to:
            return 0
        delta = int((date_to - date_from).days)
        if inclusive:
            return max(1, delta + 1)
        return max(1, delta) if delta >= 0 else 0

    @api.model
    def compute_line_payload(self, *, charge_mode: str, participants: int, min_people: int, date_from: date, date_to: date):
        participants = int(participants or 0)
        if participants < 0:
            raise UserError(_("Participantes no puede ser negativo."))

        nights_raw = self.compute_nights(date_from, date_to)
        # Para salones/capilla se cobra por día (inclusivo)
        days = self.compute_days(date_from, date_to, inclusive=False)

        if charge_mode == "room_person_night":
            # Si entrada == salida, cobrar 1 noche (UX)
            nights = max(1, int(nights_raw)) if (date_from and date_to and date_to >= date_from) else int(nights_raw)
            qty = float(max(0, participants) * nights)
            return {"qty": qty, "participants": participants, "nights": nights, "days": days}

        if charge_mode == "day":
            qty = float(days)
            return {"qty": qty, "participants": participants, "nights": int(nights_raw), "days": days}

        if charge_mode == "person_day":
            base = max(0, participants)
            min_people = int(min_people or 0)
            if min_people and base < min_people:
                base = min_people
            qty = float(base * days)
            return {"qty": qty, "participants": participants, "nights": int(nights_raw), "days": days}

        if charge_mode == "person":
            base = max(0, participants)
            min_people = int(min_people or 0)
            if min_people and base < min_people:
                base = min_people
            qty = float(base)
            return {"qty": qty, "participants": participants, "nights": int(nights_raw), "days": days}

        # fixed / other
        return {"qty": 1.0, "participants": participants, "nights": int(nights_raw), "days": days}
