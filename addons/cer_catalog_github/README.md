# cer_catalog_github (Odoo 19 Community)

Catálogo de productos CER desde CSV.

## Modos
### Modo A (deploy-time)
- Importa el CSV local del módulo: `cer_catalog_github/data/catalog_seed.csv`
- Se ejecuta en `post_init_hook` (instalación del módulo).
- Recomendación: mantener ese CSV versionado (Git) y desplegarlo con el código.

### Modo B (sync automático)
- Configurar una Fuente con `github_raw_url`.
- Cron (diario por defecto) o botón "Sincronizar ahora".

## CSV esperado (encabezados)
Requeridos:
- default_code
- name
Opcionales:
- type (product/service)
- list_price
- tax (nombre de impuesto, p.ej. "IVA 19")
- categ (p.ej. "CER/Habitaciones")
- uom (p.ej. "Units")
- active (1/0, true/false)
- charge_mode (room_person_night/day/person/fixed)
- min_people (entero)
