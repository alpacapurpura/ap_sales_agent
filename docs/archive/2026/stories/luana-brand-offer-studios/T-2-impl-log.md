---
ticket: T-2
title: "Create luana-core-brand-studio package skeleton"
started_at: 2026-05-11
state: assigned
---

## Plan

1. mkdir -p core/luana-core-brand-studio/src/luana_core_brand_studio
2. mkdir -p core/luana-core-brand-studio/tests
3. Write pyproject.toml per 03-arch.md §8.1
4. Write README.md stub
5. Create empty __init__.py files
6. Run uv sync --all-packages to verify skeleton resolves
7. Commit: `feat(luana-core-brand-studio): skeleton + pyproject.toml + README`
