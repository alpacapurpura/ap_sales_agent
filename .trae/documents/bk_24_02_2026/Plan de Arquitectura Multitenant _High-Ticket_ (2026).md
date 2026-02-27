# Plan de Refactorización Multitenant: "High-Ticket Isolation Architecture"

Este plan transforma tu sistema actual en una arquitectura **Multitenant Jerárquica** (SaaS B2B), diseñada para clientes "High Ticket" que requieren personalización profunda (Prompts y Datos aislados) sobre un núcleo compartido.

## 🏛️ Filosofía Arquitectónica (Best Practices 2026)
Para sistemas de Agentes IA en 2026, la tendencia no es crear bases de datos separadas (demasiado costo operativo), sino una **Aislamiento Lógico Estricto con Contexto Dinámico**:
1.  **Row-Level Security (RLS) Lógico**: Todos comparten tablas, pero una columna `tenant_id` es obligatoria y se inyecta automáticamente.
2.  **Hierarchical Configuration (Configuración en Cascada)**:
    *   *Nivel Sistema*: Prompts base y reglas globales.
    *   *Nivel Tenant*: Sobreescritura de prompts y configuración específica.
3.  **Vector Partitioning**: Qdrant usa un solo cluster, pero cada vector lleva `tenant_id` en el payload para filtrado duro.

---

## 🛠️ Fase 1: Núcleo de Datos y Modelado (Backend)
Modificaremos el esquema para soportar múltiples inquilinos sin romper la estructura actual.

### 1.1 Nuevo Modelo `Tenant`
Crearemos la entidad "Organización" o "Cliente".
- **Tabla**: `tenants`
- **Campos**: `id`, `name`, `slug` (para subdominios), `config_json` (variables globales: `company_name`, `voice_tone`), `is_active`.

### 1.2 Vinculación de Usuario
- **Tabla `users`**: Agregar `tenant_id` (ForeignKey).
- **Lógica**: Un usuario pertenece a UN solo tenant (modelo simple) o a MÚLTIPLES (modelo complejo). *Recomendación*: Empezar con **1 Usuario = 1 Tenant** para simplicidad, gestionado por ti desde el Super Admin.

### 1.3 Aislamiento de Datos (Migración Masiva)
Agregar columna `tenant_id` (UUID, Non-Nullable) a todas las tablas críticas:
- **Negocio**: `products`, `enrollments`, `avatar_definitions`, `marketing_assets`, `documents`, `objections`, `sensitive_data`.
- **Observabilidad**: `messages`, `agent_traces`, `llm_call_logs`, `prompt_versions`.
- **Acción**: Script de migración (Alembic) que asigne el `tenant_id` del cliente "Visionarias" a todos los datos existentes por defecto.

---

## 🔒 Fase 2: Seguridad y Contexto (Middleware)
El sistema debe saber "quién llama" antes de ejecutar cualquier lógica.

### 2.1 Middleware de Contexto (`TenantContextMiddleware`)
Intercepta cada request HTTP:
1.  **Resolución**: Identifica el Tenant basado en el Usuario autenticado (JWT de Clerk -> User DB -> Tenant ID).
2.  **Inyección**: Guarda el `tenant_id` en una variable de contexto global (ej. `contextvar`) para que los servicios lo consuman sin pasarlo como argumento en cada función.
3.  **Seguridad**: Si un usuario intenta acceder a un recurso de otro tenant, lanza `403 Forbidden` automáticamente.

### 2.2 Refactor de Servicios (Repository Pattern)
Actualizar `BaseRepository` para que **automáticamente** agregue `.filter(tenant_id=ctx.tenant_id)` a todas las queries (`get`, `list`, `create`). Esto evita fugas de datos por error humano.

---

## 🧠 Fase 3: Sistema de Prompts Dinámicos (Meta-Prompting)
Transformar los `.j2` estáticos en un sistema vivo gestionado por base de datos.

### 3.1 Migración a DB (`PromptVersion`)
- Moveremos físicamente los archivos `.j2` actuales a la tabla `prompt_versions` asignados al tenant "System" (o Visionarias como base).
- **Estrategia de Fallback**:
    1. El Agente pide el prompt `sales_system`.
    2. El sistema busca en DB: `SELECT * FROM prompt_versions WHERE key='sales_system' AND tenant_id='CLIENTE_ACTUAL'`.
    3. Si no existe, busca: `WHERE key='sales_system' AND tenant_id='SYSTEM_DEFAULT'`.
    4. Esto permite que Visionarias tenga su prompt único, y el Cliente B use el genérico hasta que se lo personalices.

### 3.2 Variables Dinámicas (Jinja2)
Reemplazar texto duro en los prompts:
- *Antes*: "Soy el asistente de Visionarias..."
- *Después*: "Soy el asistente de {{ company_name }}..."
- Estas variables se llenan desde `Tenant.config_json` en tiempo de ejecución.

---

## 🤖 Fase 4: Vector Store (RAG Multitenant)
- **Ingesta**: Al subir un PDF, se guarda en Qdrant con metadata `{"tenant_id": "xyz"}`.
- **Búsqueda**: El `Retriever` inyecta automáticamente un filtro Qdrant:
  ```python
  models.Filter(must=[models.FieldCondition(key="tenant_id", match=models.MatchValue(value=current_tenant_id))])
  ```
- Esto garantiza que un cliente NUNCA recupere documentos de otro.

---

## 👨‍💻 Fase 5: Admin Panel & Dashboard
### 5.1 Super Admin (Tu Vista)
- Nueva página "Tenants": Crear/Editar clientes.
- Botón "Impersonate": "Ver como Visionarias" o "Ver como Cliente B". Esto cambia tu contexto global y te permite usar el Admin Panel existente como si fueras ellos.

### 5.2 Cliente Admin (Futuro)
- Vista restringida donde solo ven sus `Enrollments` y `Metrics`.

---

## 📅 Pasos de Ejecución
1.  **Schema Migration**: Crear tablas y columnas. (Prioridad Alta)
2.  **Context Engine**: Implementar Middleware y `contextvar`.
3.  **Prompt Refactor**: Cargar prompts en DB y parametrizar.
4.  **Admin Update**: Habilitar gestión de Tenants.
