# Business Domain Documentation Index

**IMPORTANT FOR AI AGENTS:**
Before implementing or modifying any feature, you MUST read the relevant domain documentation file listed below. This ensures you understand the business context, rules, and edge cases.

## Domain Map

| Domain | Description (Propósito del Negocio) | Documentation File |
| :--- | :--- | :--- |
| **Brand** | Centraliza la identidad corporativa (misión, visión, tono de voz). Fuente de verdad para contenido alineado. | [module_brand.md](./module_brand.md) |
| **Offer** | Diseña y gestiona "Ofertas Irresistibles", precios y promesas. Fuente de verdad para funnels. | [module_offer.md](./module_offer.md) |
| **Landing** | Transforma ofertas en páginas de aterrizaje de alta conversión sin código. | [module_landing.md](./module_landing.md) |
| **Sales Agent** | Gestiona conversaciones de venta multi-canal, tácticas y cierre de ventas/citas. | [module_sales_agent.md](./module_sales_agent.md) |
| **Copilot** | Asistente flotante para configuración del sistema y llenado de formularios mediante IA. | [module_copilot.md](./module_copilot.md) |
| **CRM** | Administra relaciones a largo plazo (LTV), retención y upselling. | [module_crm.md](./module_crm.md) |
| **Scheduling** | Motor de gestión de tiempos, disponibilidad y reserva de citas. | [module_scheduling.md](./module_scheduling.md) |
| **Advertising** | Gestión de pauta pagada (Ads) y rendimiento financiero (ROAS/CPL). | [module_advertising.md](./module_advertising.md) |
| **Social Media** | Gestión de presencia orgánica, contenido y moderación en redes sociales. | [module_social_media.md](./module_social_media.md) |
| **Analytics** | Consolida métricas estratégicas y visualización de funnels de múltiples sistemas. | [module_analytics.md](./module_analytics.md) |
| **IAM** | Núcleo de seguridad, identidad de usuarios, tenants y aislamiento de datos. | [module_iam.md](./module_iam.md) |
| **Connections** | Bóveda de credenciales y gateway de comunicaciones (WhatsApp, Meta, etc.). | [module_connections.md](./module_connections.md) |
| **Assets** | Gestión centralizada de archivos estáticos con seguridad. | [module_assets.md](./module_assets.md) |
| **Core (Tech)** | Infraestructura técnica base (DB, logs) agnóstica al negocio. | [tech_module_core.md](./tech_module_core.md) |
| **Shared (Tech)** | Entidades base y utilidades comunes transversales. | [tech_module_shared.md](./tech_module_shared.md) |

## How to Use
1. Identify the domain related to your task.
2. Read the "Propósito del Negocio" and "Reglas de Negocio Estrictas" in the linked file.
3. Check "Casos Borde Conocidos" to avoid regressions.
4. Si tu tarea requiere de información de otro módulo, o de entidades comunes o de infraestructura técnica base, consulta el "Propósito del Negocio" del módulo que intuyas para que puedas profundizar y reutilizar y/o modificar donde corresponda realmente (No duplicar código).
5. Si intuyes que una acción pudo hacerse similar en otro módulo, consulta su documentación para ver si puedes reutilizar la lógica y/o codigo.
6. Update the documentation if your changes introduce new rules or modify existing ones.
