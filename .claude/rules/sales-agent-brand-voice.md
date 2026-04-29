---
globs: "backend/src/modules/sales_agent/**/*.py,backend/src/modules/brand/domain/personality.py"
description: Stub — invoca sales-agent-expert skill
---

# Sales Agent Brand Voice

SSoT voz sales_agent = `personality_profiles.system_instruction`. Compiler v2 (6 bloques, "ASÍ HABLAS / ASÍ NO"). Slot 5 `BRAND_VOICE` cache prefix. Brand Studio `/brand-studio/estilo` punto único config tenant.

Detalle (compilador, slot architecture, micro-anchor per-turn, cache invalidation, voice fidelity grader, tests obligatorios, research stack) en `sales-agent-expert` skill → `references/sales-agent-brand-voice.md`.

**No-skip creep guard:**
- ❌ NO crear tabla `brand_voice_summary` ni mirror LLM-distilled
- ❌ NO fine-tuning per tenant
- ❌ NO voice-rewriter LLM pass post-generación
- ❌ NO hardcodear voz en `agent_identity.j2` o specialists
- ❌ NO inyectar `{tenant_name}` mid-block cache prefix

Voseo: `spanish-text.md` NO aplica al output sales_agent (respeta voz tenant).
