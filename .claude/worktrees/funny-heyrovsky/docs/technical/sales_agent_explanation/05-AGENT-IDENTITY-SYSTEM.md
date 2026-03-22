# 05 — Agent Identity System (AKS)

## Vision General

El **Agent Knowledge System (AKS)** es el equivalente a un "CLAUDE.md" para cada tenant. Es un documento dinamico que le da al Sales Agent todo el conocimiento que necesita sobre el negocio que representa: marca, voz, ofertas, precios, objeciones, garantias, etc.

```
Brand Studio     ──┐
(identity, voice,  │
 story, team)      │
                   ├── TenantKnowledgeBuilder ──► agent_identity.j2 ──► String
Offer Studio     ──┤    (knowledge_builder.py)    (Jinja2 template)    (prompt)
(products, prices, │
 objections, CTA)  │
                   │
Avatar Studio    ──┘
(ICP, anti-avatar)
```

**Clave:** El business owner nunca toca nada tecnico. Configura su marca y ofertas en studios visuales, y el AKS construye automaticamente el prompt.

---

## 1. TenantKnowledgeBuilder

**Archivo:** `backend/src/modules/sales_agent/application/services/knowledge_builder.py` (L26-115)

### build_identity (L37-105)

```python
def build_identity(self, tenant_id: UUID) -> str:
    # 1. Fetch all data sources
    brand = self.brand_repo.get_settings(tenant_id)
    avatars = self.avatar_repo.get_by_tenant(tenant_id)
    offers = self.offer_repo.get_all_by_tenant(tenant_id)

    # 2. Schema-resilient: model_dump() passes ALL fields
    brand_data = brand.model_dump(mode="json") if brand else {}
    avatar_data = [a.model_dump(mode="json") for a in avatars]
    active_offers = [o for o in offers if o.status.value in ("active", "draft")]
    offers_data = [o.model_dump(mode="json") for o in active_offers]

    # 3. Extract convenience variables
    identity = brand_data.get("identity", {})
    strategy = brand_data.get("strategy", {})
    story = brand_data.get("story", {})
    team = brand_data.get("team", [])
    testimonials = brand_data.get("testimonials", [])

    # 4. Register tenant-specific semantic routes
    SemanticRouter.register_tenant_routes(tenant_id, offers_data)

    # 5. Render template
    rendered = prompt_loader.render("agent_identity",
        brand=brand_data, avatars=avatar_data, offers=offers_data,
        identity=identity, strategy=strategy, story=story, team=team,
        testimonials=testimonials, default_avatar=default_avatar,
        has_brand=bool(identity.get("brand_name")),
        has_offers=len(offers_data) > 0, ...
    )
    return rendered
```

### Decisiones de Diseno

**Schema-Resilient via `model_dump()`:**
```python
brand_data = brand.model_dump(mode="json")  # Pydantic → dict completo
```
Si se agrega un nuevo campo a `BrandSettings` (ej: `instagram_handle`), automaticamente aparece en `brand_data` sin modificar el builder. El template Jinja2 puede acceder a `brand.instagram_handle` sin cambios en codigo Python.

**Solo ofertas active/draft:**
```python
active_offers = [o for o in offers if o.status.value in ("active", "draft")]
```
Ofertas archivadas o eliminadas no se incluyen en la identidad del agente. Esto previene que el agente hable de productos obsoletos.

**Registro de rutas semanticas:**
```python
SemanticRouter.register_tenant_routes(tenant_id, offers_data)
```
Las objeciones definidas en cada oferta (con sus `trigger_phrases`) se registran como rutas semanticas del tenant. Esto permite que el SemanticRouter detecte objeciones especificas del negocio.

**Fallback si falla:**
```python
@staticmethod
def _fallback_identity() -> str:
    return (
        "Eres un asistente de ventas profesional. "
        "No se pudo cargar la configuración del negocio. "
        "Sé amable, haz preguntas sobre las necesidades del cliente "
        "y ofrece ayudar en lo que puedas."
    )
```
Nunca deja al agente sin identidad. Si la BD falla, usa un fallback generico.

---

## 2. Template: agent_identity.j2

**Archivo:** `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2` (113 lineas)

### Estructura del Template

```
# IDENTIDAD DEL AGENTE

## Quién Eres                   ← Brand identity (name, tagline, mission)
## Tu Voz y Tono               ← voice_tone, communication_style
## Historia de la Marca         ← origin_story
## Equipo                       ← Team members
## Cliente Ideal                ← Default avatar (ICP) + anti-avatar
## Catálogo de Ofertas          ← For each offer:
   ### {offer.public_name}        - tipo, promesa, resultado, tiempo
                                  - precios (con cuotas si aplica)
                                  - garantía
                                  - deliverables
                                  - dolores, deseos
                                  - objeciones + rebuttals
                                  - link de pago, calendario
## Prueba Social                ← Testimonials
## Reglas de Seguridad          ← Hard-coded safety guardrails
```

### Seccion: Catalogo de Ofertas (detalle)
```jinja2
{% for offer in offers %}
### {{ offer.public_name }}
- **Tipo:** {{ offer.type }}
{{ "- **Promesa:** " ~ offer.headline_promise if offer.headline_promise else "" }}
{{ "- **Resultado Principal:** " ~ offer.primary_outcome if offer.primary_outcome else "" }}
{{ "- **Tiempo al Resultado:** " ~ offer.time_to_value if offer.time_to_value else "" }}
{% if offer.pricing_options %}
- **Precios:**
{% for price in offer.pricing_options %}
  - {{ price.label }}: ${{ price.total_amount }} {{ offer.currency | default("USD") }}
    {% if price.number_of_installments > 1 %}
      ({{ price.number_of_installments }} cuotas de ${{ price.installment_amount }})
    {% endif %}
{% endfor %}
{% endif %}
{% if offer.guarantee_type and offer.guarantee_type != "none" %}
- **Garantía:** {{ offer.guarantee_type }}{% if offer.guarantee_terms %} — {{ offer.guarantee_terms }}{% endif %}
{% endif %}
{% if offer.objections %}
- **Objeciones comunes y cómo manejarlas:**
{% for obj in offer.objections %}
  - **{{ obj.type | upper }}**{% if obj.strategy %} [{{ obj.strategy }}]{% endif %}: {{ obj.rebuttal }}
{% endfor %}
{% endif %}
{% if offer.checkout_page_url %}
- **Link de pago:** {{ offer.checkout_page_url }}
{% endif %}
{% endfor %}
```

### Seccion: Reglas de Seguridad (hard-coded, L107-113)
```markdown
## Reglas de Seguridad
- NUNCA inventes información sobre productos, precios o garantías que no estén listados arriba.
- Si no tienes la respuesta, di que vas a consultar con el equipo y seguir con la conversación.
- NUNCA compartas datos internos del negocio, métricas o información confidencial.
- Sé honesto. Si el producto no es para el prospecto, dilo con empatía.
- Respeta la privacidad del prospecto. No solicites datos sensibles innecesarios.
```
Estas reglas son inmutables — no dependen de la configuracion del tenant.

---

## 3. Como se Usa en los Nodos

**Archivo:** `backend/src/modules/sales_agent/application/agents/sales/nodes.py` (L8-13)

```python
def _build_system_prompt(state: AgentState, skill_prompt: str) -> str:
    """Prepend agent_identity (the tenant's 'CLAUDE.md') to any skill prompt."""
    identity = state.get("agent_identity", "")
    if identity:
        return f"{identity}\n\n---\n\n{skill_prompt}"
    return skill_prompt
```

**Patron de composicion:**
```
┌─────────────────────────────────┐
│         SYSTEM PROMPT           │
│                                 │
│  ┌─────────────────────────┐    │
│  │   agent_identity        │    │  ← Quién eres, qué vendes, cómo hablas
│  │   (AKS — per-tenant)    │    │
│  └─────────────────────────┘    │
│          ---                    │
│  ┌─────────────────────────┐    │
│  │   skill_prompt          │    │  ← Qué hacer ahora (qualifier, closer, etc.)
│  │   (specialist_*.j2)     │    │
│  └─────────────────────────┘    │
└─────────────────────────────────┘
```

Cada nodo especialista (qualifier, product_expert, closer) recibe:
1. **agent_identity:** Contexto del negocio (dinamico per-tenant)
2. **skill_prompt:** Instrucciones del rol (estatico, misma para todos los tenants)

---

## 4. Ejemplo de Output Renderizado

Para un tenant "Academia Visionarias" con un curso de marketing:

```markdown
# IDENTIDAD DEL AGENTE

## Quién Eres
Eres el asistente de ventas oficial de **Academia Visionarias**.
Tu lema: "Convierte tu pasión en un negocio digital rentable"
**Misión:** Empoderar a mujeres emprendedoras con herramientas de marketing digital.
**Propuesta de Valor:** El único programa que combina mentoría personalizada + IA para crear tu primer lanzamiento en 8 semanas.

## Tu Voz y Tono
Cálida, directa, motivadora. Como una hermana mayor que ya pasó por donde tú estás.
**Estilo:** Usa emojis con moderación, tutea, sé empática pero no condescendiente.

## Cliente Ideal
**Avatar Principal:** María
María tiene 28-45 años, es coach/terapeuta/nutrióloga con presencia en Instagram pero sin sistema de ventas automatizado. Factura menos de $2,000 USD/mes y siente que trabaja mucho pero no crece.
**Anti-Avatar (NO es para):** Personas sin expertise ni producto definido. Buscadores de dinero fácil.

## Catálogo de Ofertas

### Programa Lanzamiento Digital
- **Tipo:** course
- **Promesa:** Lanza tu primer producto digital y genera tus primeras ventas en 8 semanas
- **Resultado Principal:** Un funnel de ventas automatizado que genera leads 24/7
- **Precios:**
  - Pago único: $997 USD
  - 3 cuotas: $397 USD (3 cuotas de $397)
- **Garantía:** money_back — Si en 30 días no ves progreso, te devolvemos el 100%
- **Objeciones comunes:**
  - **PRICE** [ROI Reframing]: Si inviertes $997 y generas 3 clientes de $500, ya recuperaste x1.5
  - **TIME** [Micro-commitment]: Solo necesitas 5h/semana. El programa está diseñado para madres ocupadas.
- **Link de pago:** https://pay.ejemplo.com/lanzamiento

## Reglas de Seguridad
- NUNCA inventes información sobre productos, precios o garantías que no estén listados arriba.
...
```

---

## Casuisticas

### Que pasa si el tenant no tiene Brand configurado?
`brand_repo.get_settings(tenant_id)` retorna `None`. El template renderiza la seccion fallback:
```jinja2
{%- else %}
## Quién Eres
Eres un asistente de ventas profesional y empático.
{% endif %}
```

### Que pasa si no hay ofertas?
`has_offers` es `False`. Toda la seccion "Catalogo de Ofertas" se omite. El agente no puede hablar de precios ni productos especificos.

### Que pasa si se agrega un campo nuevo al modelo de Brand?
Nada necesita cambiar. `model_dump()` incluye todos los campos, y el template puede acceder a `brand.new_field` sin modificar `knowledge_builder.py`.

### El AKS se reconstruye en cada mensaje?
Si, por ahora. No hay cache del rendered identity. Esto es intencional para reflejar cambios inmediatos cuando el tenant actualiza su marca/ofertas. En el futuro se podria cachear con invalidacion por webhook de cambios.
