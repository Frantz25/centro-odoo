# CER Pricing (Odoo 19 Community)

## Objetivo
`cer_pricing` centraliza las reglas de cálculo de cantidad (qty) para cotizaciones CER, evitando lógica duplicada en otros módulos.

## Alcance del módulo
### Incluye
- Motor de pricing (`cer.pricing.engine`)
- Reglas de cantidad por modo de cobro
- Integración en `sale.order` y `sale.order.line`
- Validaciones funcionales básicas

### No incluye
- Portal cliente
- Documentos/PDF
- Operación de reservas (booking)
- Disparadores de comunicaciones

## Reglas de negocio (qty)
- `room_person_night` → `qty = noches * personas`
- `day` → `qty = días`
- `person` → `qty = max(personas, cer_min_people)`
- `fixed` → `qty = 1`

## Casos de prueba de referencia
1. Habitación: 2 noches, 4 personas → `qty = 8`
2. Salón/Capilla: 3 días → `qty = 3`
3. Actividad: 10 personas, mínimo 40 → `qty = 40`

## Fuente de precio e impuestos
- `price_unit` proviene de producto/pricelist.
- Impuestos y totales se manejan con motor estándar de Odoo.
- No recalcular IVA manualmente en este módulo.

## Flujo técnico resumido
1. Usuario define fechas/personas en cabecera de `sale.order`.
2. Líneas con productos CER aplican modo de cobro.
3. Motor calcula qty y actualiza `product_uom_qty` según configuración.
4. Odoo calcula subtotales/impuestos/totales de forma estándar.

## Recomendaciones de uso
- Configurar correctamente `cer_charge_mode` y `cer_min_people` en producto.
- Mantener reglas de qty únicamente en este módulo.
- Agregar tests cuando se introduzca una nueva regla de cálculo.
