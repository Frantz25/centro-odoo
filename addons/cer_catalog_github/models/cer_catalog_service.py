# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import io
import time
import hashlib
import urllib.request
import urllib.error

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CERCatalogService(models.AbstractModel):
    _name = "cer.catalog.service"
    _description = "CER Catalog Service"

    @api.model
    def run_sync_from_local_path(self, source, local_path: str, initiated_by="manual"):
        with open(local_path, "rb") as f:
            data = f.read()
        filename = local_path.split("/")[-1]
        return self._run_sync(source, data, initiated_by=initiated_by, filename=filename, url="local")

    @api.model
    def run_sync_from_url(self, source, initiated_by="manual"):
        url = source.github_raw_url
        headers = {
            "User-Agent": "Odoo CER Catalog Sync",
            "Accept": "text/csv,*/*",
        }
        if source.github_token:
            headers["Authorization"] = f"token {source.github_token}"

        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = resp.read()
        except urllib.error.HTTPError as e:
            raise UserError(_("Error HTTP al descargar catálogo (%s): %s") % (e.code, e.reason))
        except urllib.error.URLError as e:
            raise UserError(_("Error de red al descargar catálogo: %s") % (getattr(e, "reason", e),))
        except Exception as e:
            raise UserError(_("Error inesperado al descargar catálogo: %s") % (e,))

        filename = (url.split("/")[-1] or "catalog.csv")
        return self._run_sync(source, data, initiated_by=initiated_by, filename=filename, url=url)

    @api.model
    def _run_sync(self, source, raw_bytes: bytes, *, initiated_by: str, filename: str, url: str):
        source.ensure_one()
        company = source.company_id
        now = fields.Datetime.now()
        started = time.time()

        Log = self.env["cer.catalog.sync.log"].sudo()
        log = Log.create({
            "name": f"{source.name} - {now}",
            "company_id": company.id,
            "source_id": source.id,
            "initiated_by": initiated_by,
            "state": "failed",
            "started_at": now,
            "url": url,
            "filename": filename,
        })

        created = updated = skipped = 0

        try:
            source_hash = hashlib.sha256(raw_bytes or b"").hexdigest()
            if source.last_source_hash and source.last_source_hash == source_hash:
                log.write({
                    "state": "skipped",
                    "message": "Sin cambios: hash de origen idéntico al último sync.",
                })
                self._finalize_source(source, log, started, source_hash=source_hash)
                return log

            text = raw_bytes.decode("utf-8-sig", errors="replace")
            rows = self._parse_csv(text)

            if not rows:
                log.write({
                    "state": "skipped",
                    "message": "CSV sin filas (solo encabezados o vacío).",
                })
                self._finalize_source(source, log, started)
                return log

            Product = self.env["product.product"].with_company(company).sudo()
            Tax = self.env["account.tax"].with_company(company).sudo()
            Category = self.env["product.category"].sudo()
            UoM = self.env["uom.uom"].sudo()

            codes = [r.get("default_code") for r in rows if r.get("default_code")]
            cer_skus = [r.get("cer_sku") for r in rows if r.get("cer_sku")]

            existing = Product.browse()
            if codes:
                existing |= Product.search([("default_code", "in", list(set(codes)))])
            if cer_skus:
                existing |= Product.search([("product_tmpl_id.cer_sku", "in", list(set(cer_skus)))])

            existing_code_map = {p.default_code: p for p in existing if p.default_code}
            existing_sku_map = {p.product_tmpl_id.cer_sku: p for p in existing if p.product_tmpl_id.cer_sku}

            categ_cache = {}
            uom_cache = {}

            default_tax = company.cer_catalog_default_sale_tax_id
            allow_create_categories = bool(company.cer_catalog_allow_create_categories)
            allow_uom_fallback = bool(company.cer_catalog_allow_create_uom)

            for r in rows:
                code = r.get("default_code")
                cer_sku = r.get("cer_sku") or code
                name = r.get("name")
                if not code or not name:
                    skipped += 1
                    continue

                prod = existing_sku_map.get(cer_sku) or existing_code_map.get(code)
                prod_vals = {}
                tmpl_vals = {"cer_sku": cer_sku}

                # type
                ptype = (r.get("type") or "").strip().lower()
                if ptype in ("product", "consu", "service"):
                    prod_vals["type"] = "service" if ptype == "service" else "product"

                # list_price
                if r.get("list_price") not in (None, ""):
                    try:
                        prod_vals["list_price"] = float(r["list_price"])
                    except Exception:
                        pass

                # active
                if r.get("active") not in (None, ""):
                    prod_vals["active"] = self._to_bool(r.get("active"))

                # category
                categ = (r.get("categ") or "").strip()
                if categ:
                    categ_id = self._get_or_create_category(Category, categ, categ_cache, allow_create_categories)
                    if categ_id:
                        tmpl_vals["categ_id"] = categ_id

                # uom
                uom_name = (r.get("uom") or "").strip()
                if uom_name:
                    uom_id = self._find_uom(UoM, uom_name, uom_cache)
                    if not uom_id and allow_uom_fallback:
                        uom_id = self._find_uom(UoM, "Units", uom_cache) or self._find_uom(UoM, "Unit(s)", uom_cache)
                    if uom_id:
                        tmpl_vals["uom_id"] = uom_id
                        tmpl_vals["uom_po_id"] = uom_id

                # taxes
                tax_name = (r.get("tax") or "").strip()
                tax_id = False
                if tax_name:
                    tax_id = self._find_sale_tax_by_name(Tax, tax_name)
                elif default_tax:
                    tax_id = default_tax.id
                if tax_id:
                    tmpl_vals["taxes_id"] = [(6, 0, [tax_id])]

                # CER fields on template (from cer_base)
                charge_mode = (r.get("charge_mode") or "").strip()
                if charge_mode in ("room_person_night", "day", "person", "fixed"):
                    tmpl_vals["cer_charge_mode"] = charge_mode

                if r.get("min_people") not in (None, ""):
                    try:
                        tmpl_vals["cer_min_people"] = int(float(r.get("min_people")))
                    except Exception:
                        pass

                if prod:
                    if prod.name != name:
                        prod_vals["name"] = name

                    if prod_vals:
                        prod.write(prod_vals)
                    if tmpl_vals:
                        prod.product_tmpl_id.write(tmpl_vals)
                    updated += 1
                else:
                    create_vals = {"name": name, "default_code": code, "sale_ok": True}
                    create_vals.update(prod_vals)
                    new_prod = Product.create(create_vals)
                    existing_code_map[code] = new_prod
                    existing_sku_map[cer_sku] = new_prod
                    if tmpl_vals:
                        new_prod.product_tmpl_id.write(tmpl_vals)
                    created += 1

            log.write({
                "state": "success",
                "created_count": created,
                "updated_count": updated,
                "skipped_count": skipped,
                "message": "Sync completada.",
            })

        except Exception as e:
            import traceback
            log.write({
                "state": "failed",
                "error_message": str(e),
                "error_trace": traceback.format_exc(),
            })

        self._finalize_source(source, log, started, source_hash=source_hash)
        return log

    @api.model
    def _finalize_source(self, source, log, started_time, source_hash=None):
        duration_ms = int((time.time() - started_time) * 1000.0)
        log.write({
            "finished_at": fields.Datetime.now(),
            "duration_ms": duration_ms,
        })
        vals = {
            "last_sync_at": log.finished_at,
            "last_sync_state": log.state,
            "last_sync_log_id": log.id,
        }
        if source_hash:
            vals["last_source_hash"] = source_hash
        source.write(vals)

    @api.model
    def _parse_csv(self, text: str):
        buf = io.StringIO(text)
        reader = csv.reader(buf)
        headers = next(reader, [])
        if not headers:
            return []

        headers_norm = [self._norm(h) for h in headers]
        rows = []
        for line in reader:
            if not line or all((c or "").strip() == "" for c in line):
                continue
            row = {}
            for i, val in enumerate(line):
                if i >= len(headers_norm):
                    continue
                row[headers_norm[i]] = (val or "").strip()
            rows.append(self._coerce_row_keys(row))
        return rows

    @api.model
    def _coerce_row_keys(self, row):
        aliases = {
            "codigo": "default_code",
            "code": "default_code",
            "sku": "cer_sku",
            "cer_sku": "cer_sku",
            "nombre": "name",
            "precio": "list_price",
            "price": "list_price",
            "impuesto": "tax",
            "categoria": "categ",
            "uom_name": "uom",
            "modo_cobro": "charge_mode",
            "min_personas": "min_people",
        }
        for k, v in list(row.items()):
            ak = aliases.get(k)
            if ak and ak not in row and v not in (None, ""):
                row[ak] = v
        return row

    @api.model
    def _norm(self, s):
        return (s or "").strip().lower()

    @api.model
    def _to_bool(self, v):
        s = (v or "").strip().lower()
        return s in ("1", "true", "t", "yes", "y", "si", "sí", "on")

    @api.model
    def _find_sale_tax_by_name(self, Tax, name):
        tax = Tax.search([("type_tax_use", "=", "sale"), ("name", "=", name)], limit=1)
        if tax:
            return tax.id
        tax = Tax.search([("type_tax_use", "=", "sale"), ("name", "ilike", name)], limit=1)
        return tax.id if tax else False

    @api.model
    def _find_uom(self, UoM, name, cache):
        key = name.strip().lower()
        if key in cache:
            return cache[key]
        rec = UoM.search([("name", "ilike", name)], limit=1)
        cache[key] = rec.id if rec else False
        return cache[key]

    @api.model
    def _get_or_create_category(self, Category, categ_path, cache, allow_create):
        key = categ_path.strip()
        if key in cache:
            return cache[key]
        parts = [p.strip() for p in categ_path.split("/") if p.strip()]
        parent = False
        full = ""
        for part in parts:
            full = f"{full}/{part}" if full else part
            if full in cache:
                parent = cache[full]
                continue
            dom = [("name", "=", part), ("parent_id", "=", parent or False)]
            cat = Category.search(dom, limit=1)
            if not cat and allow_create:
                cat = Category.create({"name": part, "parent_id": parent or False})
            cache[full] = cat.id if cat else False
            parent = cache[full]
        cache[key] = parent
        return parent
