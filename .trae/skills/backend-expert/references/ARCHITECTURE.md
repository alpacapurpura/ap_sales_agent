# Arquitectura Backend: Monolito Modular (DDD)

El proyecto Visionarias Brain sigue una arquitectura de **Monolito Modular** estrictamente alineada con los principios de **Domain-Driven Design (DDD)** y **Clean Architecture**.

El objetivo es mantener la agilidad de un monolito (despliegue único, base de código unificada) pero con la separación de responsabilidades y escalabilidad lógica de los microservicios.

## 🏗️ Estructura de Directorios

La raíz del código fuente es `backend/src/`.

### 1. Módulos de Negocio (`src/modules/`)
Cada carpeta dentro de `modules` representa un **Bounded Context** (Contexto Delimitado) autónomo.
**Lista de Módulos:**
- `iam`: Identidad y Gestión de Accesos y Autenticación  (Usuarios, Tenants, Auth).
- `sales`: Gestión de Ventas, CRM y Pipelines.
- `communication`: Orquestación de mensajería (WhatsApp, Telegram, Email).
- `offer`: Gestión del catálogo de productos y servicios.
- `marketing`: CDP, Segmentación y Gestión de Campañas.
- `brand`: Configuración de marca y personalización por tenant.
- `landing`: Generador de landing pages.
- `gallery`: Gestión de activos digitales (imágenes, archivos, audios, etc.).
- `integration`: Conectores con herramientas externas (Whatsapp, ManyChat, Google Calendar, etc.).
- `onboarding`: Flujos de bienvenida y configuración inicial.

#### Estructura Interna de un Módulo
Cada módulo DEBE seguir esta estructura de capas:

```text
src/modules/{nombre_modulo}/
├── api/                  # CAPA DE INTERFAZ (Transporte)
│   ├── routers.py        # Endpoints FastAPI
│   └── dtos.py           # Esquemas de Entrada/Salida (Pydantic)
│
├── application/          # CAPA DE APLICACIÓN (Casos de Uso)
│   ├── services/         # Lógica de negocio y orquestación
│   └── event_handlers/   # Manejadores de eventos de dominio
│
├── domain/               # CAPA DE DOMINIO (Reglas de Negocio Puras)
│   ├── entities.py       # Modelos de Dominio (Pydantic, NO ORM)
│   ├── events.py         # Definición de Eventos de Dominio
│   ├── exceptions.py     # Excepciones específicas del dominio
│   └── interfaces.py     # Interfaces (Protocolos) para repositorios/servicios
│
└── infrastructure/       # CAPA DE INFRAESTRUCTURA (Implementación Técnica)
    ├── models/           # Modelos de Base de Datos (SQLAlchemy)
    ├── repositories/     # Implementación de Repositorios (SQLAlchemy)
    └── external/         # Clientes HTTP, Adaptadores de servicios externos
```

### 2. Núcleo Compartido (`src/shared/`)
Código reutilizable que NO pertenece a ningún dominio específico.
- `application/`: Utilidades de aplicación generales.
- `core/`: Configuración global, Logging (`structlog`), Excepciones base.
- `domain/`: Tipos básicos, Interfaces genéricas.
- `infrastructure/`: Configuración de DB (`session.py`), Cliente HTTP base, Seguridad.
- `utils/`: Herramientas auxiliares (fechas, hashing).

---

## 🔄 Flujo de Datos (Request-Response)

1.  **Request**: Llega a `api/routers.py`. Se valida con DTOs.
2.  **Delegación**: El router llama al Servicio de Aplicación (`application/services/`).
3.  **Orquestación**: El servicio aplica reglas de negocio.
    -   Si necesita datos, llama al Repositorio (inyectado como interfaz).
    -   Si necesita IA, llama al Agente o Servicio de IA.
4.  **Persistencia**: El Repositorio (`infrastructure/repositories/`) traduce la entidad de Dominio a Modelo ORM y ejecuta la query.
5.  **Retorno**: Los datos fluyen de vuelta hacia arriba, siempre convertidos a Entidades de Dominio o DTOs antes de salir de la capa correspondiente.

## 🛑 Reglas de Arquitectura

1.  **Regla de Dependencia**: Las capas internas (Dominio) NO deben conocer a las externas (Infraestructura, API).
    -   *Correcto*: `Infrastructure` importa `Domain`.
    -   *Incorrecto*: `Domain` importa `SQLAlchemy`.
2.  **Aislamiento de Módulos**:
    -   Un módulo NO puede importar directamente código de otro módulo (excepto interfaces públicas o DTOs compartidos, aunque se prefiere evitar).
    -   La comunicación entre módulos debe ser vía **Eventos** (Asíncrono) o llamadas a **Servicios Públicos** explícitos.
    -   **NUNCA** hacer JOINS entre tablas de diferentes módulos.
3.  **State Management (IA)**:
    -   El estado de los agentes (LangGraph) se gestiona como parte de la infraestructura de IA, pero las definiciones de estado pueden vivir en `application` o `domain` según su complejidad.
