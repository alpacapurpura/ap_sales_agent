# FP2 — `format_for_channel` auto-trigger middleware (B24-TP11)

**Bug origen:** TP11 J2.T2 + J2.T3 user pidió "armame copy WhatsApp" 2 veces, copilot ignoró.
**TP origen:** `results/TP11-2026-04-26.md §B24-TP11`.
**Tiempo estimado:** 4-8 horas.
**Pre-req hard:** FP1 cerrado (ambos tocan `chat.py` orchestrator).
**Capa stack:** Backend (chat orchestrator middleware + tool binding heuristics).

---

## Misión

Garantizar que cuando el user pida output en canal específico (WhatsApp / email / SMS / Instagram DM / Telegram), el copilot **siempre** invoque `format_for_channel` tool — independiente del phrasing exacto del user. Hoy depende del LLM descubriéndolo, y Kimi K2.6 es phrasing-sensitive (B11-TP6).

---

## Research mandate

Queries:

- `"langchain force tool selection trigger keyword 2026 middleware"` — patrones force-binding tools por intent detection.
- `"intent classification short utterance LLM 2026 keyword vs embedding"` — si usar regex keywords o embedding similarity.
- `"deepagents tool routing middleware before_model 2026"` — hook points en deepagents 0.5.3.

Tessl tiles: `tessl__langgraph` si aplica.

---

## Acceptance criteria

| AC | Descripción | Evidence pre-fix | Evidence post-fix |
|---|---|---|---|
| **AC1** | User msg matches `(whatsapp\|wa)` keyword (case-insensitive, accent-insensitive) → `format_for_channel` está en bound tools del turn | trace event `tool_call` ausente | trace event `tool_call name='format_for_channel'` con `args.channel='whatsapp'` |
| **AC2** | User msg matches `(email\|correo\|gmail)` → same para channel='email' | tool ausente | tool fired |
| **AC3** | User msg matches `(sms\|texto)` → same para channel='sms' | tool ausente | tool fired |
| **AC4** | User msg matches `(copia.*pega\|copy.*paste)` sin canal específico → copilot pregunta canal en T+1 (clarification) — NO inventa | copilot inventaría / responde generic | clarification card emitida |
| **AC5** | Output formateado WhatsApp respeta constraints: sin markdown asterisks, ≤1024 chars segmentos, sin headers `#` | output con markdown roto | output WA-clean validado |
| **AC6** | Match es accent-insensitive y case-insensitive (e.g. "WhatsApp", "whatsapp", "WHATSAPP") | inconsistente | match consistente |
| **AC7** | False positive: msg "una landing en whatsapp.com" NO trigger force-bind (URL mention, not channel intent) | n/a | tool NO bound |

---

## Procedimiento por AC

### Setup
- TP11 J2 conversation `08a002c5-...` o crear nueva. Reproducir bug:
  - Send "armame copy para WhatsApp" → confirm `tool_call` event ausente para `format_for_channel`.

### AC1-AC3 — keyword detection

1. **Investigar code path actual:** `grep -rn "format_for_channel\|channel_format" backend/src/modules/copilot/`. Localizar:
   - Tool definition file
   - Bind path en `chat.py::_build_dynamic_tools` o `tools/registry.py`
   - Dynamic tool selection logic (`get_tools_for_context`)
2. **Diseño middleware:**
   - Crear `application/orchestrator/channel_intent_detector.py` con función `detect_channel_intent(user_msg: str) -> ChannelIntent | None`.
   - `ChannelIntent` dataclass: `channel: str` ("whatsapp" / "email" / "sms" / "instagram_dm" / "telegram") + `confidence: float`.
   - Implementar via regex case+accent insensitive con anchored boundary (evitar false positives URL).
3. **Wire middleware:** en `chat.py::CopilotOrchestrator.run` antes de bind tools, llamar `intent = detect_channel_intent(user_msg)` y si no None, force-add `"channel_format"` group al `bound_groups` set.
4. **System prompt hint:** si intent detectado, append a system prompt: `"El usuario pidió formato {channel}. USA \`format_for_channel\` con channel='{channel}' antes de finalizar la respuesta."`.
5. **Test RED:** unit test `test_channel_intent_detector.py` con casos por canal.
6. **Test GREEN:** implementar.
7. **Live re-run J2.T2 mismo prompt** → trace event `tool_call format_for_channel` debe aparecer.

### AC4 — clarification path

1. Si keyword "copia.*pega" sin canal específico → middleware NO force-bind tool, pero agregar hint a system prompt: "El usuario pidió copy listo, pregunta el canal antes de generar".
2. Test live: scenario "armame algo para copy paste" → copilot pide canal.

### AC5 — WhatsApp output validation

1. Re-run J2.T2 post-fix → verificar output `panelEnd` no contiene markdown roto (`**`, `##`, etc).
2. Test BE: `format_for_channel` tool con `channel='whatsapp'` debe devolver string sin markdown asterisks.
3. Si fail: investigar `application/tools/format_for_channel.py` post-process logic.

### AC6 — accent/case insensitive

1. Test parametrize: ["WhatsApp", "whatsapp", "WHATSAPP", "wa", "WA"] → todos detectados.
2. Test ["Wassap" / "WhatsAp"] (typos) → 0 detection (NO too-loose match).

### AC7 — false positive control

1. Test ["mira esta landing https://whatsapp.com/landing"] → NO detection (URL mention, not intent).
2. Implement via regex que excluye `(?<!\.)(whatsapp)(?!\.com|/)` o equivalent — context-aware.

---

## Tests / archivos a crear / modificar

### Backend
- `backend/src/modules/copilot/application/orchestrator/channel_intent_detector.py` (NEW)
- `backend/src/modules/copilot/application/orchestrator/chat.py` (UPDATE — wire middleware + system prompt hint)
- `backend/src/modules/copilot/application/tools/format_for_channel.py` (UPDATE si needed para AC5 cleaning)
- `backend/tests/modules/copilot/test_channel_intent_detector.py` (NEW — 20+ parametrized cases)
- `backend/tests/modules/copilot/test_channel_format_auto_trigger.py` (NEW — integration test mock LLM con channel msg)

---

## Failure playbook

- **Force-binding rompe budget tools:** muchos tools en bound set = más tokens en system prompt. Verificar trace events post-fix que tokens no exploten.
- **System prompt hint causa LLM ignore otra request:** validar que el hint se agrega como instrucción ADD-ON, no replaces el system prompt principal.
- **Regex demasiado loose / strict:** iterar test parametrize hasta cubrir 95% real-world phrasings sin false positives.
- **Embedding similarity considered:** si regex muy frágil, F-pos posterior considerar embedding-based intent (reuse OpenAI embedding-3-large). NO en FP2 — keep regex first.

---

## Sub-bugs descubiertos durante FP2

> Append-only.

- (none yet)

---

## Output esperado

`results/FP2-{fecha}.md` con:
- Pre-research insights
- AC1-AC7 checklist con evidence
- Tests added
- Sub-bugs
- Métricas: regex performance + tokens delta cuando middleware activa
- Aprendizajes para FP3
- Handoff prompt en `prompts/FP3-start.md`
