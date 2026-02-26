# Especificación Técnica: Transformación a Closer Studio

## 1. Visión General
Transformación del módulo "Sales Studio" a "Closer Studio", centrando la arquitectura en el cliente. El objetivo principal es eliminar la duplicidad de datos entre Ventas y Marketing, estableciendo `CustomerProfile` (Marketing) como la fuente única de verdad para la identidad del contacto, mientras que `LeadModel` (Sales) gestiona el contexto de la negociación y el estado del pipeline.

## 2. Arquitectura de Datos

### Modelo Actual (Problemático)
- **LeadModel (Sales):** Contiene `full_name`, `email`, `phone`, `telegram_id`, etc.
- **CustomerProfile (Marketing):** Contiene `full_name`, `primary_email`, `identities`.
- **Problema:** Desincronización. Si marketing actualiza un email, ventas no se entera. Duplicidad de almacenamiento.

### Nuevo Modelo (Target)

#### `CustomerProfile` (Marketing Module) - *Sin Cambios Estructurales Mayores*
Mantiene la identidad y datos demográficos.
- `id`: UUID
- `full_name`: String
- `primary_email`: String
- `primary_phone`: String
- `identities`: Relación 1:N con `CustomerIdentity` (Email, Phone, TelegramID, WhatsAppID).

#### `LeadModel` (Sales Module) - *Refactorizado*
Pasa a ser un "Contexto de Venta" asociado a un cliente.
- `id`: UUID
- `customer_id`: UUID (FK -> `customer_profiles.id`) **[NUEVO]**
- `tenant_id`: UUID
- `status`: Enum (Pipeline Stage)
- `temperature`: Enum (Cold, Warm, Hot)
- `fit_score`: Integer
- `key_objections_history`: JSONB
- `conversation_summary`: Text
- **Eliminados:** `full_name`, `email`, `phone`, `telegram_id`, `whatsapp_id`, `instagram_id`.

## 3. Estrategia de Migración (Backend)

### Fase 1: Schema Change
1. Añadir columna `customer_id` a la tabla `leads` (nullable inicialmente).
2. Crear índices para `customer_id`.

### Fase 2: Data Migration (Script)
Para cada registro en `leads`:
1. Buscar si existe un `CustomerProfile` con el mismo email/phone.
   - **Si existe:** Enlazar `leads.customer_id` = `customer_profiles.id`.
   - **Si no existe:** Crear nuevo `CustomerProfile` usando los datos del `Lead` y enlazar.
2. Mover `telegram_id`, `whatsapp_id`, etc. a la tabla `customer_identities`.

### Fase 3: Cleanup
1. Hacer `customer_id` no nullable.
2. Eliminar columnas obsoletas de `leads` (`full_name`, `email`, `phone`, etc.).

## 4. Frontend Architecture (Atomic & Mock-First)

### Componentes Clave
- **`CloserLayout`:** Wrapper principal del estudio.
- **`LeadKanban`:** Vista de pipeline.
- **`LeadCard`:** Tarjeta atómica. Muestra nombre/avatar (desde `Customer`) y estado/temperatura (desde `Lead`).
- **`CustomerSidebar`:** Panel lateral con detalles del cliente (reutilizable de Marketing).

### Interfaces TypeScript
```typescript
interface Customer {
  id: string;
  fullName: string;
  email: string;
  avatarUrl?: string;
  // ... marketing fields
}

interface Lead {
  id: string;
  customerId: string;
  customer: Customer; // Hydrated relation
  status: PipelineStage;
  temperature: 'COLD' | 'WARM' | 'HOT';
  // ... sales fields
}
```

## 5. Endpoints & API
- `GET /api/v1/sales/leads`: Debe hacer JOIN (o fetch eager) con `CustomerProfile` para devolver la data completa.
- `POST /api/v1/sales/leads`: Acepta datos de cliente. Crea/Busca `Customer` primero, luego crea `Lead`.
