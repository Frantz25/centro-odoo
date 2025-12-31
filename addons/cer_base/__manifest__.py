# -*- coding: utf-8 -*-
{
    "name": "CER Base",
    "version": "19.0.1.0.1",
    "category": "Tools",
    "summary": "Fundación transversal CER (config, seguridad, helpers, campos CER en producto)",
    "description": """
CER Base (Odoo 19 Community, on-premise)

- Grupos y menús raíz CER
- Parámetros globales y por compañía (ir.config_parameter con scope __company_ID)
- Helpers/mixins reutilizables (multi-compañía, secuencias, normalización de códigos)
- Campos CER en producto (modo de cobro, mínimo de personas)
""",
    "author": "CER",
    "license": "LGPL-3",
    "depends": [
        "base",
        "product",
    ],
    "data": [
        "security/cer_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/res_config_settings_views.xml",
        "views/product_template_views.xml",
        "views/cer_menus.xml",
    ],
    "installable": True,
    "application": True,
}

