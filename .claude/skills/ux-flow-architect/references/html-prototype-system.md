# HTML Prototype System

Technical reference for generating clickable multi-page prototypes in Phase 5.

---

## Directory Structure

All HTML files live inside the current session folder, alongside the specs and plan:

```
docs/ux-sessions/{YYYY-MM-DD}-{slug}/prototype/
├── index.html                        (meta refresh → dashboard.html or first studio)
├── dashboard.html                    (proposed dashboard home — if applicable)
├── brand-studio/
│   ├── esencia.html
│   ├── estrategia.html
│   ├── publico.html
│   ├── identidad-creativa.html
│   ├── tono-y-voz.html              (newly surfaced)
│   └── assets.html                   (newly surfaced)
├── offer-studio/
│   ├── index.html                    (offer list)
│   └── offer-detail.html            (represents /offer/[id])
├── growth-studio/
│   ├── atraccion.html
│   ├── nutricion.html
│   ├── ventas.html
│   ├── adopcion.html
│   ├── expansion.html
│   └── campanas.html                (newly surfaced)
├── sales/
│   ├── resumen.html
│   ├── inbox.html
│   ├── pipeline.html
│   ├── frozen.html
│   └── contactos.html
├── settings/
│   ├── index.html
│   └── connections.html
└── styles.css                        (shared styles + design tokens)
```

Only generate pages relevant to the approved changes. Don't generate the full app if only auditing one studio.

---

## Base HTML Template

Every page uses this structure:

```html
<!DOCTYPE html>
<html lang="es" class="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{PAGE_TITLE}} — Nicolify Flow Preview</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            background: 'hsl(0, 0%, 100%)',
            foreground: 'hsl(222.2, 84%, 4.9%)',
            card: 'hsl(0, 0%, 100%)',
            'card-foreground': 'hsl(222.2, 84%, 4.9%)',
            popover: 'hsl(0, 0%, 100%)',
            'popover-foreground': 'hsl(222.2, 84%, 4.9%)',
            primary: { DEFAULT: 'hsl(222.2, 47.4%, 11.2%)', foreground: 'hsl(210, 40%, 98%)' },
            secondary: { DEFAULT: 'hsl(210, 40%, 96.1%)', foreground: 'hsl(222.2, 47.4%, 11.2%)' },
            muted: { DEFAULT: 'hsl(210, 40%, 96.1%)', foreground: 'hsl(215.4, 16.3%, 46.9%)' },
            accent: { DEFAULT: 'hsl(210, 40%, 96.1%)', foreground: 'hsl(222.2, 47.4%, 11.2%)' },
            destructive: { DEFAULT: 'hsl(0, 84.2%, 60.2%)', foreground: 'hsl(210, 40%, 98%)' },
            border: 'hsl(214.3, 31.8%, 91.4%)',
            input: 'hsl(214.3, 31.8%, 91.4%)',
            ring: 'hsl(222.2, 84%, 4.9%)',
          },
          borderRadius: {
            lg: '0.5rem',
            md: 'calc(0.5rem - 2px)',
            sm: 'calc(0.5rem - 4px)',
          },
          fontFamily: {
            sans: ['Inter', 'system-ui', 'sans-serif'],
          }
        }
      }
    }
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Inter', system-ui, sans-serif; }
    .nav-active { background-color: hsl(210, 40%, 96.1%); color: hsl(222.2, 47.4%, 11.2%); font-weight: 500; }
    .nav-item:hover { background-color: hsl(210, 40%, 96.1%); }
    /* Mobile menu toggle */
    #mobile-menu-toggle:checked ~ .mobile-sidebar { display: block; }
    #mobile-menu-toggle:checked ~ .mobile-overlay { display: block; }
  </style>
</head>
<body class="bg-background text-foreground min-h-screen">

  <!-- Mobile menu checkbox (hidden) -->
  <input type="checkbox" id="mobile-menu-toggle" class="hidden">

  <!-- Mobile overlay -->
  <label for="mobile-menu-toggle" class="mobile-overlay hidden fixed inset-0 bg-black/50 z-40 md:hidden"></label>

  <!-- Mobile sidebar (slides in) -->
  <aside class="mobile-sidebar hidden fixed inset-y-0 left-0 w-64 bg-card border-r border-border z-50 overflow-y-auto md:hidden">
    {{SIDEBAR_CONTENT}}
  </aside>

  <div class="flex min-h-screen">
    <!-- Desktop sidebar -->
    <aside class="hidden md:flex md:w-64 md:flex-col md:border-r md:border-border bg-card">
      {{SIDEBAR_CONTENT}}
    </aside>

    <!-- Main content -->
    <main class="flex-1 overflow-auto">
      <!-- Mobile header -->
      <div class="md:hidden flex items-center gap-3 p-4 border-b border-border">
        <label for="mobile-menu-toggle" class="cursor-pointer p-1 rounded hover:bg-muted">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
        </label>
        <span class="font-semibold text-sm">{{PAGE_TITLE}}</span>
      </div>

      <!-- Page content -->
      <div class="p-6">
        {{PAGE_CONTENT}}
      </div>
    </main>
  </div>

  <!-- Journey tracker bar -->
  {{JOURNEY_TRACKER}}

</body>
</html>
```

---

## Sidebar Template

The sidebar shows the PROPOSED navigation structure (not current). Highlight the active page.

```html
<!-- Sidebar content (used for both desktop and mobile) -->
<div class="flex flex-col h-full">
  <!-- Logo area -->
  <div class="p-4 border-b border-border">
    <div class="flex items-center gap-2">
      <div class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
        <span class="text-primary-foreground font-bold text-sm">N</span>
      </div>
      <span class="font-semibold">Nicolify</span>
    </div>
  </div>

  <!-- Navigation groups -->
  <nav class="flex-1 p-3 space-y-6 overflow-y-auto">
    <!-- Group: [Studio Name] -->
    <div>
      <p class="px-2 mb-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">[Group Label]</p>
      <ul class="space-y-0.5">
        <li>
          <a href="{{RELATIVE_PATH}}" class="nav-item flex items-center gap-2 px-2 py-1.5 rounded-md text-sm {{ACTIVE_CLASS}}">
            {{ICON_SVG}}
            <span>[Entry Label]</span>
            <!-- Optional: NEW badge for newly surfaced routes -->
            <span class="ml-auto text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-primary text-primary-foreground">NEW</span>
          </a>
        </li>
      </ul>
    </div>

    <!-- Repeat for each group -->
  </nav>

  <!-- Footer -->
  <div class="p-3 border-t border-border">
    <p class="text-xs text-muted-foreground text-center">Flow Preview — Not real app</p>
  </div>
</div>
```

### Active Page Highlighting

Add `nav-active` class to the `<a>` element matching the current page. Remove it from all others. This provides visual feedback about where the user is in the navigation.

### NEW Badges

Routes that are newly surfaced (previously orphaned) should show a small "NEW" badge next to their label. This helps the user see what changed vs the current app.

---

## Dynamic Route Handling

Routes with parameters become static HTML files with representative mock data:

| Dynamic Route | Static File | Mock Data |
|---------------|-------------|-----------|
| `/offer-studio/offer/[id]` | `offer-studio/offer-detail.html` | "Programa de Coaching 1:1" |
| `/growth-studio/atraccion-captura/[channelSlug]` | `growth-studio/atraccion-instagram.html` | Instagram organic channel |
| `/brand-studio/publico/persona/[personaId]` | `brand-studio/persona-detail.html` | "María, Emprendedora Digital" |
| `/connections/[provider]` | `settings/connections-meta.html` | Meta connection config |

Each dynamic file includes a comment at the top of the `<body>`:

```html
<!-- Real route: /[tenantId]/offer-studio/offer/[id] -->
<!-- This is a static preview with mock data -->
```

---

## Journey Tracker Bar

A floating bar at the bottom showing which journey(s) pass through this page:

```html
<div class="fixed bottom-0 left-0 right-0 bg-blue-50 border-t border-blue-200 px-4 py-2 text-xs flex items-center justify-between z-30">
  <div class="flex items-center gap-4">
    <span class="font-semibold text-blue-700">Journey: {{JOURNEY_NAME}}</span>
    <span class="text-blue-600">Paso {{STEP_NUMBER}} de {{TOTAL_STEPS}}: {{STEP_DESCRIPTION}}</span>
  </div>
  <a href="{{NEXT_STEP_URL}}" class="text-blue-700 hover:text-blue-900 font-medium flex items-center gap-1">
    Siguiente: {{NEXT_STEP_NAME}} →
  </a>
</div>
```

If multiple journeys pass through the page, stack them or use a tabbed display:

```html
<div class="fixed bottom-0 left-0 right-0 z-30">
  <div class="bg-blue-50 border-t border-blue-200 px-4 py-1.5 text-xs">
    <strong class="text-blue-700">Onboarding:</strong> Paso 2/5 — Configurar marca
    <a href="..." class="ml-2 text-blue-600 hover:underline">→ Siguiente</a>
  </div>
  <div class="bg-green-50 border-t border-green-200 px-4 py-1.5 text-xs">
    <strong class="text-green-700">Daily Use:</strong> Paso 1/4 — Ver dashboard
    <a href="..." class="ml-2 text-green-600 hover:underline">→ Siguiente</a>
  </div>
</div>
```

---

## Page Content Patterns

Use these patterns for page content. Focus on structure, not pixel perfection.

### KPI Cards Row
```html
<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
  <div class="bg-card border border-border rounded-lg p-4">
    <p class="text-sm text-muted-foreground">Leads Captados</p>
    <p class="text-2xl font-bold">1,247</p>
    <p class="text-xs text-green-600">+12% vs mes anterior</p>
  </div>
  <!-- More cards -->
</div>
```

### Data Table
```html
<div class="bg-card border border-border rounded-lg">
  <div class="p-4 border-b border-border flex items-center justify-between">
    <h3 class="font-semibold">Ofertas Activas</h3>
    <button class="px-3 py-1.5 bg-primary text-primary-foreground text-sm rounded-md">+ Nueva Oferta</button>
  </div>
  <table class="w-full text-sm">
    <thead class="border-b border-border">
      <tr>
        <th class="text-left p-3 text-muted-foreground font-medium">Nombre</th>
        <th class="text-left p-3 text-muted-foreground font-medium">Estado</th>
        <th class="text-left p-3 text-muted-foreground font-medium">Conversiones</th>
      </tr>
    </thead>
    <tbody>
      <tr class="border-b border-border hover:bg-muted/50">
        <td class="p-3"><a href="offer-detail.html" class="text-primary hover:underline">Coaching 1:1</a></td>
        <td class="p-3"><span class="px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-xs">Activa</span></td>
        <td class="p-3">42</td>
      </tr>
    </tbody>
  </table>
</div>
```

### Empty State
```html
<div class="flex flex-col items-center justify-center py-16 text-center">
  <div class="w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
    <svg class="w-6 h-6 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
    </svg>
  </div>
  <h3 class="font-semibold mb-1">No hay campañas aún</h3>
  <p class="text-sm text-muted-foreground mb-4">Crea tu primera campaña para empezar a atraer leads</p>
  <button class="px-4 py-2 bg-primary text-primary-foreground text-sm rounded-md">Crear Campaña</button>
</div>
```

### Contextual CTA (cross-studio link)
```html
<!-- "What's next" card — used to bridge between studios -->
<div class="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center justify-between">
  <div>
    <p class="font-medium text-blue-900">Siguiente paso: Crea tu primera oferta</p>
    <p class="text-sm text-blue-700">Ya tienes tu marca configurada. Ahora define qué vendes.</p>
  </div>
  <a href="../offer-studio/index.html" class="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700">
    Ir a Offer Studio →
  </a>
</div>
```

---

## Serving

After generating all files:

```bash
# Kill any existing preview server
pkill -f "http.server 8888" 2>/dev/null || true

# Serve the prototype (SESSION = $(date +%Y-%m-%d)-{slug})
python3 -m http.server 8888 -d "docs/ux-sessions/$SESSION/prototype/" &

echo ""
echo "=========================================="
echo "  Flow Preview disponible en:"
echo "  http://localhost:8888"
echo "=========================================="
echo ""
echo "Abre en tu navegador y navega por el sidebar."
echo "Para detener: pkill -f 'http.server 8888'"
```

Tell the user to open `http://localhost:8888` in their browser.

---

## Scope Control

- **Full audit:** Generate all pages from the proposed sidebar structure
- **Studio-scoped:** Generate only pages for that studio + the sidebar (so they see context)
- **Journey-focused:** Generate only pages that appear in the selected journey
- **Micro-connection:** Generate only the 2-3 pages involved in the connection

Always generate the sidebar even in scoped mode — it provides navigation context.

---

## Anti-patterns

| Don't | Do |
|-------|-----|
| Use React, Vue, or any JS framework | Use plain HTML + Tailwind CDN |
| Try to replicate exact Shadcn components | Use visually similar HTML that conveys the same structure |
| Generate 50+ pages for a simple audit | Only generate pages relevant to approved changes |
| Polish visual details | Focus on navigation structure and clickable links |
| Use `file:///` URLs | Always serve via `python3 -m http.server` for clean relative paths |
| Hardcode absolute paths in links | Use relative paths (`../growth-studio/atraccion.html`) |
