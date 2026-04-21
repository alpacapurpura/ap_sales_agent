---
globs: "backend/src/modules/copilot/**/*.py"
description: Copilot module resilience rules
---

# Copilot Resilience

## Field Discovery
- NEVER hardcode field names en copilot tools
- Use `schema_introspection.py` para Pydantic model field discovery
- New fields/sections en existing models need NO copilot changes (auto-discovered)

## Module Registration
- New modules: add `ModuleDescriptor` to `copilot/domain/module_registry.py`
- Tools use `MODULE_REGISTRY` for data access, no direct repo imports

## Route Registration
- New routes: update `navigation_map.py` + `tools/registry.py` ROUTE_TOOL_MAP
- Route-based tool selection — only relevant tools bound per route
