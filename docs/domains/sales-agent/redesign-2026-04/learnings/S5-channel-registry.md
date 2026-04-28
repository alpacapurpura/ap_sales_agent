# Learnings · S5 · Channel format registry shared (cross-agent)

> Doc para S6 (fitness tests ratchet). El registry es SSoT cross-agent
> ahora; cualquier specialist nuevo o canal nuevo se conecta sin tocar
> `OutputManager` ni `compose_system_prompt`. S6 puede asumir que slot 6
> está populado y que el arch ratchet bloquea hardcoded channel literals
> en `output_manager.py`.

---

## Resumen (3 líneas)

- **Entregado**: `src/shared/agent_observability/channels/{format,format_for_channel,intent_detector}.py` con 7 canales canónicos (chat, whatsapp, telegram, instagram_dm, sms, voice, email). `ChannelFormat` extendido con 3 campos opcionales sales-relevantes (`chunk_size`, `typing_simulation_cpm`, `parse_mode`). Aliases (`instagram` → `instagram_dm`). Telegram MarkdownV2 escape utility. Copilot mantiene 3 shims back-compat (`output_channels.py`, `format_for_channel.py`, `channel_intent_detector.py`) — 113 tests copilot verdes via shim. Sales `OutputManager._parse_response` consume `chunk_size` via `_enforce_chunk_size` + `_split_by_cap` con boundary preference. Sales `compose_system_prompt` slot 6 (`CHANNEL_FORMAT_HINT`) populated via `_channel_format_hint(state)` lee `state.channel_type`. Arch ratchet `test_no_hardcoded_channel_in_output_manager.py` sin allowlist (AST scan Compare + Dict keys). 3134 tests verde (1729 files ruff format clean, 0 ruff errors).
- **Decisión no obvia**: el plan original §criterio decía "extraer + redesign". El audit reveló que copilot ya tenía un registry production-grade — `move + extend` en lugar de redesign. Los 3 archivos copilot (`output_channels.py`, `format_for_channel.py`, `channel_intent_detector.py`) se convierten en thin shims (~30-50 LOC re-export) y la implementación canónica vive en shared. Los 6+ consumers copilot siguen funcionando sin modificación. Trade-off: 3 archivos shim viven hasta DEFERRED-post-S6 cleanup (sweep de imports copilot directos a shared) — pero zero risk migration vs touching 6 archivos al día 1.
- **Listo para S6**: el arch ratchet `test_no_hardcoded_channel_in_output_manager.py` es punto fijo. S6 puede sumar a la matriz de fitness tests + invariants. El channel registry es cross-agent — futuros agentes (email_agent, voice_agent) registran via `register_channel(fmt)` sin modificar shared. La migración sales OutputManager+compose_system_prompt es completa para los 7 canales canónicos.

---

## Decisiones clave

- **Move + extend vs redesign**:
  - Tomada: mover los 3 archivos copilot a `shared/agent_observability/channels/` con cero cambio de comportamiento + extender `ChannelFormat` con 3 campos opcionales (defaults preservan back-compat). Copilot mantiene shims re-export.
  - Razón: el código copilot ya cumplía los criterios senior (`@dataclass(frozen=True, slots=True)`, idempotent register, get-with-fallback, reset-for-tests). Redesign sería deuda técnica gratuita. La extensión por campos opcionales con defaults None preserva la firma de constructor para los 7 baseline (todos pasan field=value posicional/keyword).
  - Alternativa descartada: rewrite from scratch en shared (los 3 archivos canónicos, breaking copilot consumers). Rechazada — 6+ consumers en copilot/synthesizer.py + output_sanitizer.py + chat.py + tools/registry.py + 3 archivos test directos. Migrar todos en S5 = scope creep + alto riesgo.

- **Aliases dict en lugar de canal duplicado**:
  - Tomada: `_CHANNEL_ID_ALIASES: dict[str, str] = {"instagram": "instagram_dm"}` en `format.py`. `get_channel_format("instagram")` resuelve a `instagram_dm` baseline.
  - Razón: sales `ChannelResolver._CHANNEL_MAP` ya tiene clave `"instagram"` (no `_dm`). FE/BE inconsistency histórica. Crear un canal `"instagram"` separado duplicaría specs. Crear un alias dict centraliza la traducción sin duplicar.
  - Alternativa descartada: rename ChannelResolver a `instagram_dm`. Rechazada — `ChannelResolver._CHANNEL_MAP` es §3 adyacente (webhook adapters reglas existentes). Cambio cascada al webhook routing — fuera de scope S5.

- **`chunk_size` como campo opcional, no required**:
  - Tomada: `chunk_size: int | None = None`. Channels sin chunk_size declared (chat, email, voice, sms) mantienen legacy paragraph-only behavior. Solo `whatsapp` (1024) e `instagram_dm` (900) declaran cap.
  - Razón: SMS / chat / email / voice no necesitan post-paragraph splitting — chat es desktop UI sin caps reales, SMS ya cae bajo el max_chars=160 truncate de format_for_channel, email es 5000 que rara vez excede, voice es para TTS (timing manda). Forzar chunk_size en todos sería cap espurio que truncaría conversaciones largas en chat sin razón.
  - Alternativa descartada: chunk_size=max_chars default. Rechazada — semánticamente chunk_size (split en chunks múltiples) ≠ max_chars (cap de truncación). El registry distingue ambos conceptos.

- **`typing_simulation_cpm` declarativo pero NO consumido**:
  - Tomada: agregar el campo (default None) sin wirear `OutputManager._calculate_typing_time`. CPM_SPEED global de `domain/tuning.py` sigue activo.
  - Razón: §3 protected dice "CPM_SPEED + caracter cap calibrados, no tocar". El campo declarativo está disponible para S6 si se decide override per-canal (ej. SMS no necesita typing simulation, voice tampoco). FLAGGED en tech debt log.
  - Alternativa descartada: wirear ya con preferencia `fmt.typing_simulation_cpm or cls.CPM_SPEED`. Rechazada — toca §3.

- **Telegram MarkdownV2 escape como utility, NO auto-aplicado**:
  - Tomada: `escape_markdown_v2(text)` exportado desde `format.py`. NO consumido por `format_for_channel_impl`. Channel adapter Telegram (`shared/links/ports/channel_adapter.py::create_telegram_adapter`) consume cuando le toque.
  - Razón: auto-aplicar el escape en el post-processor rompería intentional markdown del LLM. El escape correcto requiere context (escape solo chars NO parte de markdown sintáctico) — implementación correcta requiere parser (parsimonious / marko-py / similar). Una utility "escape ALL special chars" es útil para texto plano que NO debería renderizar markdown — usable por adapter cuando el LLM emite plain text via channel con `parse_mode=MarkdownV2` activo.
  - Alternativa descartada: integrar al `format_for_channel_impl`. Rechazada — semantics diff: post-processor strip-markdown vs escape-markdown son incompatibles.

- **Slot 6 NO usa fallback "chat" cuando channel_type is None**:
  - Tomada: `_channel_format_hint(state)` retorna `""` si `state.channel_type` viene None / "". Solo cuando channel_type es explícito set, slot se popula.
  - Razón: cache stability. Si el slot poblara siempre con "chat" baseline cuando channel_type=None, el prefix cambia entre None ↔ explicit channel — invalida cache cross-turn cuando el orchestrator agrega channel_type post-hoc. Mejor: slot vacío si no sabemos el canal.
  - Alternativa descartada: poblar slot 6 siempre con "chat" fallback. Rechazada — agrega ~150 chars de hint genérico al cacheable prefix por turnos donde el canal aún no está resolved.

- **Boundary preference en `_split_by_cap`**:
  - Tomada: sentence-end (". " / "! " / "? " / "…" / "\n") → whitespace → hard cut. Boundary char queda en LEFT piece para legibilidad.
  - Razón: sales messages chunking en WhatsApp (cap 1024) debe leer natural. Tests verifican `chunk[-1] in ".!?…\n "` para >= len(chunks)-1 chunks (último puede ser incompleto).
  - Alternativa descartada: split simple por whitespace. Rechazada — produce chunks que terminan a mitad de oración, lectura incómoda para el lead.

---

## Sorpresas / gotchas críticos

- **OutputManager NO tenía hardcoded if-else por canal** — el tech debt log original (entrada `[MEDIUM] OutputManager hardcodeado por canal`) se basaba en una intuición no verificada. Audit reveló: `_parse_response(channel_type)` recibía `# noqa: ARG003` (parámetro unused). El "tech debt" era un wiring missing, no anti-pattern. **Lección**: validar tech debt entries con grep AST antes de tomarlas como bug — el plan se simplifica si la realidad es menos rota que la documentación dice.

- **Backslash en docstring rompe ruff D301** — el primer draft del docstring de `_split_by_cap` usaba ``\\n`` para escapar el backslash literal. Ruff D301 flag: "Use `r\"\"\"` if any backslashes in a docstring". Fix: prefix `r"""` raw-string. **Lección**: cualquier docstring que mencione regex chars o escape sequences usa raw string prefix de entrada. Pattern aparece también en `format.py` docstring de módulo (mencionaba ``\``  \``  literal en specs de Telegram → reescrito sin el char en docstring).

- **`from src.shared.agent_observability.channels.format import SUPPORTED_CHANNELS as updated`** triggers ruff N811 — re-importar un constant con alias que no es UPPER_CASE rompe el naming convention check. Solución: importar el módulo y leer `module.SUPPORTED_CHANNELS`. **Lección**: cuando un test necesita re-leer un module-level constant después de mutación (registry pattern), import-the-module en lugar de import-the-constant. Esto también es semánticamente más correcto — el constant se REBINDS post-mutation, los tests deben leer fresh.

- **Compose nested `if isinstance(...) and isinstance(...): if condition` triggers SIM102** — ruff agrega los anidados a la lista de simplification offers. Resolver con `if A and B and C` collapsado. **Lección**: cuando AST walk inspecciona condiciones múltiples, preferir bool-and chain en lugar de nested if (lectura natural + ruff happy).

- **Copilot tests siguen consumiendo `from src.modules.copilot.domain.output_channels import ChannelFormat`** — el shim re-export funciona porque Python resuelve los re-exports transitivamente. 113 tests copilot verde sin tocar imports test. **Lección**: thin re-export shims son herramienta válida para migración sin breaking change cuando el SSoT mueve. Trade-off: los shims agregan ~50 LOC files por destination. Aceptable mientras el plan tiene fase de cleanup explícita (DEFERRED-post-S6).

- **Slot 6 cacheable invariant requiere channel_type stable cross-turn** — el primer test draft asumió slot 6 siempre populado. Falló cuando `_realistic_state(channel_type=None)` produjo prompt diferente vs `channel_type="whatsapp"`. **Lección**: cache invariant es válido SOLO bajo el mismo canal. Cross-canal change invalida cache (intencional). Tests deben asegurar (a) cross-turn mismo canal = mismo prefix, (b) cross-canal = prefix diferente.

---

## Recomendaciones accionables para S6

- [ ] **Arch ratchet pass S6 puede sumar `test_no_hardcoded_channel_in_output_manager.py` al snapshot** — hoy es un test individual. Si S6 formaliza un meta-arch test (each module has a no-hardcoded-X check), agregarlo al pattern.

- [ ] **Sweep de imports copilot directos a shared** — 6+ archivos copilot importan via shim hoy. Cleanup pass:
  ```bash
  cd backend && grep -rn "from src.modules.copilot.domain.output_channels\|from src.modules.copilot.application.tools.format_for_channel\|from src.modules.copilot.application.orchestrator.channel_intent_detector" src/ --include="*.py" | grep -v "copilot/domain/output_channels\|copilot/application/tools/format_for_channel\|copilot/application/orchestrator/channel_intent_detector"
  ```
  Cada hit → reemplazar con `from src.shared.agent_observability.channels.<module> import ...`. Después borrar los 3 shims. Plan: scope estricto + tests verdes pre-borrar.

- [ ] **Update `tests/architecture/test_ddd_boundaries.py:75` allowlist** — apuntar a `src.shared.agent_observability.channels.format` cuando los shims se borren.

- [ ] **Wirear `typing_simulation_cpm` en `OutputManager._calculate_typing_time`** SI S6 abre §3 ventana — `OutputManager` está bajo §3 hoy. Si S6 ratchet pass lo libera (validar antes con usuario), wirear: `cpm = fmt.typing_simulation_cpm or cls.CPM_SPEED`. Útil para SMS (typing 0 = no simulation), voice (similar).

- [ ] **Update docstring `agent_identity.j2` para retirar `## Reglas por Canal`** en S7 — slot 6 es ahora SSoT. La duplicación benigna actual es ~100-200 tokens extra por turn. S7 es el momento natural (touches Jinja templates).

- [ ] **Si S6 introduce nuevo canal (ej. `web_chat` separado)** — agregar entry en `_BASELINE` en `format.py`, declarar `chunk_size` si aplica, agregar test en `test_channel_registry.py::TestBaselineRegistry`. Arch test `test_baseline_covers_canonical_channels` se ajusta por si querés gate baseline (hoy gate=7).

---

## Hooks listos

- `backend/src/shared/agent_observability/channels/format.py::CHANNEL_FORMATS` — registry mutable. Lookup via `get_channel_format(channel_id)`. Mutación via `register_channel(fmt)`. Reset (tests only) via `reset_registry_for_tests()`.

- `backend/src/shared/agent_observability/channels/format.py::ChannelFormat` — dataclass frozen+slots. 8 campos: 5 required (id, label_es, max_chars, emoji_allowed, line_break_style, markdown_allowed, structure_hint) + 3 opcionales (chunk_size, typing_simulation_cpm, parse_mode).

- `backend/src/shared/agent_observability/channels/format.py::escape_markdown_v2(text)` — Telegram MarkdownV2 escape utility. Channel adapter Telegram consume cuando aplique.

- `backend/src/shared/agent_observability/channels/format_for_channel.py::format_for_channel` (LangChain @tool) y `format_for_channel_impl(content, channel_id)` (pure). Strip markdown / strip emoji / truncate per spec del registry.

- `backend/src/shared/agent_observability/channels/intent_detector.py::detect_channel_intent(user_msg)` — regex-based detection ("mándame por WhatsApp"). URL guard incluido.

- `backend/src/modules/sales_agent/infrastructure/external/output_manager.py::OutputManager._parse_response(raw, channel_type)` — wirea `_enforce_chunk_size(chunks, channel_type)` que consulta `get_channel_format(channel_type).chunk_size`. None → no enforcement.

- `backend/src/modules/sales_agent/application/prompts/compose.py::_channel_format_hint(state)` — slot 6 builder. Lee `state["channel_type"]` y resuelve via registry.

- `backend/tests/architecture/test_no_hardcoded_channel_in_output_manager.py` — 4 fitness tests sin allowlist:
  - `test_output_manager_module_exists`
  - `test_no_string_literal_channel_comparisons` (AST Compare scan)
  - `test_no_dict_keyed_by_channel_literal` (AST Dict scan)
  - `test_imports_get_channel_format` (regex import scan)

- `backend/tests/shared/agent_observability/channels/` — 3 test files (registry / format_for_channel / intent_detector) con 73 tests cross-agent.

- `backend/tests/modules/sales_agent/test_output_manager_uses_registry.py` — 9 integration tests (consumes registry + boundary preference + fallback).

- `backend/tests/modules/sales_agent/prompts/test_channel_format_hint_slot.py` — 8 integration tests (slot 6 wiring + cache invariant + alias resolution).

- `backend/src/modules/copilot/domain/output_channels.py` (shim 30 LOC) — re-export para back-compat. Mismo para `format_for_channel.py` y `channel_intent_detector.py`.

---

## Riesgos abiertos

- **Slot 6 duplica `## Reglas por Canal` con agent_identity.j2 hoy** — 100-200 tokens redundantes. Si S7 no se ejecuta, la duplicación persiste. DEFERRED-S7. Watchpoint: si emerge feedback de "el agente repite reglas del canal" en producción, priorizar S7.

- **Tenants con canales custom no documentados** — `register_channel(fmt)` permite agregar canales runtime, pero los 7 baseline son hardcoded en `_BASELINE` dict. Si un tenant integra un canal nuevo (ej. Discord), debe agregar al baseline o registrar en startup. Sin docs claras esto puede generar bugs de "canal X no resuelve". Mitigación: `get_channel_format` cae a `chat` baseline (safe fallback) — el adapter decide.

- **Cross-agent registry mutation race** — si copilot y sales registran canales custom al mismo tiempo en startup, theoretically race condition en `CHANNEL_FORMATS` dict. En práctica: register_channel ocurre al import de bootstrap module — single-threaded. No race detectado en tests. Arquitectónicamente seguro mientras los registers sigan siendo bootstrap-only.

- **`escape_markdown_v2` no auto-aplicado** — un specialist podría emitir texto con `.` `-` `!` literales pensando que se renderiza correcto en Telegram. Si el adapter Telegram NO escapa antes de send, el mensaje rompe. Verificar adapter implementation en S6/S7.

---

## Tech debt detectado (NO arreglado)

Ya en `05-tech-debt-log.md` sección "Detectados durante S5":

- [MEDIUM] `agent_identity.j2` duplica `## Reglas por Canal` con slot 6 → DEFERRED-S7.
- [LOW] `format_for_channel` tool no wireado en sales tools registry → DEFERRED-S8.
- [LOW] `channel_intent_detector` no wireado en sales orchestrator → DEFERRED-post-S6.
- [LOW] `typing_simulation_cpm` declarado pero no consumido → FLAGGED.
- [LOW] Copilot shims `output_channels.py` + `format_for_channel.py` + `channel_intent_detector.py` re-export only → DEFERRED-post-S6.
- [LOW] Test `test_ddd_boundaries.py:75` allowlist apunta a path obsoleto → DEFERRED-post-S6.

Y FIXED arriba:

- [MEDIUM] OutputManager hardcodeado por canal → FIXED en S5 (con caveat: era wiring missing, no anti-pattern).
- [LOW] `agent_identity.j2` mezcla offer + channel rules → FIXED-PARTIAL en S5 (slot 6 populated, retire del bloque inline DEFERRED-S7).

---

## Fuentes research útiles

Solo las que **cambiaron una decisión**.

- [WhatsApp Business API limits 2026](https://www.engagespark.com/support/whatsapp-business-limits/) + [SparkTG limit guide 2026](https://blogs.sparktg.com/limit-on-message-length-whatsapp-business-api.html) — confirmaron 4096 session text + 1024 templates + markdown subset propio (NO estándar). Decisión: `max_chars=4096` para session, `chunk_size=1024` para template-safe + Evolution API v2 wrapper compatible. `markdown_allowed=False` (estricto).
- [Telegram Bot API MarkdownV2 spec](https://core.telegram.org/bots/api) — confirmó lista exacta de chars que MUST escapar: `_*[]()~`>#+-=|{}.!`. Decisión: `escape_markdown_v2` utility cubre los 18 chars + backslash. parse_mode field declarativo en baseline Telegram.
- [Instagram DM character limits 2026](https://www.inro.social/blog/how-many-direct-messages-can-you-send-on-instagram) — confirmó 1000 chars cap (emojis cuentan ≥2 chars). Decisión: `max_chars=1000`, `chunk_size=900` (headroom para emojis), `markdown_allowed=False`.
- [GSM-7 vs UCS-2 Wikipedia](https://en.wikipedia.org/wiki/GSM_03.38) + [Twilio GSM-7 guide](https://www.twilio.com/docs/glossary/what-is-gsm-7-character-encoding) — confirmaron tildes españolas no están en GSM-7 base, fuerzan UCS-2 (cap 70). Decisión: SMS `max_chars=160`, structure_hint advierte explícito sin tildes/emoji.
- [Evolution API v2 sendText docs](https://doc.evolution-api.com/v2/api-reference/message-controller/send-text) — confirmó adapter wraps WhatsApp Cloud API con misma char specs. Decisión: NO crear `evolution` channel separado; sales `channel_type="whatsapp"` cubre tenants que usen Evolution. Adapter mapea internamente.

---

## Métricas medidas

- BE quality gates nativos: `ruff check src/ tests/ --no-cache` 0 errors (1 warning pre-existing en `offer_type_presets.py:28` no S5), `ruff format --check` 1729 files clean.
- `pytest tests/modules/sales_agent/ tests/architecture/ tests/admin/ tests/shared/ tests/modules/copilot/ -x -q`: **3134 passed, 1 warning** (Pydantic deprecation, no impacto).
- Tests nuevos S5: **90+** (32 channel_registry + 18 format_for_channel + 14 intent_detector + 9 output_manager_uses_registry + 8 channel_format_hint_slot + 4 arch_no_hardcoded_channel + tests cubre tests legacy via shim).
- Tests legacy copilot via shim: 113 passed (test_output_channel_format + test_format_for_channel_tool + test_channel_intent_detector + test_channel_formatter_compliance arch).
- Tests legacy sales OutputManager: 10 passed (block stripping + paragraph chunking + markdown code blocks).
- Files nuevos: 7 (3 shared modules + 1 shared __init__ + 3 test files + 1 test __init__).
- Files modificados: 6 (compose.py + output_manager.py + 3 copilot shims + S5 phase doc).
- LOC añadidas: ~1100 (incluye learnings + tests + module canónico + tech debt entries).
- Spanish neutro: NO regresión — structure_hint del registry cross-canal en español neutro (revisado los 7 baseline, no voseo). Channel hint del slot 6 inyecta `# Reglas del canal (Label)\n\n{structure_hint}` al cacheable prefix.
- Cache hit rate impact: slot 6 ahora populated (~150-250 chars per channel) en cacheable prefix. Esto AGREGA bytes cacheables (no invalida — cross-turn mismo canal el slot es estable). Hit rate target ≥60% mantenido. Validable post-deploy con `SELECT SUM(cached_read_tokens)::numeric / SUM(input_tokens) FROM sales_agent_llm_call WHERE tenant_id=:t AND occurred_on >= NOW() - INTERVAL '7 days';`.
