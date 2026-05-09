# Story 9 — Luana v0.1.0 release

> **Outcome:** luana-platform-migration · **Sequence:** 9/14

## What

Promote Luana de `0.0.x-alpha` a `0.1.0` (production-grade alpha). Release engineering cross-package.

## Scope

- All Python packages: bump to `0.1.0`
- All TypeScript packages: bump to `0.1.0`
- semantic-release auto-tags `v0.1.0` en `luana-core` repo
- Changelog generated cross-packages
- API reference docs auto-gen (Python: pdoc/sphinx; TS: typedoc)
- Extension points docs published `luana-core/docs/extension-points.md`
- Migration guide for consumers (`docs/migration-from-nicolify.md`)
- GitHub release with assets

## Acceptance

- All packages tagged `v0.1.0` and published to GH Packages
- `luana-core@0.1.0` documentation site live (GitHub Pages)
- Smoke test: nuevo proyecto stub puede `pip install luana-core-platform==0.1.0` + `npm install @luana/ui-kit@0.1.0` y construir un mini-app funcional
- All 5 critical extension points (EP-1..EP-5) callable + tested
- CI green across all packages
- No `0.0.x-alpha` packages reference circular

## Effort: 5-8 tickets, ~2 días
