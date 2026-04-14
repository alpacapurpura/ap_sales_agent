# Personality Engine — Design Spec

**Date:** 2026-04-13
**Status:** Approved
**Scope:** Fase 1 — Presets + Clonación desde chat history
**Visual brainstorm files:** `.superpowers/brainstorm/16107-1776130306/content/`

---

## 1. Problem Statement

El sales agent de Nicolify habla de forma genérica. El campo `identity.voice_tone` es un string libre ("conversacional, aspiracional") que no produce comportamiento consistente ni diferenciado. La personalidad está dispersa en 6 campos sin modelo unificado. El usuario no tiene forma de hacer que su agente suene como él/ella.

## 2. Architecture: 3-Layer Compositional Model

El system instruction del sales agent se compone de 3 capas independientes. La personalidad SIEMPRE tiene prioridad.

### Capa 1: Personalidad (QUIEN eres) — Fase 1
- **Scope:** 1 por marca (brand-level), inmutable
- **Donde se configura:** Brand Studio → Voz y Personalidad
- **Fuente:** Preset pre-configurado O clonación desde chat history
- **Test ácido:** Si quitaras el contexto de venta y la persona estuviera hablando de fútbol — ¿seguiría sonando igual? Entonces ES personalidad.

### Capa 2: Estrategia de Venta (COMO vendes) — Fase 2
- **Scope:** 1 por oferta (offer-level), configurable
- **Donde se configura:** Offer Studio (auto-configurado según tipo/precio)
- **Test ácido:** Si cambiaras al vendedor pero mantuvieras la misma táctica — ¿seguiría funcionando? Entonces ES estrategia.

**Defaults inteligentes por tipo de oferta:**

| Oferta | Estrategia default |
|---|---|
| Lead magnet (gratis) | Consultiva suave, presión 0, persistencia baja |
| Tripwire ($7-47) | Relacional + micro-urgencia, persistencia media |
| Curso medio ($97-497) | Challenger + social proof + urgencia real |
| High-ticket ($997-5K) | Qualification + consultiva + escasez genuina |
| Mentoría 1:1 ($5K+) | Diagnóstica + ROI + exclusividad + agenda call |
| Evento/Lanzamiento | Urgencia máxima + FOMO + countdown + follow-up agresivo |

### Capa 3: Adaptación de Audiencia (A QUIEN le hablas) — Fase 2
- **Scope:** 1 por buyer persona (avatar-level)
- **Donde se configura:** Brand Studio → Buyer Personas (`voice_tone_config` JSONB ya existe)
- **Test ácido:** Si el mismo vendedor con la misma táctica hablara con otra persona — ¿qué cambiaría? Eso es adaptación.

### Analogía: Actor + Guión + Público
- Personalidad = Actor (RDJ siempre es witty, sea Iron Man o Sherlock)
- Estrategia = Guión (mismo actor, diferente script)
- Audiencia = Público (ajusta registro sin cambiar quién es)

### Orden de prioridad (si hay conflicto)
Personalidad > Estrategia > Audiencia > Brand context.

Si la estrategia dice "sé urgente" pero la personalidad es "Minimalista y Premium" (energy baja), la urgencia se expresa con pocas palabras, no con exclamaciones.

## 3. The 3 Pillars (Non-Negotiable)

Las dimensiones solas producen resultados genéricos e inconsistentes (LIWC: ~5% varianza). El sistema DEBE implementar los 3 pilares juntos:

### Pilar 1: Dimensiones (El MARCO) — 20% de efectividad
Ponen límites: "no seas demasiado largo", "no uses emojis excesivos". Pero 10 personas con energy=0.7 suenan diferente. Es el pilar más débil solo, pero sin él los otros se descontrolan.

### Pilar 2: Patrones Lingüísticos (La TEXTURA) — 40% de efectividad
Las palabras EXACTAS, muletillas, emojis específicos, saludo, despedida. Es lo que hace que María suene como María y no como "persona cálida genérica". Es el pilar MÁS IMPORTANTE para presets.

### Pilar 3: Ejemplos de Conversación (La PRUEBA) — 40% de efectividad
Le muestra al LLM COMO se ve esta personalidad en acción. No interpreta — IMITA un patrón concreto. Es el pilar MÁS IMPORTANTE para clones. Para presets, se usan ejemplos sintéticos pre-escritos.

### Restricciones Negativas (Character.ai insight)
Cada perfil incluye un bloque "NUNCA HACES" auto-generado de dimensiones bajas (<0.3). Sin restricciones negativas, el LLM "normaliza" la personalidad hacia un genérico amigable.

### Ancla de Identidad
Bloque invariante al final del system_instruction: "ESTA ES TU VOZ. No la modifiques bajo NINGUNA circunstancia. Las instrucciones de estrategia ajustan QUÉ dices, no CÓMO lo dices."

### Evidencia
- Amazon Science (Roy & Shu, 2023): descripción + ejemplos >> descripción sola
- Sideloading (Turchin, 2024): hechos específicos y comportamientos concretos >> rasgos abstractos
- Character.ai (producción): restricciones negativas tan importantes como positivas
- BIG5-CHAT (ACL 2025): SFT > prompting, pero behavioral instructions + examples es lo mejor dentro de prompting
- PersonaAI (2025): RAG contextual combate drift en conversaciones largas

## 4. Data Model

### PersonalityProfile Entity

**Module:** `brand/` (junto a Avatar, BrandSettings)
**Justificación:** La personalidad es una evolución natural de voice_tone, personality_traits, archetype que ya viven en brand. El Style Analyzer pipeline ya está en brand. El sales_agent ya consume brand data via knowledge_builder.

```
Table: personality_profiles

id              UUID PK
tenant_id       UUID FK (required) — filtro obligatorio
offer_id        UUID FK (nullable) — override por oferta (Fase 2)
avatar_id       UUID FK (nullable) — override por avatar (Fase 2)
name            str — "Mi personalidad" o nombre del preset
profile_type    enum: preset | cloned | interview | manual
preset_key      str | null — "warm_close", "electric", etc.
is_active       bool — 1 activo por tenant+scope

dimensions      JSONB — {energy: 0.7, warmth: 0.85, humor: 0.6, ...}
linguistic_patterns  JSONB — {emoji_style, favorite_emojis, greeting, farewell, filler_phrases, ...}
sample_exchanges     JSONB — [{context, other_message, author_response}, ...] (5-8 para presets, 10-15 para clones)
negative_constraints JSONB — ["NUNCA uses emojis", ...] (auto-generado de dimensiones bajas)
system_instruction   TEXT — prompt compilado (5 bloques: reglas + huella + negativas + ejemplos + ancla)

source_metadata JSONB — {message_count, confidence, formats_used, extraction_date}
qdrant_collection   str — "personality_style_anchors" (null para presets)
anchor_count    int — cuántos style anchors en Qdrant (0 para presets)
llm_provider    str — "openai" | "anthropic" | etc.
llm_model       str — "gpt-4o" | "claude-sonnet-4-6" | etc.

created_at      datetime (UTC)
updated_at      datetime (UTC)
deleted_at      datetime | null (soft delete)
```

### Qdrant: Style Anchors (solo para clones)

```
Collection: personality_style_anchors

Point:
  id: UUID
  vector: float[] (embedding del intercambio)
  payload:
    tenant_id: UUID    — FILTRO OBLIGATORIO en toda query
    profile_id: UUID
    context_type: str  — "greeting" | "price_question" | "objection" | "closing" | "follow_up" | "casual"
    other_message: str — lo que dijo el prospecto/otro
    author_response: str — lo que respondió el usuario
```

Una collection única con filtro por `tenant_id` + `profile_id`. No una collection por tenant.

### Presets Registry (en código, no en DB)

```python
# brand/domain/personality.py
PERSONALITY_PRESETS: dict[str, PresetDefinition] = {
    "warm_close": PresetDefinition(
        name="Cálida y Cercana",
        icon="☀️",
        dimensions=PersonalityDimensions(energy=0.65, warmth=0.85, humor=0.6, ...),
        linguistic_patterns=LinguisticPatterns(emoji_style="frequent", ...),
        sample_exchanges=[...],  # 5-8 intercambios sintéticos pre-escritos
        # negative_constraints se auto-genera del contrato de dimensiones
    ),
    ...
}
```

Agregar un preset = agregar un entry al dict. Zero migraciones.

## 5. Dimension Contract

Cada dimensión tiene 5 niveles con reglas concretas. El compilador resuelve el nivel y emite instrucciones explícitas. El LLM nunca ve números.

### Dimensiones

| Dimensión | Rango | Descripción |
|---|---|---|
| energy | 0.0–1.0 | Calma ↔ Eléctrica |
| warmth | 0.0–1.0 | Distante ↔ Íntima |
| humor | 0.0–1.0 | Serio ↔ Cómico |
| expressiveness | 0.0–1.0 | Minimalista ↔ Maximalista |
| narrative | 0.0–1.0 | Factual ↔ Cinematográfica |
| verbosity | 0.0–1.0 | Telegráfico ↔ Elaborado |

### Niveles por dimensión (ejemplo: Energy)

| Rango | Nivel | Reglas concretas |
|---|---|---|
| 0.0–0.2 | Muy baja | Sin exclamaciones. Respuestas mesuradas. "Interesante." "Entiendo." |
| 0.2–0.4 | Baja | Exclamaciones raras (1 por conversación). Calma pero presente. |
| 0.4–0.6 | Media | Exclamaciones moderadas. Entusiasmo cuando el tema lo amerita. |
| 0.6–0.8 | Alta | Exclamaciones frecuentes. Ritmo ágil. "vamos!", "dale!" |
| 0.8–1.0 | Eléctrica | MAYÚSCULAS intencionales. "INCREIBLE!!!" "VAMOS 🔥🔥" |

Cada una de las 6 dimensiones tiene esta tabla completa de 5 niveles definida en `DimensionContract`. Ver archivos visuales para el contrato completo de las 6 dimensiones.

### Auto-generación de restricciones negativas

Dimensiones con valor < 0.3 generan automáticamente restricciones "NUNCA":
- energy < 0.3 → "NUNCA uses exclamaciones múltiples"
- warmth < 0.3 → "NUNCA uses diminutivos ni preguntes cosas personales"
- humor < 0.3 → "NUNCA hagas chistes ni uses jaja/jeje"
- expressiveness < 0.3 → "NUNCA uses emojis"
- narrative < 0.3 → "NUNCA cuentes historias, ve directo a los datos"
- verbosity < 0.3 → "NUNCA escribas más de 2 oraciones por mensaje"

## 6. System Instruction Compilation

El `PersonalityCompiler` genera el `system_instruction` con 5 bloques en este orden:

```
BLOQUE 1: Reglas de personalidad (compilado de dimensiones → contrato → instrucciones concretas)
BLOQUE 2: Huella lingüística (patrones específicos: muletillas, emojis, saludos, despedidas)
BLOQUE 3: Restricciones negativas (auto-generado de dimensiones bajas, "NUNCA HACES:")
BLOQUE 4: Ejemplos de conversación (sintéticos para presets / reales para clones)
BLOQUE 5: Ancla de identidad ("ESTA ES TU VOZ. No la modifiques bajo NINGUNA circunstancia.")
```

## 7. 6 Presets de Personalidad Pura

Cada preset define los 3 pilares completos. No contienen estrategia de venta (eso va en Capa 2).

| # | Key | Nombre | Energía | Calidez | Humor | Expresividad | Narrativa | Verbosidad |
|---|---|---|---|---|---|---|---|---|
| 1 | warm_close | Cálida y Cercana ☀️ | 0.65 | 0.85 | 0.6 | 0.7 | 0.5 | 0.4 |
| 2 | electric | Eléctrica y Expresiva ⚡ | 0.9 | 0.7 | 0.7 | 0.9 | 0.5 | 0.5 |
| 3 | serene | Serena y Articulada 🧠 | 0.35 | 0.5 | 0.3 | 0.3 | 0.5 | 0.6 |
| 4 | direct | Directa y Sin Filtro 🔥 | 0.8 | 0.4 | 0.5 | 0.3 | 0.3 | 0.25 |
| 5 | narrative | Narrativa y Vívida 📖 | 0.55 | 0.6 | 0.5 | 0.7 | 0.85 | 0.7 |
| 6 | minimalist | Minimalista y Premium 🖤 | 0.15 | 0.25 | 0.1 | 0.1 | 0.2 | 0.15 |

Cada preset incluye además:
- `linguistic_patterns`: muletillas, emojis favoritos, saludo, despedida, estilo de puntuación
- `sample_exchanges`: 5-8 intercambios sintéticos en contextos clave (saludo, pregunta de precio, objeción, cierre, follow-up)
- `negative_constraints`: auto-generadas de dimensiones bajas (ej: Minimalista → "NUNCA uses emojis", "NUNCA hagas chistes")

## 8. Cloning Pipeline (LangGraph, 6 nodos)

Evolución del Style Analyzer existente (`brand/application/agents/style_analyzer/`). Hoy tiene 4 nodos; agregamos 2 (Parser + Embedder).

### Nodo 1: Parser (NUEVO)
- **Input:** archivo raw (WhatsApp .txt, IG JSON, Telegram JSON)
- **Acción:** Detecta formato, extrae solo mensajes del usuario, convierte a formato unificado
- **LLM:** No (parsing determinístico con regex/JSON)
- **Output:** `List[Message(text, timestamp, has_emoji, word_count)]`
- **Formatos soportados (Fase 1):** WhatsApp .txt (P0), Instagram DM JSON (P1), Telegram JSON (P2)

### Nodo 2: Janitor (EXISTE)
- **Input:** List[Message]
- **Acción:** Redacta PII (emails, teléfonos, direcciones), elimina mensajes de sistema, filtra spam/forwards
- **LLM:** Sí (redacción inteligente)
- **Output:** `List[CleanMessage]`

### Nodo 3: Psychologist (EVOLUCIONAR)
- **Input:** List[CleanMessage]
- **Acción:** Analiza mensajes y extrae los 3 pilares con structured output JSON
- **LLM:** Sí (configurable: OpenAI/Claude/etc)
- **Output:** `PersonalityProfile(dimensions, linguistic_patterns, sample_exchanges, confidence)`
- **Prompt:** Pide evidencia por dimensión (citar 2+ mensajes que justifiquen cada valor)

### Nodo 4: Architect (EVOLUCIONAR)
- **Input:** PersonalityProfile
- **Acción:** Compila los 5 bloques del system_instruction usando DimensionContract
- **LLM:** Sí (para redacción natural de las instrucciones)
- **Output:** `system_instruction` (texto compilado)

### Nodo 5: Embedder (NUEVO)
- **Input:** sample_exchanges del PersonalityProfile
- **Acción:** Embebe los 10-15 mejores intercambios en Qdrant con metadata (tenant_id, profile_id, context_type)
- **LLM:** No (usa embedding model)
- **Output:** `anchor_count` + `qdrant_collection` ref

### Nodo 6: Simulator (EXISTE)
- **Input:** system_instruction compilado
- **Acción:** Genera 3 respuestas de simulación para validación del usuario (saludo, objeción de precio, follow-up)
- **LLM:** Sí (usa el system_instruction recién compilado)
- **Output:** `List[SimulatedResponse]`

### Privacy: Process-and-Delete
El chat raw se procesa en memoria y se elimina después de la extracción. Solo se persiste: PersonalityProfile (DB) + style anchors (Qdrant). Cumple GDPR, Ley 29733 (Perú), LFPDPPP (México).

## 9. Sales Agent Integration (Runtime)

En cada turno del sales agent:

### Paso 1: knowledge_builder (existente, extender)
Carga PersonalityProfile activo del tenant. Inyecta `system_instruction` como primer bloque del system prompt.

```python
# Hoy:
brand = brand_repo.get_settings(tenant_id)
identity["voice_tone"] = brand.identity.voice_tone

# Después:
profile = personality_repo.get_active(tenant_id)
identity["personality_instruction"] = profile.system_instruction
```

### Paso 2: style_anchor_retriever (NUEVO)
Si el perfil tiene `anchor_count > 0`, busca en Qdrant 2-3 style anchors similares al mensaje actual del prospecto. Los inyecta como few-shot dinámico en el prompt. Filtro obligatorio: `tenant_id` + `profile_id`.

Esto combate el drift en conversaciones largas: los ejemplos frescos se inyectan en CADA turno, no solo al inicio.

### Paso 3: strategy_resolver (Fase 2)
Detecta qué oferta se está vendiendo. Carga estrategia de Capa 2. Inyecta como segundo bloque.

### System prompt final:
```
[Capa 1] Personalidad: reglas + patrones + restricciones negativas + ancla
[Capa 2] Estrategia (Fase 2): presión, urgencia, cierre según oferta
[Capa 3] Audiencia (Fase 2): formalidad, vocabulario según buyer persona
[RAG] 2-3 style anchors similares al contexto actual
[Existing] Brand identity, offers, testimonials, team, avatar, channel rules
```

## 10. UI Flow (Brand Studio)

### Estado: Sin personalidad configurada
- Pantalla vacía con 2 CTAs: "Elegir un preset" / "Clonar mi personalidad"

### Flujo A: Elegir Preset
1. Catálogo de 6 cards con icon, nombre, descripción, y ejemplo de mensaje
2. Click selecciona → preview con chat simulado
3. (Opcional) Ajustar dimensiones con sliders → recalcula system_instruction y regenera preview
4. Guardar → materializa como PersonalityProfile row

### Flujo B: Clonar
1. Upload de archivo (drag & drop o click)
2. Formatos aceptados: .txt (WhatsApp), .json (IG, Telegram)
3. Loading state mientras el pipeline procesa (30-60 seg)
4. Resultado: perfil extraído con dimensiones (barras), patrones (chips), simulación (chat mock)
5. (Opcional) Ajustar dimensiones con sliders
6. Guardar → PersonalityProfile + style anchors en Qdrant

### Estado: Personalidad activa
- Resumen con: nombre, tipo (preset/clonado), barras de dimensiones, huella lingüística (chips)
- Preview en vivo: chat simulado con 2 intercambios (pregunta de precio + objeción)
- Botones: Editar (sliders), Cambiar (volver al selector), Regenerar preview

> **NOTA PARA FASE 2:** El preview en vivo debe integrarse con el Copilot sidebar. Evaluar si el chat de simulación se renderiza inline en la página de personalidad O si se mueve al Copilot panel como un modo "preview de personalidad". La infraestructura del Copilot expandable sidebar (3 estados) ya soportaría esto. Revisar cuando se implemente la integración Copilot.

## 11. Module Structure

```
modules/brand/
  domain/
    personality.py              # PersonalityProfile entity, PersonalityDimensions VO,
                                # DimensionContract, LinguisticPatterns VO,
                                # PresetDefinition, PERSONALITY_PRESETS dict,
                                # PersonalityCompiler
    ...existing files unchanged...

  infrastructure/
    models/
      personality_model.py      # SQLAlchemy model (personality_profiles table)
    repositories/
      personality_repository.py # CRUD, get_active(tenant_id), deactivate_others()
    qdrant/
      style_anchor_store.py     # Qdrant client: upsert_anchors(), search_similar(),
                                # delete_by_profile(), COLLECTION_NAME
    parsers/
      whatsapp_parser.py        # WhatsApp .txt → List[Message]
      instagram_parser.py       # IG JSON → List[Message]
      telegram_parser.py        # Telegram JSON → List[Message]
      base.py                   # ChatParser protocol, Message dataclass
    ...existing files unchanged...

  application/
    agents/style_analyzer/      # EVOLUCIONAR pipeline existente (4→6 nodos)
      graph.py                  # LangGraph graph (add Parser + Embedder nodes)
      nodes.py                  # Evolucionar Psychologist + Architect
      prompts.py                # Evolucionar prompts para structured output
      state.py                  # Evolucionar state schema
    services/
      personality_service.py    # select_preset(), clone_from_chat(), get_active(),
                                # update_dimensions(), compile_instruction(),
                                # delete_with_anchors()
    ...existing files unchanged...

  api/
    personality.py              # GET /presets, GET /active, POST /select-preset,
                                # POST /clone, PUT /{id}/dimensions, DELETE /{id},
                                # POST /{id}/simulate
    ...existing files unchanged...

modules/sales_agent/
  application/
    services/
      knowledge_builder.py      # EXTENDER: cargar PersonalityProfile activo
      style_anchor_retriever.py # NUEVO: buscar style anchors en Qdrant por turno
```

## 12. API Endpoints

```
GET    /api/v1/brand/personality/presets          # Catálogo de presets (público por tenant)
GET    /api/v1/brand/personality/active            # Perfil activo del tenant
POST   /api/v1/brand/personality/select-preset     # Materializar un preset como perfil activo
POST   /api/v1/brand/personality/clone             # Upload chat + ejecutar pipeline
PUT    /api/v1/brand/personality/{id}/dimensions    # Ajustar dimensiones + recompilar
POST   /api/v1/brand/personality/{id}/simulate      # Regenerar preview de simulación
DELETE /api/v1/brand/personality/{id}               # Soft delete + limpiar Qdrant anchors
```

Todos filtrados por `X-Tenant-ID`. Todos con `response_model=`.

## 13. Fase 1 Scope (In/Out)

### IN (esta spec)
- PersonalityProfile entity en brand/ (domain + infra + app + api)
- 6 presets con 3 pilares cada uno (dimensiones + patrones + ejemplos sintéticos + restricciones negativas)
- Pipeline de clonación (6 nodos LangGraph, evolución del existente)
- Qdrant style anchors para clones (collection + retrieval multitenant)
- Contrato de dimensiones (DimensionContract + PersonalityCompiler)
- Integración sales agent (knowledge_builder + style_anchor_retriever)
- UI Brand Studio (selector de preset, upload de chat, preview, sliders)
- Parsers de WhatsApp .txt, IG JSON, Telegram JSON
- LLM configurable (OpenAI/Claude/etc vía configuración de tenant)
- Migración idempotente para tabla personality_profiles

### OUT (Fase 2)
- Entrevista con Copilot (usar interview engine existente)
- Capa 2: Estrategia de venta por oferta (UI en Offer Studio, defaults inteligentes)
- Capa 3: Adaptación por buyer persona (UI en Brand Studio → Avatars)
- Override de personalidad por offer/avatar (FK opcionales ya en el modelo)
- A/B testing de personalidades
- Versionamiento de perfiles
- Parser de audio transcripts
- Parser de email threads
- Integración del preview en vivo con Copilot sidebar

## 14. Research References

| Source | Finding | How we use it |
|---|---|---|
| LIWC (Yarkoni, 2010) | Personality traits = ~5% linguistic variance | Dimensions are FRAME only, not solution alone |
| Amazon Science (Roy & Shu, 2023) | Description + examples >> description alone | 3 pillars: dimensions + patterns + examples |
| Sideloading (Turchin, 2024) | Specific behaviors >> abstract traits | Compiled instructions with concrete rules |
| Character.ai (production) | Negative constraints as important as positive | Auto-generated "NUNCA HACES" block |
| BIG5-CHAT (ACL 2025) | Behavioral instructions + examples best for prompting | Our exact approach |
| PersonaAI (2025) | RAG contextual combats drift | Style anchors injected per turn |
| Challenger Sale (CEB) | 5 seller profiles, strategy != personality | Layer separation: personality vs strategy |
| Gong.io | Top sellers: 43% talk, 57% listen | Informs strategy layer defaults (Fase 2) |

## 15. Migration

Idempotent (raw SQL + IF NOT EXISTS), per project rules.

```sql
CREATE TABLE IF NOT EXISTS personality_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    offer_id UUID REFERENCES offers(id),
    avatar_id UUID REFERENCES avatars(id),
    name VARCHAR(255) NOT NULL,
    profile_type VARCHAR(20) NOT NULL DEFAULT 'preset',
    preset_key VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT false,
    dimensions JSONB NOT NULL DEFAULT '{}',
    linguistic_patterns JSONB NOT NULL DEFAULT '{}',
    sample_exchanges JSONB NOT NULL DEFAULT '[]',
    negative_constraints JSONB NOT NULL DEFAULT '[]',
    system_instruction TEXT,
    source_metadata JSONB NOT NULL DEFAULT '{}',
    qdrant_collection VARCHAR(100),
    anchor_count INTEGER NOT NULL DEFAULT 0,
    llm_provider VARCHAR(50),
    llm_model VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_personality_profiles_tenant
    ON personality_profiles(tenant_id) WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_personality_profiles_active
    ON personality_profiles(tenant_id)
    WHERE is_active = true AND deleted_at IS NULL AND offer_id IS NULL AND avatar_id IS NULL;
```

## 16. Backward Compatibility

El campo `identity.voice_tone` (string libre) sigue existiendo en BrandSettings. Convivencia:

- Si existe un PersonalityProfile activo → `knowledge_builder` usa `profile.system_instruction` e ignora `voice_tone`
- Si NO existe PersonalityProfile activo → fallback a `voice_tone` (comportamiento actual)
- El campo `voice_tone` no se elimina ni se migra. Los tenants existentes siguen funcionando sin cambios hasta que configuren una personalidad.

## 17. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| LLM interprets dimensions inconsistently | Generic-sounding agent | 3 pillars + negative constraints + examples anchor behavior |
| Personality drift in long conversations | Agent loses voice after 20+ turns | RAG style anchors injected every turn, not just at init |
| Chat export too small (<50 messages) | Low-confidence extraction | Psychologist reports confidence score; UI warns if <0.5 and suggests preset instead |
| Qdrant unavailable | Style anchors not retrieved | Graceful degradation: fall back to system_instruction only (presets always work) |
| Privacy: raw chat persisted | GDPR/legal risk | Process-and-delete: raw data never hits DB/disk, only structured profile + embeddings |
| Strategy overrides personality | Agent loses voice when selling aggressively | Priority order enforced: Personality > Strategy. Ancla de identidad at prompt end |
