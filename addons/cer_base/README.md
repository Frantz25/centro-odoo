# cer_base (Odoo 19.0 Community)

Módulo base de la suite CER.

## Qué incluye
- Seguridad base (grupos CER) y menús raíz.
- Parámetros CER:
  - Global: `cer_base.policy_mandatory` (ir.config_parameter)
  - Por compañía (scope `__company_<id>`):
    - `cer_base.default_deposit_percent__company_<id>`
    - `cer_base.quote_validity_days__company_<id>`
- Mixins/Helpers reutilizables:
  - `cer.company.mixin` (company_id con check_company)
  - `cer.sequence.mixin` (asignación de secuencia reusable)
  - `cer.helpers` (normalización de códigos)
- Campos CER en producto.template:
  - `cer_charge_mode`
  - `cer_min_people`

## No incluye (por diseño)
Reglas de proceso (pricing, booking, documentos, comunicaciones, portal).

