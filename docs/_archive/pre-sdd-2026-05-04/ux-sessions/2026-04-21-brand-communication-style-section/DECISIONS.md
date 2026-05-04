# DECISIONS — Brand Studio "Estilo Comunicacional"

## 2026-04-21 · Inception

### Slug `estilo` vs `communication-style` vs `voz`
**Decisión:** `estilo`.
**Razón:** consistente con `publico` (único slug en español). Corto, memorable. `voz` es demasiado estrecho (el concepto incluye dimensiones, huella, ejemplos — no solo tono). `communication-style` es largo y mezcla idiomas en URL.
**Alternativas rechazadas:** `voz`, `tono`, `communication-style`, `estilo-comunicacional`.

### Posición en sidebar (después de identity)
**Decisión:** posición 3, entre `identity` y `positioning`.
**Razón:** orden narrativo **quién eres → cómo hablas → qué prometes → cómo lo cuentas**. Identity define la marca; style es su expresión superficial inmediata. Mantiene `publico` al inicio (quién le hablas primero).
**Alternativas:** al inicio del studio (rechazada — identity debe venir primero porque ancla narrativa), al final (rechazada — downstream depende del estilo activo, conviene configurar temprano).

### Reutilizar infraestructura existente (`personality_profiles`) vs nueva tabla
**Decisión:** reutilizar.
**Razón:** backend ya tiene PersonalityProfileModel + 6 presets + compiler + 5 endpoints funcionando. Crear tabla paralela duplicaría esfuerzo. El único gap es exponerlo en frontend bajo una sección propia.
**Trade-off:** ligar la UI al nombre "personality" en código vs "Estilo Comunicacional" en UI. Aceptable — la UI puede usar su label y el backend mantener su dominio.

### Borrar `voice_tone` de `BrandIdentity` DB
**Decisión:** **NO borrar la columna** en v1. Dejar `nullable=True`, stop writing, stop reading.
**Razón:** preservar datos de tenants existentes para posible migración. Drop en sprint futuro si nadie lee.
**Alternativa rechazada:** drop inmediato con migration de rescue (toma datos → genera PersonalityProfile automáticamente). Rechazada porque la conversión heurística puede ser inexacta y queremos dar al tenant la opción (card de migración en UI).

### Card de migración opt-in
**Decisión:** mostrar card una vez si `voice_tone` existe. User elige convertir o descartar.
**Razón:** no forzar migración automática porque el mapeo string → dimensions es lossy. User debe aprobar.
**Dismiss:** persistir flag `voice_tone_migration_dismissed` en Tenant config JSON o `BrandSettings` (arbitrar con backend-expert).

### Endpoint `POST /clone` hoy retorna 501
**Decisión:** Fase 1 del PLAN implementa la integración al LangGraph `personality_app`.
**Razón:** sin esto, la sección solo soporta presets (50% del valor). El LangGraph ya existe y está testeado standalone.
**Bloqueante:** no lanzar la sección sin clonación funcional. Preset-only launch es rechazado porque el valor diferencial está en la clonación.

### Clone wizard: textarea vs chat builder
**Decisión:** textarea para paste + upload file para bulk.
**Razón:** la mayoría de users pegará WhatsApp export o threads de mensajes. Chat builder (mensaje por mensaje) añade fricción sin mejorar calidad.
**Futuro:** explorar scraping de DMs Instagram/WhatsApp si user conecta esas integraciones.

### HTML prototype: omitir en esta sesión
**Decisión:** skip Phase 5.
**Razón:** la propuesta es una sección single-page con 4 estados y 3 overlays. Los wireframes ASCII + UI-SPEC son suficientes para implementación. HTML prototype agregaría valor si:
- El cambio fuera cross-studio (navegación compleja).
- User pidiera validar interacciones antes de codear.
Ninguna de las dos aplica aquí.
**Reversible:** si Chris pide HTML tras ver el FLOW-SPEC, se genera bajo demanda.

### Personality port en `shared/links/`
**Decisión:** crear `backend/src/shared/links/ports/personality.py`.
**Razón:** consumidores cross-module (sales_agent, landing, assets) necesitan acceso al PersonalityProfile activo. Importar directo de `modules/brand/` viola DDD (cross-module import forbidden). Patrón probado — hay precedentes (`tenant_profile` port, `guardrails` port del commit reciente).

### Activate endpoint separado
**Decisión:** crear `POST /personality/{id}/activate` nuevo, en vez de extender `/select-preset`.
**Razón:** `/select-preset` semánticamente crea-y-activa desde un preset_key. Activar un perfil ya existente (clonado o migrado) es otra acción. Separar endpoints respeta el dominio y simplifica el router.

---

## Pendientes para decidir

- [ ] ¿El port `personality` se llama así o `communication_style`? Preferencia pragmática: `personality` (match backend module). UI conserva "Estilo Comunicacional".
- [ ] ¿Mover algún preset fuera (si resulta redundante) o agregar presets "Formal Corporativo" / "Juvenil Gen-Z"? Sugerencia: mantener los 6 actuales en v1, evaluar después de 3 meses de uso.
- [ ] ¿Quién escribe la guía "cómo elegir tu estilo" para hint del empty state? Candidato: content-hunter skill + revisión de Chris.
