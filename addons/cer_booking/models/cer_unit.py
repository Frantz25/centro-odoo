# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CerUnit(models.Model):
    _name = "cer.unit"
    _description = "CER Unit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "unit_type, name"

    name = fields.Char(string="Nombre", required=True, tracking=True)
    unit_type = fields.Selection(
        [
            ("vip_1", "VIP 1 persona"),
            ("vip_2", "VIP 2 personas"),
            ("std_4", "Estándar 4 personas"),
            ("std_5", "Estándar 5 personas"),
            ("camp_slot", "Camping (cupo)"),
            ("event_space", "Espacio de evento"),
        ],
        string="Tipo de unidad",
        required=True,
        tracking=True,
    )
    capacity = fields.Integer(string="Capacidad", default=1, required=True, tracking=True)

    is_pool = fields.Boolean(
        string="Es pool",
        help="Úsalo para cupos genéricos (ej. camping).",
        tracking=True,
    )
    pool_qty = fields.Integer(
        string="Cupos del pool",
        default=0,
        help="Cantidad de cupos disponibles cuando la unidad funciona como pool.",
    )

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )

    _sql_constraints = [
        ("cer_unit_name_company_uniq", "unique(name, company_id)", "Ya existe una unidad con ese nombre en esta compañía."),
    ]

    @api.constrains("capacity", "is_pool", "pool_qty")
    def _check_capacity_values(self):
        for rec in self:
            if rec.capacity < 1:
                raise ValidationError(_("La capacidad debe ser mayor o igual a 1."))
            if rec.is_pool and rec.pool_qty < 1:
                raise ValidationError(_("Si es pool, debes indicar cupos de pool mayores a 0."))
            if not rec.is_pool and rec.pool_qty:
                raise ValidationError(_("pool_qty solo aplica cuando 'Es pool' está activo."))
