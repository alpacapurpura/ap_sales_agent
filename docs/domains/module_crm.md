# Módulo CRM (Identidad & Relaciones) - Documentación para Agentes

> **CONTEXTO DEL AGENTE**: Este módulo es la FUENTE DE VERDAD para la identidad de las personas. Implementa un patrón **CDP (Customer Data Platform)**. Úsalo para resolver quién es un usuario (Identity Resolution), gestionar su ciclo de vida (Lifecycle) y centralizar su historial unificado.

## 1. Mapa de Código (The "Where")

> ⚠️ **Explorar el código directamente** — no confíes en inventarios de archivos.

- **Backend**: `backend/src/modules/crm/`
  - **Dominio (Entidades)**: `domain/customer.py` (Profile & Identity), `domain/lead.py` (Sales Context).
  - **Resolución de Identidad**: `application/services/identity_service.py` (Entry Point crítico).
  - **Infraestructura**: `infrastructure/repositories/` (CustomerRepo maneja la lógica de búsqueda compleja).
  - **API**: `api/cdp.py` (Endpoints de identificación), `api/leads.py`.

## 2. Arquitectura de Datos: Patrón CDP (The "Why")

El sistema separa **QUIÉN** es la persona de **CÓMO** la contactamos y **QUÉ** estamos vendiendo.

### Modelo de 3 Entidades
1. **CustomerProfile (WHO)**: La persona unificada ("Golden Record"). Sobrevive a múltiples ventas y canales.
   - *Responsabilidad*: Datos demográficos, scoring global (RFM), estado del ciclo de vida.
   - *Relación*: 1:N con Identities, 1:N con Leads.

2. **CustomerIdentity (HOW)**: Puntos de contacto resolubles.
   - *Ejemplos*: `(EMAIL, juan@gmail.com)`, `(TELEGRAM, 123456789)`, `(WHATSAPP, +54911...)`.
   - *Propósito*: Permite que "Juan en Telegram" y "Juan en Email" sean el mismo `CustomerProfile`.

3. **Lead (CONTEXT)**: Contexto de una oportunidad de venta específica.
   - *Responsabilidad*: Estado del funnel, temperatura, historial de objeciones de *esta* venta.
   - *Vida útil*: Efímero (dura lo que dura el intento de venta).

> **Regla de Oro**: Nunca dupliques datos demográficos en `Lead`. El `Lead` tiene `customer_id` -> usa el `CustomerProfile` para nombre, email, etc.

## 3. Lógica de Negocio Crítica

### Resolución de Identidad (Identity Resolution)
- **Entrada**: Un mensaje de un canal (ej: Telegram ID).
- **Proceso**: `IdentityService.get_or_create_customer()` busca una `CustomerIdentity` existente.
- **Resultado**: Devuelve el `CustomerProfile` único. Si no existe, crea Profile + Identity atómicamente.

### Ciclo de Vida Automático
- **Conversión vs Expansión**: `SaleService` detecta automáticamente si es la primera venta (`CONVERSION`) o una recurrente (`EXPANSION`) basándose en el historial.
- **Soft Deletes**:
  - `CustomerProfile`: `lifecycle_stage = CHURNED` (nunca borrar, histórico es valioso).
  - `Lead`: `is_blacklisted` para bloqueos, `deleted_at` para borrado lógico.

### Aislamiento Multi-tenant
- **Estricto**: `tenant_id` (UUID) es obligatorio en TODAS las consultas.
- **Riesgo**: La resolución de identidad por email/teléfono DEBE filtrar por `tenant_id`. Un mismo email puede existir en dos tenants diferentes como personas distintas.

## 4. Integración entre Módulos

- **Sales Agent -> CRM**: El agente *siempre* opera sobre un `Lead`. Al iniciar chat, llama a `IdentityService` para obtener/crear el `CustomerProfile` y luego genera/recupera el `Lead` activo.
- **Analytics -> CRM**: Lee `CustomerProfile` para métricas de LTV y Cohortes.
- **Channels (Webhook) -> CRM**: Provee los identificadores crudos (telegram_id, phone) para que CRM resuelva la identidad.

## 5. Casos Borde y Gotchas (Edge Cases)

- **Falsos Positivos de Fusión**: Si dos personas comparten un teléfono (ej: línea fija o error de input), se fusionarán en un solo perfil. *Mitigación*: Validar propiedad del canal si es posible.
- **Race Conditions en Creación**: Si dos mensajes llegan en paralelo del mismo usuario nuevo, podrían crearse dos perfiles. *Solución*: `IdentityService` debe manejar transacciones o bloqueos optimistas (actualmente depende de DB constraints).
- **N+1 en Historial**: Cargar un `CustomerProfile` con todos sus `Leads` y `Sales` puede ser pesado. Usar `joinedload` con cuidado en SQLAlchemy.

## 6. Snippets para Agentes

### Resolver Identidad desde un Canal (Python)
```python
# En un servicio de entrada de mensajes (ej: Telegram Handler)
from src.modules.crm.application.services.identity_service import IdentityService
from src.modules.crm.domain.enums import IdentityType

async def handle_incoming_message(tenant_id: UUID, telegram_user_id: str, user_name: str):
    # 1. Resolver quién es (Busca o Crea)
    customer = await identity_service.get_or_create_customer(
        tenant_id=tenant_id,
        identity_type=IdentityType.TELEGRAM,
        identity_value=str(telegram_user_id),
        profile_data={"full_name": user_name} # Solo se usa si se crea nuevo
    )
    
    # 2. Ahora tenemos el ID unificado para buscar leads, ventas, etc.
    print(f"Cliente identificado: {customer.id}")
```
