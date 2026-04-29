# DECISIONS — CRM Hub Module
**Session:** 2026-04-29-crm-module-proposal

## Aceptadas

### D1 — CRM Hub como submódulo dentro de Sales (no módulo top-level)
**Motivo:** El Studio de Sales ya maneja lo operativo. El CRM Hub es la capa estratégica del mismo dominio de ventas. Evita crear un nuevo top-level menu item — el sidebar ya tiene Closer Studio.
**Trade-off rechazado:** CRM como módulo separado al nivel de Brand/Offer/Growth. Demasiada fragmentación para microempresarios.

### D2 — Sales Agent = motor de ejecución de campañas (no construir email sender propio)
**Motivo:** El Sales Agent ya sabe comunicarse por canal. Extenderlo con un entry point "outbound" es más eficiente que construir un sender separado. El CRM Hub solo orquesta, el agente ejecuta.
**Implicación:** El Email Agent (futuro) usará la misma API de Campaigns con `agent_type="email"`.

### D3 — Segmentos dinámicos > tags estáticos como primer class citizen
**Motivo:** Attio y HubSpot probaron que los filtros dinámicos dan más valor que las listas manuales para empresas en crecimiento. Las listas estáticas son para casos edge (evento específico, lista de espera manual).
**Trade-off:** Mayor complejidad inicial en el filter builder. Mitigado con segmentos preconstruidos del sistema.

### D4 — Pulso ("Attention Queue") como primera vista del CRM Hub
**Motivo:** El microempresario no tiene tiempo para revisar 200 contactos. Necesita que el sistema le diga "haz esto hoy". Es el diferenciador de UX.
**Referencia:** HubSpot Breeze AI, 11x daily digest pattern.

### D5 — Copilot como punto de contacto conversacional para CRM
**Motivo:** Alineado con la visión Nicolify = agencia de marketing. El Copilot es el account manager. Debe poder responder "¿quiénes son mis leads calientes?" sin que el emprendedor abra la app.

## Pendientes (preguntas abiertas)

- D6 — Canal prioritario para campañas outbound (WhatsApp vs Email vs Telegram)
- D7 — Import CSV de contactos externos: ¿MVP o diferir?
- D8 — Template de mensaje: siempre IA personaliza, o el emprendedor puede escribir uno fijo?
- D9 — Scope de notas manuales en contactos: ¿MVP o Fase 2?

## Descartadas

### Descarte 1 — Lookalike finder en MVP
**Motivo:** Alta complejidad, bajo uso inmediato. Los microempresarios no tienen suficiente data para que sea útil al inicio.

### Descarte 2 — Fine-grained permission sharing de segmentos
**Motivo:** Los tenants de Nicolify son solos o equipos muy pequeños. El modelo multi-user granular es over-engineering para el MVP.

### Descarte 3 — Predictive churn model
**Motivo:** El `is_inactive` + score decay del sistema existente es suficiente proxy de churn para este segmento. Un modelo ML requiere datos que aún no hay.
