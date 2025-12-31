# -*- coding: utf-8 -*-
import os


def post_init_hook(env):
    """Modo A (deploy-time): importación del CSV local del módulo.

    Odoo 19 (y recientes) invoca post_init_hook con un `env`.
    Mantener este hook compatible evita errores tipo:
    - TypeError: post_init_hook() missing 1 required positional argument: 'registry'

    Producción segura:
    - `data/catalog_seed.csv` viene con encabezados y sin filas.
    - Puedes reemplazarlo por tu catálogo real en el repo antes de desplegar.
    """
    Source = env["cer.catalog.source"].sudo()

    # Crear una fuente por compañía si no existe ninguna
    companies = env["res.company"].sudo().search([])
    for company in companies:
        existing = Source.search([("company_id", "=", company.id)], limit=1)
        if existing:
            continue
        Source.create({
            "name": f"Catálogo CER (deploy-time) - {company.name}",
            "company_id": company.id,
            "mode": "install",
            "source_type": "local",
            "active": True,
        })

    local_path = os.path.join(os.path.dirname(__file__), "data", "catalog_seed.csv")
    if not os.path.exists(local_path):
        return

    sources = Source.search([("active", "=", True), ("mode", "=", "install"), ("source_type", "=", "local")])
    for src in sources:
        src.with_company(src.company_id).action_sync_from_local_file(local_path, initiated_by="post_init_hook")
