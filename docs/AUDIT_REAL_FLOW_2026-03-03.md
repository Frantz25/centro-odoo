# Auditoría profunda de flujo real (CER Odoo)

**Proyecto:** `/root/.openclaw/workspace/incoming/centro-odoo`  
**Fecha:** 2026-03-03  
**Foco:** flujo operativo real `cotización → aceptación → reserva → pago 50% → documentos → comunicaciones` (sin idealizar)

---

## Resumen ejecutivo (12 bullets)

1. El flujo de **pricing base** sí funciona: fechas, participantes, estacionalidad y descuentos se aplican en `sale.order`/`sale.order.line`.
2. El flujo de **reserva manual** (botón “Reservar”) está implementado y valida políticas + abono mínimo + disponibilidad por capacidad de producto.
3. El control de **abono mínimo 50%** existe, pero está acoplado a facturas publicadas/pagadas; en flujo estándar de Odoo puede bloquear la reserva temprana.
4. Hay una inconsistencia crítica: `action_confirm()` confirma primero la venta y recién después valida bloqueo de reserva; deja ventas confirmadas sin booking CER.
5. El camino de **aceptación por portal** crea/confirmar booking sin validar disponibilidad explícita en ese punto.
6. `cer.booking.state` y `sale.order.cer_booking_state` no están sincronizados de forma robusta; se puede cancelar pedido sin liberar estado real del booking.
7. La asignación de unidades tipo **pool** no controla `pool_qty`; puede sobreasignar cupos sin freno.
8. Existe doble disparo del evento `document_finalized` en documentos (por `action_generate` y por `write`), riesgo de comunicaciones duplicadas.
9. Se dispara evento `sale_portal_accepted`, pero no existe regla default para ese evento; en práctica no comunica nada.
10. El cálculo de “días” para pricing usa lógica diferente al “display de estadía”; puede producir desalineación comercial (precio vs lo que se muestra).
11. La capa de comunicaciones depende de email/chatter; sin SMTP se puede validar por chatter y cola de correo, pero no hay guía QA formal en repo.
12. Cobertura de tests es insuficiente para el flujo de negocio crítico: hay tests en `cer_pricing`, pero no para booking/documents/communications integrados.

---

## 1) Qué funciona hoy realmente

### 1.1 Cotización + pricing CER
- Extensión de `sale.order` con fechas/participantes y recalculo de líneas CER:  
  `addons/cer_pricing/models/sale_order.py`
- Motor de pricing por modo de cobro (`room_person_night`, `day`, `person_day`, `person`):  
  `addons/cer_pricing/models/cer_pricing_engine.py`
- Descuento por cliente aplicado en líneas con bandera CER:  
  `addons/cer_pricing/models/sale_order.py`, `addons/cer_booking/models/sale_order.py`

**Conclusión real:** la cotización con lógica CER sí se puede operar hoy.

### 1.2 Reserva CER manual
- Botones de flujo en `sale.order` (`Marcar`, `Reservar`, `Confirmar`, `Cancelar`):  
  `addons/cer_booking/views/sale_order_views.xml`
- Reserva valida fechas/política/abono mínimo/disponibilidad antes de pasar a `reserved`:  
  `addons/cer_booking/models/sale_order.py:286-301`
- Creación de `cer.booking` idempotente desde `sale.order`:  
  `addons/cer_booking/models/cer_booking.py:77-103`

**Conclusión real:** existe un flujo usable para el equipo interno, con frenos básicos.

### 1.3 Documentos CER
- Wizard para crear documento desde `sale.order`:  
  `addons/cer_documents/wizards/cer_document_create_wizard.py`
- Generación de HTML desde plantilla y salida PDF:  
  `addons/cer_documents/models/cer_document.py`
- Firma portal pública con token de acceso:  
  `addons/cer_documents/controllers/portal_sign.py`

**Conclusión real:** documentos se generan y pueden firmarse por token.

### 1.4 Comunicaciones automáticas
- Servicio de reglas por evento/canal/destinatario:  
  `addons/cer_communications/models/cer_communication_service.py`
- Disparadores conectados a eventos de booking y cron (vigencia/precheckin/postevento):  
  `addons/cer_communications/models/sale_order_booking.py`, `addons/cer_communications/data/cron.xml`

**Conclusión real:** framework de comunicación funciona, aunque con huecos de regla y duplicidades.

---

## 2) Qué está roto o riesgoso (no idealizado)

## P0 (crítico)

### P0-1: Confirma venta antes de validar reserva
**Evidencia:** `addons/cer_booking/models/sale_order.py:228-240`  
`action_confirm()` ejecuta `super().action_confirm()` antes de validar política/abono mínimo. Si falla, solo deja mensaje en chatter y continúa.

**Impacto real:** puedes terminar con `sale.order` en estado venta confirmada, pero sin reserva CER efectiva.

---

### P0-2: Flujo “reserva con 50%” choca con ciclo estándar de Odoo
**Evidencia:**
- Requisito de abono mira facturas posteadas/pagadas: `addons/cer_booking/models/sale_order.py` (`_cer_get_paid_amount`, `_cer_assert_minimum_deposit_for_reservation`)
- “Reservar” solo está en `draft/sent`: `addons/cer_booking/models/sale_order.py:286-301`, vista en `addons/cer_booking/views/sale_order_views.xml`

**Impacto real:** en Odoo estándar, el anticipo normalmente nace al confirmar venta; aquí pides anticipo para reservar antes de confirmar. Riesgo de flujo bloqueado o workaround manual.

---

### P0-3: Estados desincronizados entre `sale.order` y `cer.booking`
**Evidencia:**
- `cer.booking.state` nace como `confirmed`: `addons/cer_booking/models/cer_booking.py:56-66, 85-91`
- Al cancelar order solo se cambia `sale.order.cer_booking_state`: `addons/cer_booking/models/sale_order.py:327-332`
- No hay método que sincronice sistemáticamente `cer.booking.state` con cancelaciones/rollback.

**Impacto real:** ocupación/unidades y reporting pueden quedar “confirmados” cuando comercialmente ya se canceló.

---

## P1 (alto)

### P1-1: Aceptación portal confirma booking sin control explícito de disponibilidad
**Evidencia:** `addons/cer_booking/models/sale_order.py:242-262`  
En `action_quotation_accept()` se valida política + abono y se crea booking, pero no llama a `_cer_check_availability()` en ese flujo.

**Impacto real:** en picos de demanda, portal puede confirmar y luego descubrir conflicto operativo.

---

### P1-2: Pool de unidades no respeta `pool_qty`
**Evidencia:**
- Campo existe: `addons/cer_booking/models/cer_unit.py` (`pool_qty`)
- Asignación pool no usa `pool_qty`: `addons/cer_booking/models/cer_booking.py:153-171`

**Impacto real:** sobreventa silenciosa en cupos tipo camping/pool.

---

### P1-3: Evento de documento finalizado se dispara dos veces
**Evidencia:** `addons/cer_communications/models/cer_document.py:10-15` y `17-24`.

**Impacto real:** emails/chatter duplicados para `document_finalized`.

---

### P1-4: Evento `sale_portal_accepted` sin reglas default
**Evidencia:**
- Trigger existe: `addons/cer_booking/models/sale_order.py:245-246`
- No hay registros `event_code = sale_portal_accepted` en `addons/cer_communications/data/default_rules.xml` (líneas 5-150).

**Impacto real:** aceptación portal no genera comunicación esperada por defecto.

---

## P2 (medio)

### P2-1: Inconsistencia “días” pricing vs display de estadía
**Evidencia:**
- Pricing engine comenta cobro inclusivo pero usa `inclusive=False`: `addons/cer_pricing/models/cer_pricing_engine.py:35-37`
- `sale.order` calcula días como noches+1 (inclusivo): `addons/cer_pricing/models/sale_order.py:_compute_cer_stay`

**Impacto real:** potencial desalineación entre lo que se cobra y lo que se comunica al cliente.

---

### P2-2: Duplicidad de definición `cer_apply_discount`
**Evidencia:**
- `addons/cer_pricing/models/sale_order_line.py`
- `addons/cer_booking/models/sale_order_line.py`

**Impacto real:** deuda técnica y riesgo de drift funcional en upgrades.

---

### P2-3: Cobertura de tests no cubre flujo crítico extremo a extremo
**Evidencia:** tests encontrados en `cer_pricing`, `cer_base`, `cer_catalog_github`; sin tests de integración booking-docs-comms.

**Impacto real:** regresiones en flujo real pasan a producción sin detección temprana.

---

## 3) Inconsistencias entre módulos (cer_booking / cer_documents / cer_communications / cer_pricing)

1. **booking vs comunicaciones:** se emiten eventos de portal acceptance sin reglas por defecto (`sale_portal_accepted`).
2. **booking vs documentos/comms:** documento “final” dispara notificación doble por herencia en comunicaciones.
3. **booking vs pricing:** control de reserva exige pago (facturas) en etapa donde comercialmente aún se opera cotización.
4. **booking (estado order) vs booking (estado entidad):** dos máquinas de estado paralelas sin sincronización robusta.
5. **pricing (days engine) vs pricing/display (stay_days):** semántica de días no unificada.

---

## 4) Flujo recomendado único y mínimo viable (operación real)

## Objetivo
Un flujo operativo que no rompa Odoo estándar y sí garantice control de riesgo.

### MVP propuesto (único)
1. **Cotización (`draft/sent`)**
   - Capturar fechas, participantes, líneas y pricing automático.
2. **Aceptación cliente**
   - Aceptación portal marca `cer_policy_accepted` y deja “pendiente de abono”.
3. **Reserva tentativa (soft hold, sin confirmar venta)**
   - Validar disponibilidad al instante.
   - Crear `cer.booking` en estado `draft/reserved` (no `confirmed`) con vencimiento de hold.
4. **Pago 50%**
   - Registrar anticipo mediante flujo estándar (factura de anticipo + pago).
5. **Confirmación definitiva**
   - Revalidar disponibilidad + abono mínimo.
   - Confirmar `sale.order` y pasar booking a `confirmed` en transacción consistente.
6. **Documentos**
   - Generar acta/contrato al confirmar; firma portal opcional antes de check-in.
7. **Comunicaciones**
   - Confirmación + pase check-in + recordatorios por cron/chatter.

**Regla de oro:** no dejar `sale.order` confirmada con booking pendiente/inválido.

---

## 5) Plan de fixes priorizado (P0 / P1 / P2) con evidencia

## P0 (semana 1)

### Fix P0-A: Hacer atómico `action_confirm()` con validaciones previas
- **Cambiar:** validar política + abono + disponibilidad *antes* de `super().action_confirm()`.
- **Archivo:** `addons/cer_booking/models/sale_order.py` (zona 228-240, 286-315)
- **Resultado esperado:** si no cumple, no se confirma venta.

### Fix P0-B: Rediseñar gating de abono 50%
- **Cambiar:** permitir “reserva tentativa” sin confirmación de venta, o mover control de 50% al paso de confirmación definitiva.
- **Archivo:** `addons/cer_booking/models/sale_order.py` (`action_cer_booking_reserve`, `action_cer_booking_confirm`, `_cer_assert_minimum_deposit_for_reservation`)
- **Resultado esperado:** flujo ejecutable sin hacks contables.

### Fix P0-C: Sincronización fuerte de estados
- **Cambiar:** mapear y sincronizar `sale.order.cer_booking_state` ↔ `cer.booking.state` en confirmación/cancelación.
- **Archivo:** `addons/cer_booking/models/sale_order.py`, `addons/cer_booking/models/cer_booking.py`
- **Resultado esperado:** disponibilidad y reporting coherentes.

---

## P1 (semana 2)

### Fix P1-A: Validar disponibilidad en aceptación portal
- **Cambiar:** incluir `_cer_check_availability()` en `action_quotation_accept()` antes de crear/confirmar booking.
- **Archivo:** `addons/cer_booking/models/sale_order.py:242-262`

### Fix P1-B: Corregir capacidad de pool
- **Cambiar:** en `_auto_assign_units`, comparar `qty_requested` vs `pool_qty` y reservas solapadas previas.
- **Archivo:** `addons/cer_booking/models/cer_booking.py:153-171`

### Fix P1-C: Evitar doble trigger `document_finalized`
- **Cambiar:** disparar solo en `write` (transición de estado) o solo en `action_generate`, no ambos.
- **Archivo:** `addons/cer_communications/models/cer_document.py:10-24`

### Fix P1-D: Agregar reglas default para `sale_portal_accepted` (y opcional rejected)
- **Cambiar:** insertar records en `default_rules.xml`.
- **Archivo:** `addons/cer_communications/data/default_rules.xml`

---

## P2 (semana 3)

### Fix P2-A: Unificar semántica de días/noches
- **Cambiar:** decidir estándar (inclusive o exclusivo) y alinear engine + display + reportes.
- **Archivo:** `addons/cer_pricing/models/cer_pricing_engine.py`, `addons/cer_pricing/models/sale_order.py`

### Fix P2-B: Eliminar duplicidad de campo `cer_apply_discount`
- **Cambiar:** definir una sola vez y heredar sin redefinir.
- **Archivo:** `addons/cer_pricing/models/sale_order_line.py`, `addons/cer_booking/models/sale_order_line.py`

### Fix P2-C: Suite de tests E2E del flujo real
- **Cambiar:** tests para aceptación→reserva→abono→confirmación→doc→comms.
- **Evidencia de gap actual:** no hay tests en `cer_booking`, `cer_documents`, `cer_communications`.

---

## 6) Checklist QA realista (sin SMTP)

> Validar en entorno local sin salida de correo real: usar chatter + cola de mails (`mail.mail`) + logs de mensajes.

## Preparación
- [ ] Configurar `mail.catchall` local o dejar SMTP no operativo.
- [ ] Activar modo desarrollador.
- [ ] Crear productos reservables (habitación/salón/camping) con capacidades.
- [ ] Crear cliente con email dummy (`qa+cliente@local.test`).

## Caso A: Cotización y pricing
- [ ] Crear cotización con fechas y participantes.
- [ ] Verificar cálculo de qty/noches/días por línea CER.
- [ ] Cambiar temporada/descuento y confirmar recálculo.

## Caso B: Aceptación y política
- [ ] Aceptar por portal.
- [ ] Verificar `cer_policy_accepted`, fecha y firmante.
- [ ] Revisar chatter del pedido por trazabilidad.

## Caso C: Reserva + disponibilidad
- [ ] Ejecutar “Reservar” en una cotización válida.
- [ ] Crear segunda cotización solapada para forzar conflicto.
- [ ] Confirmar que bloqueo de disponibilidad actúa.

## Caso D: Abono 50%
- [ ] Intentar reservar/confirmar sin abono y validar bloqueo.
- [ ] Registrar anticipo (factura+payment) y repetir.
- [ ] Confirmar transición correcta de estado.

## Caso E: Documentos
- [ ] Crear documento desde wizard.
- [ ] Generar PDF y verificar adjunto en chatter.
- [ ] Firmar por portal con token y archivo imagen.
- [ ] Verificar cambio de estado de firma + trazas.

## Caso F: Comunicaciones sin SMTP
- [ ] Disparar `booking_reserved`, `booking_confirmed`, `booking_cancelled`.
- [ ] Verificar publicaciones en chatter.
- [ ] Verificar creación de correos en cola (`mail.mail`) aunque no se envíen.
- [ ] Ejecutar cron manual de precheckin/postevento y validar que crea actividad/cola esperada.

## Caso G: Cancelación y consistencia
- [ ] Cancelar `sale.order` ya confirmada.
- [ ] Verificar estado en `sale.order` y `cer.booking` (deben quedar consistentes).
- [ ] Confirmar que no queden unidades ocupadas indebidamente.

---

## Nota final
La base funcional existe, pero el flujo real hoy tiene **fracturas de consistencia transaccional** y **desalineación con el ciclo contable de Odoo** para el abono del 50%. Priorizar P0 es imprescindible antes de escalar operación diaria.
