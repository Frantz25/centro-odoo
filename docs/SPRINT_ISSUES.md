# Backlog inicial por sprints (crear como Issues)

## Sprint 1 — Fundación (`cer_base`)
1. [S1][cer_base] Validar/ajustar manifest y carga de data
2. [S1][cer_base] Activar y verificar secuencias base (booking/ticket/request)
3. [S1][cer_base] Parametrización global CER en Ajustes
4. [S1][cer_base] Seguridad base: grupos CER Usuario/Manager
5. [S1][repo] Hardening: secretos y artefactos fuera de Git

## Sprint 2 — Motor (`cer_pricing`)
1. [S2][cer_pricing] Regla qty habitación = noches × personas
2. [S2][cer_pricing] Regla qty salón/capilla = días
3. [S2][cer_pricing] Regla qty actividades = personas (+ mínimo)
4. [S2][cer_pricing] Vigencia 7 días + abono 50% parametrizado
5. [S2][tests] Casos de prueba de cálculo

## Sprint 3 — Operación (`cer_booking`)
1. [S3][cer_booking] Crear booking al confirmar cotización (idempotente)
2. [S3][cer_booking] Unidades reservables (habitación/salón/capilla/camping)
3. [S3][cer_booking] Camping pool genérico (150 inicial, 600 máx)
4. [S3][cer_booking] Validaciones de capacidad y estados

## Sprint 4 — Documentos (`cer_documents`)
1. [S4][cer_documents] PDF comercial CER
2. [S4][cer_documents] Acta con firma PNG
3. [S4][cer_documents] Adjuntos + trazabilidad en chatter

## Sprint 5 — Portal (`cer_portal`)
1. [S5][cer_portal] Formulario web de solicitud de cotización
2. [S5][cer_portal] Aceptación/rechazo con motivo obligatorio
3. [S5][cer_portal] Firma canvas + almacenamiento attachment
4. [S5][cer_portal] QR reserva/ticket (flujo portal)

## Sprint 6 — Comunicaciones + release (`cer_communications`)
1. [S6][cer_communications] Plantillas por evento
2. [S6][cer_communications] Disparadores idempotentes
3. [S6][qa] Pruebas end-to-end
4. [S6][release] Runbook y salida a producción
