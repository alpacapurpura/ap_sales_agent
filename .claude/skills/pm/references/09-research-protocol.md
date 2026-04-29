# Research Protocol — "Robar como artista"

> Web + Reddit + producto análogos. Antes definir feature crítica, investigar 6m últimos. PM exitoso roba bien, no inventa.

## Cuándo investigar

| Trigger | Profundidad |
|---|---|
| Nuevo PI grande (módulo nuevo) | Profundo (1-2h, 5-10 fuentes) |
| Feature significativa dentro PI | Medio (30-60min, 3-5 fuentes) |
| Decisión arquitectónica (modelo, vendor) | Profundo |
| Bug fix / mejora pequeña | Skip |

## Cómo

### 1. Define preguntas antes buscar

Sin preguntas claras → research vago. Ejemplos:
- "¿Cómo Productos {X, Y, Z} resolvieron el problema {P}?"
- "¿Qué patrón conversacional usan SDR AI 2025-26?"
- "¿Hay startup en {sector} con {capacidad} ya?"
- "¿Qué reportan users en Reddit sobre {herramienta análoga}?"

### 2. Fuentes prioritarias

| Fuente | Uso |
|---|---|
| Reddit (`r/SaaS`, `r/marketing`, `r/Entrepreneur`, `r/InfoProducts`, niche subs) | Tendencias real talk + dolor user genuino |
| Twitter/X | Industry leaders signal |
| Hacker News | Tech-side patterns |
| Product Hunt | Productos análogos lanzados |
| Lenny's Newsletter | PM patterns probados |
| Reforge content | Frameworks growth/PLG |
| YC startup blogs | Patterns startups exitosas |
| Specific product docs (HubSpot, Jasper, Writer, 11x, Replit Agent) | Patrones agentic 2026 |

### 3. Delegación a subagente

Para research denso, **delegá**. Mantenés convo principal limpia.

Patrón:
```
Agent({
  description: "Research patterns campaign module",
  subagent_type: "general-purpose",
  prompt: """
    Investigá últimos 6 meses cómo {3 productos análogos} manejaron
    {capacidad X}. Reddit + Twitter + product docs. Cita fuentes.
    Devuelve brief máximo 300 palabras con:
    - 3 patrones predominantes
    - 2 anti-patterns visibles
    - 3 quotes Reddit dolor user
    - Aplicabilidad Nicolify (1 frase por patrón)
  """
})
```

Brief vuelve al PM. PM transcribe a `research/{date}-{slug}.md`.

### 4. Documentar en research/

`research/{YYYY-MM-DD}-{slug}.md` siguiendo template `TEMPLATES/research.md`:
- Fecha + slug + tema + disparador
- Fuentes citadas
- Hallazgos clave
- Aplicabilidad Nicolify (qué tomamos / adaptamos / descartamos)
- Anti-patterns detectados
- Open questions

### 5. Vincular a PR

PR.md sección "Inspiración / Robar como artista" linkea research file. Trazabilidad completa: research → opportunity → PR → entrega.

## Reddit-specific tips

- Buscar `[problema]` o `[herramienta] reviews` en subs nicho
- Filtros: top all-time, top year, hot
- "Why I switched from X to Y" hilos = oro puro
- Comentarios > posts. Real talk vive en comentarios.
- Subs Nicolify-relevantes:
  - r/SaaS, r/Entrepreneur, r/InfoProducts, r/copywriting
  - r/marketing, r/PPC, r/digital_marketing
  - r/consulting, r/freelance (target user)
  - r/ChatGPTPromptGenius, r/AIAgents

## Anti-patterns

- ❌ Research como gathering sin preguntas → análisis paralisis
- ❌ Confundir "lo que hace X startup" con "lo que necesita user"
- ❌ Skip Reddit (es donde vive el dolor real)
- ❌ Citar fuente sin URL → no auditable
- ❌ Aplicabilidad genérica ("podríamos adaptar X") sin decisión clara

## Reference

- "Steal Like an Artist" — Austin Kleon
- Marty Cagan — *Inspired*: continuous discovery via market signals
