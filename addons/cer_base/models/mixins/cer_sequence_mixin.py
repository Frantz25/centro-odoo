# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CERSequenceMixin(models.AbstractModel):
    """Mixin CER para asignación de secuencias (reutilizable)."""

    _name = "cer.sequence.mixin"
    _description = "CER Sequence Mixin"

    _cer_sequence_auto = True

    cer_sequence = fields.Char(
        string="Referencia CER",
        index=True,
        copy=False,
        readonly=True,
    )

    def _cer_sequence_code(self) -> str:
        return ""

    def _cer_assign_sequence(self):
        for rec in self:
            if rec.cer_sequence:
                continue
            code = rec._cer_sequence_code()
            if not code:
                continue
            rec.cer_sequence = rec.env["ir.sequence"].next_by_code(code) or "/"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if getattr(records, "_cer_sequence_auto", True):
            records._cer_assign_sequence()
        return records

