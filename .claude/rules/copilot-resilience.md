---
globs: "backend/src/modules/copilot/**/*.py"
description: Copilot module resilience rules
---

# Copilot Resilience Rules

## Field Discovery
- NEVER hardcode field names in copilot tools
- Use `schema_introspection.py` for Pydantic model field discovery
- New fields/sections in existing models need NO copilot changes (auto-discovered)

## Module Registration
- New modules: add `ModuleDescriptor` to `copilot/domain/module_registry.py`
- Tools use `MODULE_REGISTRY` for data access, not direct repo imports

## Route Registration
- New routes: update `navigation_map.py` + `tools/registry.py` ROUTE_TOOL_MAP
- Route-based tool selection — only relevant tools are bound per route
