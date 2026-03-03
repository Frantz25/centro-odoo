# Sprint 4 — CER Documents (Issues propuestos)

## Issue A — [S4][cer_documents] Integrar logo oficial CER en plantillas QWeb
- Guardar logo en `addons/cer_documents/static/src/img/logo_cer.png`
- Incluir logo en encabezado de cotización CER y acta.
- Validar render PDF sin desbordes.

## Issue B — [S4][cer_documents] PDF comercial CER con datos de reserva
- Mostrar: cliente, fechas, estadía, participantes.
- Mostrar líneas con nombre limpio de producto (`product_id.name`).
- Mostrar totales estándar Odoo (`amount_untaxed`, `amount_tax`, `amount_total`).
- Mostrar abono requerido/recibido/saldo.

## Issue C — [S4][cer_documents] QR de check-in en PDF
- Incluir QR de check-in de la reserva (token/URL).
- Validar escaneo desde PDF impreso y digital.

## Issue D — [S4][cer_documents] Trazabilidad de generación documental
- Adjuntar PDF generado al pedido/reserva.
- `message_post` con evidencia de generación.

## Issue E — [S4][cer_documents] Acta de aceptación (estructura base)
- Plantilla QWeb de acta (versión inicial).
- Estructura para firma PNG (adjunto) en siguientes iteraciones.

## Labels sugeridos
- `sprint`, `cer_documents`, `backend`, `docs`, `qa`, `todo`

## Comandos GH sugeridos
```bash
cd /opt/centro-odoo

gh issue create --title "[S4][cer_documents] Integrar logo oficial CER en plantillas QWeb" --body "Usar logo en encabezado de documentos CER y validar render PDF." --label "sprint,cer_documents,frontend,todo"

gh issue create --title "[S4][cer_documents] PDF comercial CER con datos de reserva" --body "Documento comercial con datos de reserva, líneas limpias y totales estándar Odoo." --label "sprint,cer_documents,backend,todo"

gh issue create --title "[S4][cer_documents] QR de check-in en PDF" --body "Incluir QR escaneable de check-in en documento CER." --label "sprint,cer_documents,backend,qa,todo"

gh issue create --title "[S4][cer_documents] Trazabilidad documental (adjuntos + chatter)" --body "Adjuntar PDF y registrar message_post al generar documentos." --label "sprint,cer_documents,backend,qa,todo"

gh issue create --title "[S4][cer_documents] Acta de aceptación base" --body "Plantilla base de acta y estructura para firma PNG." --label "sprint,cer_documents,docs,todo"
```
