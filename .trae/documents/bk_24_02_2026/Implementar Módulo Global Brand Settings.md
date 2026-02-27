# Implementación del Módulo "Sobre la Marca" (Global Brand Settings)

Este plan detalla los pasos para agregar el nuevo módulo de configuración de marca, incluyendo la estructura de datos en el backend y la interfaz de usuario en el frontend.

## 1. Backend: Modelado de Datos y API
Se utilizará el campo `config_json` de la entidad `Tenant` para almacenar estos datos, asegurando flexibilidad y persistencia sin migraciones complejas.

### 1.1 Esquemas Pydantic (`backend/src/core/domain/schema.py`)
Definiremos los modelos de datos para validar la estructura:
- `BrandIdentity`: Nombre, razón social, web, industria, logo, zona horaria, idioma.
- `KeyFigure` (Equipo): Nombre, rol, voz principal (bool), bio, género, estilo.
- `AuthorityItem` (Respaldo): Entidad, tipo, contexto, prueba (URL), logo.
- `ContactData`: Email, teléfono, dirección, redes sociales.
- `BrandSettings`: Modelo agregador.

### 1.2 Endpoints de API (`backend/src/api/routers/settings.py`)
Implementaremos nuevos endpoints para gestionar esta configuración:
- `GET /api/v1/settings/brand`: Recupera la configuración actual del tenant.
- `PATCH /api/v1/settings/brand`: Actualiza la configuración (merge con `config_json`).

## 2. Frontend: Interfaz de Usuario
Se creará una nueva sección en el dashboard con la estructura de pestañas solicitada.

### 2.1 Navegación (`frontend/src/components/layout/app-sidebar.tsx`)
- Agregar ítem "Sobre la Marca" entre "Resumen" y "Offer Studio".
- Icono propuesto: `Building2` o `BadgeCheck`.

### 2.2 Página Principal (`frontend/src/app/(dashboard)/brand-settings/page.tsx`)
- Layout principal con pestañas verticales (Tabs).
- Gestión de estado y carga de datos inicial.

### 2.3 Componentes de Formulario (`frontend/src/components/brand/*`)
- `brand-identity-form.tsx`: Formulario simple con validación Zod.
- `authority-squad-form.tsx`: 
  - Lista de Personas (Repeater): Permitir agregar/editar/eliminar miembros.
  - Lista de Autoridad (Repeater): Permitir agregar/editar/eliminar credenciales.
- `contact-data-form.tsx`: Campos de contacto y redes sociales.

### 2.4 Integración (`frontend/src/lib/api/brand.ts`)
- Funciones `getBrandSettings` y `updateBrandSettings` conectadas al backend.
