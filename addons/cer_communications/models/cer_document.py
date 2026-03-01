# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import models


class CERDocument(models.Model):
    _inherit = "cer.document"

    def action_generate(self):
        res = super().action_generate()
        finals = self.filtered(lambda d: d.state == "final")
        if finals:
            self.env["cer.communication.service"].trigger("document_finalized", finals)
        return res

    def write(self, vals):
        prev = {rec.id: rec.state for rec in self}
        res = super().write(vals)
        if "state" in vals:
            finals = self.filtered(lambda d: prev.get(d.id) != "final" and d.state == "final")
            if finals:
                self.env["cer.communication.service"].trigger("document_finalized", finals)
        return res
