# CER Communications Matrix (Issue #31)

## Objetivo
Definir una matriz única de comunicaciones para evitar envíos improvisados y asegurar privacidad por rol.

## Principios
- **Cliente/asistente**: solo datos mínimos operativos (check-in, fechas, código, QR).
- **Interno/encargado**: detalle completo operativo/comercial cuando corresponda.
- **Trazabilidad obligatoria**: cada envío relevante debe dejar rastro en chatter.
- **No reservar sin reglas**: políticas + abono mínimo antes de confirmar reserva.

---

## Matriz de eventos

| Evento | Disparador | Destinatario | Canal | Contenido | Adjuntos | Trazabilidad |
|---|---|---|---|---|---|---|
| booking_reserved | `action_cer_booking_reserve` | Cliente | Email (+ opcional chatter) | Referencia reserva, fechas, código acceso | No obligatorio | Nota en `sale.order` |
| booking_confirmed (cliente) | `action_cer_booking_confirm` / flujo portal | Cliente | Email | Pase individual: QR, código, entrada/salida | Opcional PDF pase | Nota en `sale.order` |
| booking_confirmed (interno) | mismo evento (regla secuencia interna) | Correo compañía / staff | Email + chatter | Cliente, participantes, total, fechas, estado | Opcional PDF comercial | Nota interna |
| booking_cancelled | `action_cer_booking_cancel` | Cliente + interno | Email/chatter | Estado cancelada + referencia | No | Nota en `sale.order` |
| document_finalized | `cer.document.action_generate` (final) | Interno | Email/chatter | Documento, plantilla, origen | PDF documento | Nota + attachment |
| sale_validity_reminder | Cron diario | Cliente | Email | Vigencia cotización + total | No | Nota en `sale.order` |
| sale_portal_accepted | `action_quotation_accept` | Interno | Chatter (+opcional email) | Aceptación portal registrada | No | Nota con timestamp |
| pre_checkin_reminder *(#32)* | Cron 24h/48h antes entrada | Cliente | Email | Recordatorio de llegada + QR/código | Opcional pase PDF | Nota en `sale.order` |
| post_event_followup *(#34)* | Cron +24h después salida | Cliente | Email | Agradecimiento + feedback | No | Nota en `sale.order` |

---

## Campos mínimos por audiencia

### Cliente / asistente (mínimo)
- `cer_booking_name`
- `cer_date_from`, `cer_date_to`
- `cer_booking_offline_code`
- `cer_booking_qr_url` (+ imagen QR)

### Interno / encargado (completo)
- Todo lo anterior +
- `partner_id`, `cer_participants`
- `amount_untaxed`, `amount_tax`, `amount_total`
- Estado documental/firma si aplica

---

## Reglas de privacidad
- Prohibido enviar participantes globales y montos al asistente final.
- Plantillas cliente deben ser “minimal”.
- Plantillas internas pueden incluir detalle completo.
- Revisar cada regla `booking_confirmed` para evitar plantillas cruzadas.

---

## Criterios de aceptación #31
- [ ] Documento matriz versionado en `docs/`.
- [ ] Eventos actuales mapeados y alineados con reglas activas.
- [ ] Separación cliente vs interno explícita.
- [ ] Base lista para implementar #32/#33/#34 sin redefinir diseño.
