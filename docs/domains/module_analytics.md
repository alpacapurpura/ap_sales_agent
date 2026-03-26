---
module: Analytics
status: active
core_files: []
---

## 1. Propósito del Negocio (El "Por Qué")
- Extraer y consolidar la información de múltiples sistemas (publicidad externa, ventas internas, crm) para mostrar el estado global del negocio en un único vistazo (como un diagrama de Sankey o funnel). Permite al usuario tomar decisiones estratégicas basadas en métricas clave.

## 2. Reglas de Negocio Estrictas (Business Rules)
- Lectura Desacoplada (CQRS): Es un dominio primordialmente de lectura. No realiza joins infernales en tiempo real contra los otros módulos. Debe consumir Vistas Materializadas o tablas de agregación tipo Data Mart actualizadas de forma asíncrona.
- Inmutabilidad Relativa: No modifica datos de los otros módulos, únicamente los lee y los transforma en DTOs amigables para gráficos y visualización web.

## 3. Mapa de Código (Rutas relativas a Front y Back para este módulo)
- Backend: backend/src/modules/analytics/ (Contiene endpoints de reportes y workers/cron jobs para agregar data).
- Frontend: frontend/src/features/growth-studio/

## 4. Casos Borde Conocidos (Edge Cases)
- Inconsistencia de Datos Temporales (Lag): Si los cron jobs de agregación fallan silenciosamente, el usuario verá el funnel con los datos exactos pero del día anterior, causando confusión.
- Cuellos de Botella de Rendimiento: Si se intenta calcular la atribución o el funnel cruzando millones de filas de sales_agent y advertising cada vez que el usuario carga la página web, el sistema completo se colapsará.