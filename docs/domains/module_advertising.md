---
module: Advertising
status: active
core_files: []
---

## 1. Propósito del Negocio (El "Por Qué")
Tratar exclusivamente con pauta pagada (Meta Ads, Google Ads). Manejar la creación de campañas, creativos específicos para conversión y lectura del rendimiento financiero (CPL, ROAS).

## 2. Reglas de Negocio Estrictas (Business Rules)
- Métricas Batch: La lectura de métricas (AdMetrics) no se hace en Métricas Batch (Extracción y Propiedad de Datos): La lectura de métricas de rendimiento externo (Meta Ads, Google Ads) es responsabilidad exclusiva de este módulo. No se hace en tiempo real por cada visitante, sino mediante procesos programados (cron jobs asíncronos) para evitar colapsar las APIs. advertising extrae, estandariza y guarda esta data cruda en sus propias tablas (ej. AdMetricsDaily).
    * Contrato de Consumo para otros Módulos: Si el módulo analytics (para mostrar el funnel en el dashboard) o el módulo crm (para calcular el Costo de Adquisición de un cliente) necesitan datos de inversión publicitaria, tienen estrictamente prohibido conectarse a las APIs de Meta/Google. Su deber es consultar únicamente los servicios o tablas de lectura internas expuestas por este módulo advertising.
- Trazabilidad de Inversión: Cada campaña publicitaria genera un identificador que el módulo sales_agent o crm debe recibir para calcular el retorno de inversión real.

## 3. Mapa de Código (Rutas relativas a Front y Back para este módulo)
- Backend: backend/src/modules/advertising/
- Frontend: frontend/src/features/marketing-studio/
## 4. Casos Borde Conocidos (Edge Cases)
- Rechazo de Anuncios: Creación de creativos por IA que infrinjan silenciosamente políticas de Meta (ej. promesas excesivas de ingresos), resultando en cuentas baneadas.
- Sincronización de Gastos: Desfase horario (Timezone mismatch) entre la zona horaria de la cuenta publicitaria y el servidor backend local que distorsione los reportes diarios de gasto.