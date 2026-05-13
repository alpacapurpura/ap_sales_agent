"""SystemPromptComposer — 7-section system prompt builder.

See CONTRACT §20.1. Composition order (top → bottom):

    1. base_identity
    2. global_rules
    3. route_scoped_rules
    4. active_skills (each with skill-scoped rules)
    5. tenant_context_block
    6. conversation_summary
    7. tool_catalog_hint
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from jinja2 import Environment, StrictUndefined

if TYPE_CHECKING:
    from luana_core_copilot.domain.ports import CopilotContext
    from luana_core_copilot.domain.rules.rule_definition import RuleDefinition
    from luana_core_copilot.domain.rules.rule_registry import RuleRegistry
    from luana_core_copilot.domain.skills.skill_definition import SkillDefinition
    from luana_core_copilot.domain.skills.skill_registry import SkillRegistry


_BASE_IDENTITY = (
    "Eres el copiloto de Nicolify. Operas en español neutro latam "
    "(tuteo, sin voseo). Hablas caveman: directo, compacto, sin floreo. "
    "Nunca inventas datos. Si algo falta, lo dices y pides lo mínimo."
)


_TEMPLATE_SRC = """\
# Identidad

{{ base_identity }}

{%- if global_rules %}

## Reglas globales

{% for rule in global_rules -%}
- **{{ rule.metadata.name }}** (prio {{ rule.metadata.priority }}): {{ rule.metadata.description }}
{% endfor %}
{%- endif %}

{%- if route_rules %}

## Reglas de la ruta actual

{% for rule in route_rules -%}
- **{{ rule.metadata.name }}**: {{ rule.metadata.description }}
{% endfor %}
{%- endif %}

{%- if active_skills %}

## Skills activas

{% for entry in active_skills -%}
### Skill: {{ entry.skill.metadata.name }} (v{{ entry.skill.metadata.version }})

{{ entry.skill.body_markdown.strip() }}

{%- if entry.rules %}

Reglas específicas de esta skill:
{% for rule in entry.rules -%}
- **{{ rule.metadata.name }}**: {{ rule.metadata.description }}
{% endfor %}
{%- endif %}

{% endfor %}
{%- endif %}

{%- if tenant_context %}

## Contexto del tenant

{{ tenant_context }}
{%- endif %}

{%- if summary %}

## Resumen de la conversación

{{ summary }}
{%- endif %}

## Hint de catálogo de herramientas

Usa solo herramientas provistas por el runtime. Nunca inventes nombres de
tools. Propón mutaciones únicamente vía `propose_field_updates` y espera
aprobación del usuario.
"""


def _format_tenant_context(tenant_profile: dict[str, Any] | None) -> str | None:
    """Flatten a tenant profile dict into a compact caveman block."""
    if not tenant_profile:
        return None
    lines: list[str] = []
    keys = (
        "business_types",
        "brand_name",
        "value_proposition",
        "default_currency",
        "timezone",
    )
    lines.extend(f"- {key}: {tenant_profile[key]}" for key in keys if tenant_profile.get(key))
    return "\n".join(lines) if lines else None


class SystemPromptComposer:
    """Deterministic Jinja2-based system-prompt builder."""

    def __init__(
        self,
        skill_registry: SkillRegistry,
        rule_registry: RuleRegistry,
    ) -> None:
        """Wire both registries."""
        self._skill_registry = skill_registry
        self._rule_registry = rule_registry
        self._env = Environment(
            autoescape=False,
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._template = self._env.from_string(_TEMPLATE_SRC)

    def compose(
        self,
        context: CopilotContext,
        active_skills: list[SkillDefinition],
        summary: str | None = None,
        tenant_profile: dict[str, Any] | None = None,
    ) -> str:
        """Produce the full system prompt string."""
        global_rules = self._rule_registry.global_rules()
        route_rules = self._rule_registry.for_route(context.current_route)

        skill_entries: list[dict[str, Any]] = []
        for skill in active_skills:
            skill_rules = self._rule_registry.for_skill(skill.metadata.name)
            skill_entries.append({"skill": skill, "rules": skill_rules})

        tenant_ctx = _format_tenant_context(tenant_profile)

        return self._template.render(
            base_identity=_BASE_IDENTITY,
            global_rules=global_rules,
            route_rules=route_rules,
            active_skills=skill_entries,
            tenant_context=tenant_ctx,
            summary=summary,
        ).rstrip()

    # Convenience accessor (exposed for introspection tests).
    @staticmethod
    def base_identity() -> str:
        """Return the static base-identity header."""
        return _BASE_IDENTITY

    @staticmethod
    def _rule_sort_key(rule: RuleDefinition) -> tuple[int, str]:
        """Stable sort key: (priority asc, name asc)."""
        return rule.metadata.priority, rule.metadata.name
