# Módulo de Ofertas (Offer Studio) - Documentación para Agentes

> **CONTEXTO DEL AGENTE**: Este documento es la FUENTE DE VERDAD para entender cómo se estructuran los productos y servicios en el sistema. Úsalo para razonar sobre "tipos de oferta", "precios", "entregables" y la lógica polimórfica que permite vender desde Ebooks hasta Consultorías High-Ticket.

## 1. Mapa de Código (The "Where")

> ⚠️ **Explorar el código directamente** — no confíes en inventarios de archivos que pueden estar desactualizados.

- **Backend**: `backend/src/modules/offer/`
  - Capa de dominio: `domain/` (entidad `Offer`, polimorfismo de detalles)
  - Capa de infraestructura: `infrastructure/models/` y `infrastructure/repositories/`
  - API: `api/`
- **Frontend**: `frontend/src/features/offer-studio/`
  - Estado y hooks: `hooks/`
  - Tipos y validación Zod: `types/`
  - Componentes del editor: `components/`

## 2. Lógica de Negocio (The "Why" & "How")

### Polimorfismo Híbrido (Core Architecture)
El sistema debe soportar estructuras de datos radicalmente distintas (un curso tiene "módulos", un servicio tiene "sesiones", un producto físico tiene "envío").
- **Solución**: Usamos un patrón de **Discriminador + JSONB**.
  - **Discriminador**: Columna `type` (Enum: `course`, `service`, `product`, etc.).
  - **Payload**: Columna `specific_details` (JSONB) en la tabla `products`.
- **Funcionamiento**: Al leer de la DB, el `OfferRepository` mira el `type` y usa `OFFER_TYPE_TO_DETAILS_MAPPING` para instanciar la subclase correcta de Pydantic (ej. `ProgramDetails`) dentro del campo `specific_details` de la entidad `Offer`.

### Dualidad Offer vs Product
- **Dominio**: Hablamos de **Offer** (la propuesta de valor completa, incluyendo bonus, garantías y precios).
- **Infraestructura**: La tabla se llama **products** por razones históricas.
- **Regla**: En código de negocio (Python), usa siempre `Offer`. Si tocas SQL o migraciones, busca la tabla `products`.

### Precios y Entregables (Complex JSONs)
- **Pricing**: No es un simple valor escalar. Es una lista de objetos `PricingModel` (Pago único, 3 cuotas, Suscripción) almacenada en una columna JSONB `pricing`. Esto permite ofertas con múltiples opciones de pago.
- **Deliverables**: Lista de objetos que componen la oferta ("Entregables"), también en JSONB. Esto permite que una oferta tenga 1 o 50 componentes sin necesidad de tablas relacionales extra (`offer_deliverables`).

## 3. Casos Borde y Gotchas (Edge Cases)

- **Mutación de Ofertas Activas**: Si editas el precio o la promesa de una oferta que un Agente de Ventas está ofreciendo activamente en una conversación, puedes causar inconsistencias graves (el bot ofrece $300, el link de pago cobra $500).
  - *Recomendación*: Para cambios drásticos, archivar la oferta y crear una versión v2.
- **Validación en Runtime**: Al usar JSONB, la base de datos NO valida la estructura interna. Pydantic es la única barrera de defensa. Si inyectas datos corruptos en `specific_details` vía SQL directo, la API fallará con `ValidationError` al intentar leer.
- **Contexto RAG**: Los `deliverables` y `pain_points` se inyectan en el prompt del sistema del vendedor. Si hay demasiados elementos (>20), pueden saturar la ventana de contexto del LLM o diluir la atención del modelo.

## 4. Snippets para Agentes (Common Tasks)

### Cómo instanciar una Oferta Polimórfica (Backend Pattern)
```python
# ⚠️ Verificar nombres exactos de clases/métodos en el código real antes de usar
# offer_repository.py pattern
from backend.src.modules.offer.domain.offer import Offer, OFFER_TYPE_TO_DETAILS_MAPPING

def map_model_to_entity(model: ProductModel) -> Offer:
    # 1. Detectar tipo para elegir la clase de detalles correcta
    details_cls = OFFER_TYPE_TO_DETAILS_MAPPING.get(model.type)
    
    # 2. Parsear JSON específico usando Pydantic
    specific_details = details_cls(**model.specific_details) if model.specific_details else None
    
    # 3. Construir entidad completa
    return Offer(
        id=model.id,
        type=model.type,
        specific_details=specific_details,
        pricing=[PricingModel(**p) for p in model.pricing], # Lista de precios
        ...
    )
```

### Cómo renderizar condicionalmente en Frontend
```typescript
// ⚠️ Verificar nombres exactos de componentes/hooks en el código real antes de usar
// offer-editor.tsx pattern
const { offer } = useOffer();

return (
  <div className="space-y-4">
    <GeneralInfo offer={offer} />
    
    {/* Renderizado condicional según el discriminador de tipo */}
    {offer.type === 'course' && (
        <CurriculumEditor details={offer.specific_details as ProgramDetails} />
    )}
    {offer.type === 'service' && (
        <ServiceScheduleEditor details={offer.specific_details as ServiceDetails} />
    )}
  </div>
);
```
