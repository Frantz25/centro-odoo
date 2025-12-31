# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


ICP_VALIDITY_DAYS_KEY = "cer_base.quote_validity_days"
ICP_DEPOSIT_PERCENT_KEY = "cer_base.default_deposit_percent"


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # ----------------------------
    # Parámetros CER (por compañía)
    # ----------------------------
    cer_default_deposit_percent = fields.Float(
        string="Abono por defecto (%)",
        help="Porcentaje de abono inicial sugerido por CER. Se guarda por compañía.",
    )

    cer_quote_validity_days = fields.Integer(
        string="Vigencia de cotización (días)",
        help="Días de vigencia para cotizaciones CER. Se guarda por compañía.",
    )

    # ----------------------------
    # Parámetros CER (globales)
    # ----------------------------
    cer_policy_mandatory = fields.Boolean(
        string="Políticas obligatorias",
        help="Si está activo, la suite exigirá aceptación explícita de políticas CER.",
        config_parameter="cer_base.policy_mandatory",
    )

    # ----------------------------
    # Helpers: keys por compañía
    # ----------------------------
    @api.model
    def _cer_scoped_key(self, key: str, company_id: int) -> str:
        return f"{key}__company_{company_id}"

    @api.model
    def _cer_get_param(self, key: str, default=None):
        """Lee ICP con scope por compañía cuando exista; si no, usa el key global."""
        company = self.env.company
        icp = self.env["ir.config_parameter"].sudo()
        scoped = icp.get_param(self._cer_scoped_key(key, company.id), default=None)
        if scoped not in (None, ""):
            return scoped
        return icp.get_param(key, default)

    def _cer_set_param_scoped(self, key: str, value):
        """Setea ICP *solo* en scope por compañía (evita pisar global)."""
        company = self.env.company
        self.env["ir.config_parameter"].sudo().set_param(
            self._cer_scoped_key(key, company.id),
            value if value is not None else "",
        )

    # ----------------------------
    # get/set values (Odoo settings)
    # ----------------------------
    @api.model
    def get_values(self):
        res = super().get_values()
        # Defaults de suite (si no hay nada guardado)
        deposit = float(self._cer_get_param(ICP_DEPOSIT_PERCENT_KEY, 50.0) or 0.0)
        validity = int(self._cer_get_param(ICP_VALIDITY_DAYS_KEY, 7) or 0)

        res.update(
            cer_default_deposit_percent=deposit,
            cer_quote_validity_days=validity,
        )
        return res

    def set_values(self):
        super().set_values()
        # Guardar en ICP (por compañía). Usamos sudo() con justificación:
        # - res.config.settings se ejecuta en modo admin y es el patrón estándar para parámetros.
        for rec in self:
            rec._cer_set_param_scoped(ICP_DEPOSIT_PERCENT_KEY, rec.cer_default_deposit_percent)
            rec._cer_set_param_scoped(ICP_VALIDITY_DAYS_KEY, rec.cer_quote_validity_days)

    # ----------------------------
    # Validaciones (sin negocio)
    # ----------------------------
    @api.constrains("cer_default_deposit_percent")
    def _check_cer_default_deposit_percent(self):
        for rec in self:
            if rec.cer_default_deposit_percent < 0.0 or rec.cer_default_deposit_percent > 100.0:
                raise ValidationError(_("El abono por defecto debe estar entre 0 y 100."))

    @api.constrains("cer_quote_validity_days")
    def _check_cer_quote_validity_days(self):
        for rec in self:
            if rec.cer_quote_validity_days < 1 or rec.cer_quote_validity_days > 365:
                raise ValidationError(_("La vigencia debe estar entre 1 y 365 días."))

