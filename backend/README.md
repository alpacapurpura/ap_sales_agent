# Visionarias Brain - Backend

Backend modular (Modular Monolith) construido con FastAPI y PostgreSQL.

## 🏗️ Arquitectura de Módulos

El sistema está dividido en módulos de dominio (Bounded Contexts) aislados.
Cada módulo es responsable de un área específica del negocio.

### Mapa de Responsabilidades

| Módulo | Responsabilidad Principal | Notas |
| :--- | :--- | :--- |
| **`connections`** | **Conexiones y Canales Externos**. Gestiona integraciones con WhatsApp, Telegram, Gmail y Webhooks. | |
| **`scheduling`** | **Agenda y Disponibilidad**. Gestión de Calendarios, Citas, Links Públicos y Event Types. | |
| **`sales_agent`** | **Agente de Ventas**. Lógica conversacional, orquestación de mensajes y manejo de Leads. | |
| **`landing`** | **Generador de Landing Pages**. Lógica para crear y desplegar páginas de venta y captación. | |
| **`offer`** | **Catálogo de Ofertas**. Gestión de productos, precios, galerías y la IA generadora de ofertas. | |
| **`marketing`** | **CDP y Audiencias**. Segmentación de clientes, scoring (RFM) y campañas. | |
| **`iam`** | **Identidad y Acceso**. Gestión de Usuarios, Tenants (Multitenancy), Roles y Permisos. | |
| **`onboarding`** | **Agente de Onboarding**. Flujos de bienvenida y configuración inicial para nuevos clientes. | |

## 🚀 Desarrollo

### Estructura
```
src/
├── modules/          # Dominios de negocio (ver tabla arriba)
│   ├── connections/
│   ├── scheduling/
│   ├── sales_agent/
│   └── ...
├── shared/           # Código compartido (Kernel)
│   ├── core/         # Configuración y utilidades base
│   └── infrastructure/ # DB, Logging, etc.
└── main.py           # Punto de entrada (App FastAPI)
```
