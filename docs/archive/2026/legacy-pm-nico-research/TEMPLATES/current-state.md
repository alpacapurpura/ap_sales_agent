# {module} — Estado funcional actual

> SSoT funcional módulo. Mantenido por `/pm`. **Vista user-facing, no técnica.**
> Update obligatorio cuando feature shipea (rule `pm-nico-ssot.md`).

## Meta

| Campo | Valor |
|---|---|
| Módulo | {módulo} |
| Studio padre | Brand / Offer / Growth / Sales / Config / Supporting |
| Estado | activo / placeholder / nuevo / deprecated |
| Última actualización | {YYYY-MM-DD} |
| Doc técnico | `docs/domains/module_{m}.md` |

## Qué hace por el user

1 párrafo descriptivo. Vista user-facing, no técnica. ¿Qué problema le resuelve a alguien que entra a Nicolify?

## Capacidades actuales

Bullets de qué PUEDE hacer un user hoy. Verbos en infinitivo + 1 frase.

- {Verbo + complemento — qué resuelve}
- ...

## Capacidades operables desde copilot

- {Capacidad operable conversacionalmente}
- {Capacidad NO operable conversacionalmente — gap}

## Estado calidad funcional

| Capacidad | Estado | Notas |
|---|---|---|
| {capacidad} | sólido / débil / buggy / placeholder | {1 frase} |

## Conexiones cross-módulo

- **Lee de:** {módulos input}
- **Lo lee:** {módulos consumers}

## Dolor user / oportunidades detectadas

Captura señales que motivan futuras opportunities. Append-only.

| Fecha | Señal | Origen | Opportunity? |
|---|---|---|---|
| {YYYY-MM-DD} | {qué reportó user / qué se observó} | {dónde} | `opportunities/{slug}.md` o pendiente |

## PIs históricos que tocaron este módulo

| PI | Cambio | Fecha cierre |
|---|---|---|
| PI-N | {qué cambió} | {YYYY-MM-DD} |

## Decisiones producto vinculadas

Decisiones funcionales clave que afectaron este módulo. ADR-style.

| Fecha | Decisión | Razón | PI/PR origen |
|---|---|---|---|
| {YYYY-MM-DD} | {qué} | {por qué} | {link} |
