# Dashboard Feature Module

Este módulo implementa el "Centro de Comando" de Visionarias AI, siguiendo una arquitectura de componentes aislados y servicios tipados.

## Estructura

```
dashboard/
├── components/          # Widgets UI aislados
│   ├── AgendaWidget.tsx
│   ├── DashboardLayout.tsx  # Contenedor principal (Bento Grid)
│   ├── FunnelChart.tsx
│   ├── MetricCard.tsx
│   └── WarRoomWidget.tsx    # Lista de acciones críticas
├── hooks/
│   └── use-dashboard.ts     # React Query Hook
├── types.ts                 # Interfaces (Espejo de Backend DTOs)
└── README.md
```

## Arquitectura

### 1. Data Layer (Frontend)
Utilizamos `useDashboardSummary` (basado en React Query) para obtener todos los datos en una sola llamada (`GET /api/v1/dashboard/summary`).
Esto reduce la latencia y asegura consistencia entre widgets.

### 2. Componentes (UI)
Cada widget es "tonto" (presentacional) y recibe datos vía props. Si los datos no están disponibles, muestran un estado de carga o vacío, pero nunca rompen la página.
- **WarRoomWidget**: Muestra `ActionItems` (tareas críticas).
- **MetricCard**: KPIs simples.
- **DashboardLayout**: Maneja el layout responsivo.

### 3. Backend (API)
El endpoint devuelve un objeto `DashboardResponse` compuesto por DTOs estrictos (`DashboardMetrics`, `ActionItem`).
La lógica de negocio reside en `DashboardService`, que agrega datos de múltiples repositorios (`Lead`, `Appointment`, `JourneyProgress`).

## Extensión
Para agregar un nuevo widget:
1. Definir el dato en `DashboardResponse` (Backend & Frontend Types).
2. Crear el componente en `components/`.
3. Agregarlo a `DashboardLayout.tsx`.
