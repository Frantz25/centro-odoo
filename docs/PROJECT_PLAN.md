# Plan Profesional del Proyecto CER (Odoo 19 Community)

## Objetivo
Implementar una suite modular para operación comercial, reservas, documentos, portal y comunicaciones del Centro Entrenamiento y Recreación El Manzano.

## Alcance por módulos
- `cer_base`: configuración global, campos base, seguridad, secuencias.
- `cer_pricing`: reglas de cantidades, vigencia, temporadas y abonos.
- `cer_booking`: operación de reservas, unidades, capacidad, QR y check-in.
- `cer_documents`: PDF profesional, acta, adjuntos y trazabilidad.
- `cer_portal`: solicitud web, aceptación/rechazo, firma canvas.
- `cer_communications`: plantillas, disparadores, recordatorios e idempotencia.

## Decisiones técnicas vigentes
- Versión objetivo: **Odoo 19 Community**.
- Arquitectura modular estricta (sin mezclar lógica entre módulos).
- IVA: usar montos estándar de Odoo (sin recalcular manual en QWeb).
- Seguridad: ACL + reglas por rol; evitar `sudo()` salvo justificación explícita.
- Contexto negocio:
  - Hospedaje: 106 plazas base.
  - Salón: 350 personas.
  - Capilla: 120 personas.
  - Camping: cupos genéricos (pool inicial 150, escalable).

## Roadmap semanal

### Semana 1 — Fundación y gobierno técnico
**Entregables**
- `cer_base` estable e instalable.
- Secuencias base activas (`cer.booking`, `cer.ticket`, `cer.quote.request`).
- Convención de ramas + commits + checklist PR.
- Hardening inicial (sin secretos en repo).

**Criterios de aceptación**
- Instalación/actualización sin traceback.
- Campos base visibles en productos/settings.
- Logs limpios.

### Semana 2 — Motor de pricing
**Entregables**
- `cer_pricing` con reglas:
  - Habitación = noches × personas
  - Salón/Capilla = días
  - Actividades = personas
- Parámetros de vigencia (7 días) y abono (50%).

**Criterios de aceptación**
- Casos de prueba de cálculo exitosos.
- Sin lógica duplicada en booking/documentos.

### Semana 3 — Operación de reservas
**Entregables**
- `cer_booking` con creación automática al confirmar cotización (idempotente).
- Asignación por tipo+cantidad.
- Camping como pool de cupos.
- Estados operativos + trazabilidad.

**Criterios de aceptación**
- Sin duplicación de reservas por reintentos.
- Validaciones de capacidad funcionando.

### Semana 4 — Documentación legal/comercial
**Entregables**
- `cer_documents`: PDF CER + acta con firma PNG.
- Adjuntos en `ir.attachment` + `message_post`.

**Criterios de aceptación**
- PDF correcto con montos estándar (`amount_untaxed`, `amount_tax`, `amount_total`).
- Flujo de acta completo.

### Semana 5 — Portal y QR
**Entregables**
- `cer_portal`: solicitud web de cotización + portal cliente.
- Aceptación/rechazo con motivo y firma canvas.
- QR reserva/ticket.

**Criterios de aceptación**
- Cliente puede solicitar/aceptar/rechazar desde portal.
- Auditoría completa en chatter.

### Semana 6 — Comunicaciones y cierre de release
**Entregables**
- `cer_communications`: emails por evento (envío, recordatorio, aceptación, rechazo).
- QA end-to-end.
- Documentación operativa y runbook de producción.

**Criterios de aceptación**
- No duplicidad de envíos.
- Checklist de salida a producción completado.

## Flujo Git recomendado
- `main`: estable/producción.
- `develop`: integración.
- `feature/<modulo>-<tema>` por tarea.
- PR obligatoria con checklist de calidad.

## Checklist de calidad por PR
- [ ] Módulo instala/actualiza sin errores.
- [ ] Seguridad mínima (ACL y/o reglas) aplicada.
- [ ] Sin secretos en cambios.
- [ ] Logs sin traceback en arranque.
- [ ] Pruebas funcionales básicas documentadas.

## Riesgos y mitigación
- Riesgo: mezclar reglas en múltiples módulos.  
  Mitigación: pricing centralizado en `cer_pricing`.
- Riesgo: sobreuso de `sudo()`.  
  Mitigación: justificar y limitar casos.
- Riesgo: regresión al migrar módulos.  
  Mitigación: pruebas por sprint + releases pequeñas.
