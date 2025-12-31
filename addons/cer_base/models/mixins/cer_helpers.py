# -*- coding: utf-8 -*-
import re
from odoo import api, models


class CERHelpers(models.AbstractModel):
    """Helpers transversales (sin reglas de negocio)."""

    _name = "cer.helpers"
    _description = "CER Helpers"

    @api.model
    def cer_normalize_code(self, value: str, max_len: int = 64) -> str:
        value = (value or "").strip().lower()
        value = re.sub(r"[^a-z0-9]+", "_", value)
        value = re.sub(r"_+", "_", value).strip("_")
        return value[:max_len]

