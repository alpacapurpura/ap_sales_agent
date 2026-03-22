# 07 — Prompt System

## Vision General

El sistema de prompts es **hibrido multitenant**: combina templates en archivos Jinja2 (fallback) con versiones almacenadas en base de datos (override per-tenant). Esto permite que cada tenant tenga prompts personalizados sin modificar codigo.

```
                    ┌──────────────────────┐
                    │    prompt_loader      │
                    │   .render("key")      │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
         ┌────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
         │  Cache    │   │    DB     │   │   File    │
         │ (memory)  │   │ (prompt_  │   │ (.j2)     │
         │ TTL=60s   │   │ versions) │   │           │
         └───────────┘   └───────────┘   └───────────┘
              ▲                │                │
              │         Tenant Override        │
              │         → System Default       │
              │         → File Fallback ───────┘
              │                │
              └────────────────┘
```

---

## 1. PromptLoader

**Archivo:** `backend/src/modules/sales_agent/infrastructure/prompts/base.py` (L17-174)

### Modos de Operacion (`settings.PROMPT_SOURCE`)

| Mode | Behavior |
|------|----------|
| `FILE` | Solo lee de archivos `.j2`. Ignora BD. |
| `DB` | Solo lee de BD. Si no encuentra, lanza error. |
| `HYBRID` (default) | Cache → DB (tenant-specific → system default) → File fallback |

### render() — Metodo Principal (L109-165)

```python
def render(self, template_name: str, **kwargs: Any) -> str:
    key = template_name.replace(".j2", "")
    mode = settings.PROMPT_SOURCE
    tenant_id = get_tenant_id()  # Contextvars

    # 1. Inject tenant config as template variables
    if tenant_id:
        tenant_config = self._get_tenant_config(tenant_id)
        full_context = {**tenant_config, **kwargs}  # kwargs overrides
    else:
        full_context = kwargs

    # 2. Mode FILE: direct file load
    if mode == PromptSource.FILE:
        return self._load_from_file(key, template_name, **full_context)

    # 3. Mode DB/HYBRID: Cache → DB → File
    template_content = None
    cache_key = (key, tenant_id)

    # A. Try cache (TTL 60s)
    if cache_key in self._cache:
        if now - self._cache[cache_key]["loaded_at"] < 60:
            template_content = self._cache[cache_key]["content"]

    # B. Try DB
    if not template_content:
        template_content = self._get_from_db(key, tenant_id)

    # C. Render
    if template_content:
        template = self.fs_env.from_string(template_content)
        return template.render(**full_context)
    else:
        return self._load_from_file(key, template_name, **full_context)  # Fallback
```

### DB Lookup Strategy: Tenant Override → System Default (L62-94)

```python
def _get_from_db(self, key: str, tenant_id: Optional[UUID]) -> Optional[str]:
    # 1. Try tenant-specific override
    if tenant_id:
        prompt = select(PromptVersion).where(
            PromptVersion.key == key,
            PromptVersion.is_active,
            PromptVersion.tenant_id == tenant_id
        ).order_by(desc(PromptVersion.version))

    # 2. Try system default (tenant_id IS NULL)
    prompt = select(PromptVersion).where(
        PromptVersion.key == key,
        PromptVersion.is_active,
        PromptVersion.tenant_id.is_(None)
    ).order_by(desc(PromptVersion.version))
```

**Jerarquia de resolucion:**
1. **Tenant override:** Prompt con `key` + `tenant_id` = este tenant
2. **System default:** Prompt con `key` + `tenant_id IS NULL`
3. **File fallback:** Archivo `{key}.j2` en `templates/`

### Auto-Configuration: Variables del Tenant (L120-128)
```python
if tenant_id:
    tenant_config = self._get_tenant_config(tenant_id)
    full_context = {**tenant_config, **kwargs}
```
Las variables de `tenant.config_json` se inyectan automaticamente como variables Jinja2. Si un tenant tiene `config_json = {"brand_name": "Nicolify"}`, todos sus templates pueden usar `{{ brand_name }}` sin pasarlo explicitamente.

### Singleton Instance (L174)
```python
prompt_loader = PromptLoader()
```
Se importa en todos los modulos como `from ...base import prompt_loader`.

---

## 2. PromptVersion Model (BD)

**Archivo:** `backend/src/modules/sales_agent/infrastructure/models/prompt_version_model.py` (L7-19)

```python
class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(UUID, primary_key=True)
    key = Column(String, index=True)          # "supervisor_routing", "specialist_qualifier", etc.
    version = Column(Integer)                  # Auto-incrementing per key
    content = Column(Text)                     # The actual Jinja2 template
    is_active = Column(Boolean, default=True)
    change_reason = Column(String)             # "A/B test variant", "fixed tone"
    author_id = Column(String)                 # "system" or user UUID
    metadata_info = Column(JSONB)              # target_node, target_model, etc.
    tenant_id = Column(UUID)                   # NULL = system default, UUID = tenant override
    created_at = Column(DateTime)
```

**Versionado:** Cada cambio crea una nueva fila con `version + 1`. Solo la version con `is_active = True` se usa. Esto permite rollback instantaneo.

---

## 3. Templates Jinja2 (Todos los .j2)

**Directorio:** `backend/src/modules/sales_agent/infrastructure/prompts/templates/`

### agent_identity.j2 (113 lineas)
**Usado en:** `knowledge_builder.py:78`
**Proposito:** Identidad completa del agente (Brand + Offer + Avatar + Testimonials + Safety Rules).
**Detalle:** Ver [05-AGENT-IDENTITY-SYSTEM.md](05-AGENT-IDENTITY-SYSTEM.md).

### supervisor_routing.j2 (27 lineas)
**Usado en:** `nodes.py:25`
**Proposito:** Routing del supervisor a especialistas.
```
You are the Sales Supervisor. Route to the most appropriate specialist.

Available Specialists:
1. Qualifier: Gather information about the lead
2. ProductExpert: Answer specific questions about products
3. Closer: Handle buying intent, price, objections
4. Scheduler: Book a call

Current Context:
- User Intent: {{ intent }}
- Lead Score: {{ lead_score }}
- Funnel Stage: {{ stage }}

Decision Rules:
- unknown/early-stage → "qualifier"
- product details → "product_expert"
- buying signals/objections → "closer"
- schedule/book → "scheduler"

Output ONLY one word: "qualifier", "product_expert", "closer", or "scheduler".
```

### specialist_qualifier.j2 (24 lineas)
**Usado en:** `nodes.py:54`
**Proposito:** Instrucciones para el nodo Qualifier.
- **Objetivos:** Discover situation, uncover pain, identify goals, assess fit
- **Reglas:** No pitch yet, deep questions, 2-3 questions per turn, validate feelings
- **Patron:** Preguntas cerradas con 2-3 opciones (mas facil responder en chat)

### specialist_product_expert.j2 (22 lineas)
**Usado en:** `nodes.py:68`
**Proposito:** Instrucciones para el nodo Product Expert.
- **Objetivos:** Answer with authority, connect features to benefits, be precise
- **Reglas:** Tie back to pain points, never invent, suggest forward if buying interest
- **Variable dinamica:** `{{ context_rag }}` — Contexto recuperado de Qdrant (RAG)

### specialist_closer.j2 (25 lineas)
**Usado en:** `nodes.py:85`
**Proposito:** Instrucciones para el nodo Closer.
- **Framework:** Aikido Verbal (Validate → Reframe → Bridge → CTA)
- **Reglas:** Never invent prices, use guarantee for trust objections, share payment/calendar links
- **Temperatura:** 0.4 (mas creativo para persuasion)

### message_completeness.j2 (3 lineas)
**Usado en:** `semantic.py:24`
**Proposito:** Clasificador binario para el Smart Buffer.
```
Eres un clasificador binario de intención de escritura.
Determina si el mensaje está 'COMPLETO' o 'INCOMPLETO'.
Responde SOLO con una palabra.
```

### safety_context_check.j2 (8 lineas)
**Usado en:** Safety layer (content moderation)
**Proposito:** Evalua si un fragmento de texto debe ser censurado.
**Variables:** `{{ match_text }}`, `{{ security_instruction }}`, `{{ full_context }}`

### summary_generator.j2 (20 lineas)
**Usado en:** Session summary generation
**Proposito:** Genera resumen de sesion para memoria episodica.
**Output:** 2 oraciones: pain/goal + status/objection + emotional tone.

### offer_psychology_generator.j2 (31 lineas)
**Usado en:** Offer Studio AI tools
**Proposito:** Genera pains y desires psicologicos para ofertas.
**Output:** JSON con listas `pains` y `desires`.

---

## 4. Flujo de Renderizado (Ejemplo)

```
nodes.py → prompt_loader.render("specialist_qualifier")
    │
    ├─ key = "specialist_qualifier"
    ├─ tenant_id = UUID("abc-123")  (from contextvars)
    │
    ├─ Check cache: ("specialist_qualifier", UUID("abc-123"))
    │   → MISS
    │
    ├─ Check DB:
    │   1. SELECT * FROM prompt_versions WHERE key='specialist_qualifier'
    │      AND tenant_id='abc-123' AND is_active=true ORDER BY version DESC
    │      → NULL (no tenant override)
    │
    │   2. SELECT * FROM prompt_versions WHERE key='specialist_qualifier'
    │      AND tenant_id IS NULL AND is_active=true ORDER BY version DESC
    │      → NULL (no system default in DB)
    │
    ├─ Fallback to file:
    │   → Load templates/specialist_qualifier.j2
    │   → Render with full_context (kwargs + tenant_config)
    │
    └─ Return rendered string
```

---

## Casuisticas

### Que pasa si un tenant quiere un prompt custom?
Se inserta un registro en `prompt_versions` con `key="specialist_qualifier"`, `tenant_id=<UUID>`, `is_active=true`. La proxima vez que `render()` se llame para ese tenant, usara el override de BD en vez del archivo.

### Que pasa si el template Jinja2 tiene un error de sintaxis?
El `except` en L161-165 catchea el error. Si estamos en modo HYBRID, fallback al archivo. Si estamos en modo DB, propaga el error.

### Como se invalida el cache?
```python
prompt_loader.invalidate_cache("specialist_qualifier")
```
Elimina todas las entradas del cache para ese key (todos los tenants). Se deberia llamar cuando se actualiza un prompt en la BD.

### El TTL de 60 segundos puede causar prompts desactualizados?
Si, por hasta 60 segundos. Esto es aceptable para cambios de configuracion (no son time-critical). Para cambios urgentes, se puede llamar `invalidate_cache()`.
