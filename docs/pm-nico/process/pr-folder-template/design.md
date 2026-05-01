# DESIGN — PR-{N}-{slug}

> Owner: `nicolify-ux-designer` agent. Approved by: {user} on {date}.
> Builder consume `UI-SPEC.md` + este `design.md` como SSoT — NO redesigna.

## Skills consultados
{Lista — `ux-flow-architect`, `frontend-expert`, `tessl__shadcn-ui`, `tessl__tailwind`, + domain-expert si aplica + `ux-disruptivo` si user pidió creative + `tessl__figma-to-code` si Figma reference}

## Iteraciones
| # | Fecha | User feedback | Cambio aplicado |
|---|---|---|---|
| 1 | {date} | "..." | "..." |

## Scope expansions detectadas (escalated to PM)
| # | User request | PM decision | Outcome |
|---|---|---|---|
| 1 | "..." | A) restructure / B) defer / C) reject | "..." |

(Si NO hubo expansion: "Ninguna. Mockup respeta scope PR.md.")

## Design tokens usados
- Color: {bg-card, text-foreground, border-input, etc — NUNCA hex hardcoded}
- Spacing: {gap-2, gap-4, p-4, py-3}
- Radius: {rounded-md (Shadcn default)}
- Typography: {text-sm, text-base, font-semibold, text-2xl}

## Componentes Shadcn usados (existentes en `components/ui/`)
{Lista — Table, Sheet, Dialog, Checkbox, Input, Popover, Command, Slider, Badge, Tooltip, Sonner...}

## Componentes nuevos requeridos (builder crea)
| Componente | Tipo (shared/ui/feature) | Path destino | Razón |
|---|---|---|---|
| `DataTable` | shared primitive | `components/shared/data-table/` | Cross-feature reuse |

## Mockups finales aprobados
- `mockups/{screen-1}.html`
- `mockups/{screen-2}.html`
- ...

## Aprobado por
{user name} on {date}
