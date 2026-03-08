# Reporte Completo de Entidades del Backend - Visionarias Brain

Este documento presenta un inventario exhaustivo de todas las entidades de datos del sistema, clasificadas por módulo funcional y tipo de persistencia.

**Convenciones:**
*   **SQLAlchemy (DB)**: Modelos que representan tablas en la base de datos PostgreSQL. Gestionan la persistencia.
*   **Pydantic (Dominio)**: Objetos de transferencia de datos (DTOs) y modelos de dominio utilizados en la lógica de negocio y API.

---

## 1. Módulo IAM (Identity & Access Management)
**Ubicación:** `backend/src/modules/iam`
Responsable de la autenticación, gestión de inquilinos (tenants) y control de acceso.

### Modelos de Base de Datos (SQLAlchemy)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `TenantModel` | `infrastructure/models/tenant.py` | Representa una organización o cliente del sistema (SaaS). Contiene configuración global y estado de suscripción. |
| `UserModel` | `infrastructure/models/user.py` | Identidad base del usuario. Almacena credenciales (hash), email y estado global. |
| `UserTenantModel` | `infrastructure/models/user_tenant.py` | Tabla de enlace (Muchos a Muchos) que asocia usuarios con tenants y define roles específicos por tenant. |

### Modelos de Dominio (Pydantic)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `User` | `domain/user.py` | Entidad de negocio rica del usuario, incluye métodos de validación y lógica de dominio. |
| `Tenant` | `domain/tenant.py` | Entidad de negocio del tenant, incluye validación de configuración. |
| `SystemUserProfile` | `domain/schemas.py` | Perfil completo del usuario para uso interno del sistema, agrupa datos de identidad y contexto. |
| `AISettings` | `domain/schemas.py` | Configuración de comportamiento de la IA a nivel de tenant (tono, restricciones). |
| `TenantSettingsUpdate` | `domain/schemas.py` | Esquema para validación de actualizaciones de configuración del tenant. |
| `GeneralSettings` | `domain/schemas.py` | Configuraciones generales no relacionadas con IA. |
| `TeamMemberCreate` | `domain/schemas.py` | Payload para invitar o crear nuevos miembros de equipo. |

---

## 2. Módulo Sales (Ventas & CRM)
**Ubicación:** `backend/src/modules/sales`
Gestiona el pipeline de ventas, prospectos y la inteligencia de conversión.

### Modelos de Base de Datos (SQLAlchemy)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `LeadModel` | `infrastructure/models/lead_model.py` | Persistencia del prospecto. Almacena estado en el embudo, score de cualificación y datos de contacto. |

### Modelos de Dominio (Pydantic)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `Lead` | `domain/lead.py` | Agregado raíz del dominio de ventas. Encapsula lógica de cambio de estado y validación de reglas de negocio. |
| `UserProfile` | `domain/schemas.py` | DTO con datos enriquecidos del perfil del lead (obtenidos de redes sociales o formularios). |

---

## 3. Módulo Communication (Canales y Mensajería)
**Ubicación:** `backend/src/modules/communication`
Orquesta la interacción con canales externos (WhatsApp, Telegram) y el sistema de citas.

### Modelos de Base de Datos (SQLAlchemy)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `ChannelConnection` | `domain/channel_connection.py` | Configuración y credenciales de conexión a un canal externo (token, webhook secret). *Nota: Definido en capa de dominio pero hereda de Base.* |
| `Appointment` | `infrastructure/models/appointment.py` | Registro de citas agendadas, sincronización con calendario y estado (confirmada, cancelada). |
| `Message` | `infrastructure/models/message.py` | Historial inmutable de mensajes para auditoría y contexto de IA. |
| `BookingLink` | `infrastructure/models/booking_link.py` | Enlaces persistentes configurables para que los leads agenden citas. |
| `ShareableLink` | `infrastructure/models/booking_link.py` | (Si existe) Variante de enlace público para compartir recursos. |

### Modelos de Dominio (Pydantic)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `IncomingMessage` | `domain/message_models.py` | Estructura normalizada de un mensaje entrante, independiente del canal (WhatsApp/Telegram). |
| `OutgoingMessage` | `domain/message_models.py` | Estructura unificada para enviar mensajes a cualquier canal. |
| `EventType` | `domain/event_type_schema.py` | Definición de tipos de reuniones (duración, precio, descripción). |
| `BookingConfig` | `domain/availability_schema.py` | Configuración global de disponibilidad y reglas de agendamiento. |
| `AvailabilitySchedule` | `domain/availability_schema.py` | Estructura compleja de horarios disponibles por día de la semana. |
| `TimeSlot` | `domain/availability_schema.py` | Bloque de tiempo específico disponible. |

---

## 4. Módulo Offer (Oferta Irresistible)
**Ubicación:** `backend/src/modules/offer`
Core del negocio: define qué se vende y cómo se presenta.

### Modelos de Base de Datos (SQLAlchemy)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `Product` | `infrastructure/models.py` | Entidad central del catálogo. Almacena precio, promesas, entregables y configuración de venta. |

### Modelos de Dominio (Pydantic)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `Offer` | `domain/schemas.py` | Modelo de alto nivel que representa la "Oferta Irresistible" completa (Psicología + Producto). |
| `OfferGalleryImage` | `domain/offer_gallery.py` | Entidad de dominio para manipulación lógica de imágenes de oferta. |
| `PricingStructure` | `domain/schemas.py` | Detalle de precios, planes de pago, moneda y descuentos. |
| `DeliverableItem` | `domain/schemas.py` | Elemento individual que compone la entrega del producto (e.g., "Sesión 1:1"). |
| `ProductDetails` | `domain/schemas.py` | Detalles técnicos específicos del producto. |
| `SessionDetails` | `domain/schemas.py` | Detalles específicos si el producto es una sesión/consultoría. |
| `ProgramDetails` | `domain/schemas.py` | Detalles específicos si es un programa/curso. |

---

## 5. Módulo Marketing (CDP & Motores)
**Ubicación:** `backend/src/modules/marketing`
Customer Data Platform y análisis de comportamiento.

### Modelos de Base de Datos (SQLAlchemy)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `CustomerProfile` | `infrastructure/models/customer.py` | Perfil unificado del cliente ("Golden Record") agregando datos de múltiples fuentes. |
| `CustomerIdentity` | `infrastructure/models/customer.py` | Identificadores del cliente en diferentes sistemas (email, teléfono, cookie_id). |
| `JourneyEvent` | `infrastructure/models/customer.py` | Registro de eventos significativos (click, compra, visita) para análisis de viaje. |

### Modelos de Dominio (Pydantic)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `RFMResponse` | `api/dto/cdp.py` | Resultado del análisis de Recencia, Frecuencia y Monetización. |
| `ProfileResponse` | `api/dto/cdp.py` | DTO de respuesta con el perfil completo del cliente. |
| `EventCreate` | `api/dto/cdp.py` | Payload para registrar un nuevo evento de marketing. |

---

## 6. Módulo Brand (Marca & Identidad)
**Ubicación:** `backend/src/modules/brand`
Gestión de la identidad corporativa y configuración de avatares.

### Modelos de Base de Datos (SQLAlchemy)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `Avatar` | `infrastructure/models/avatar.py` | Persistencia del avatar de IA (nombre, rol, personalidad). |

### Modelos de Dominio (Pydantic)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `BrandIdentity` | `domain/models.py` | Definición de la identidad visual (colores, logo) y verbal (tono de voz). |
| `BrandStrategy` | `domain/models.py` | Estrategia de mercado, público objetivo y propuesta de valor. |
| `BrandStory` | `domain/models.py` | Narrativa de la marca, historia del fundador y misión. |
| `BrandVisuals` | `domain/models.py` | Colección de activos visuales y guías de estilo. |
| `BrandTeam` | `domain/models.py` | Estructura del equipo y roles asociados a la marca. |
| `BrandSettings` | `domain/models.py` | Configuración operativa de la marca. |

---

## 7. Módulo Landing (Generador de Páginas)
**Ubicación:** `backend/src/modules/landing`
Estructuras para la generación dinámica de Landing Pages.

### Modelos de Dominio (Pydantic)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `LandingPageConfig` | `domain/landing_page/content_schemas.py` | Configuración maestra de una landing page (tema, estructura, secciones). |
| `LandingPageTheme` | `domain/landing_page/content_schemas.py` | Definición de estilos, paleta de colores y tipografía. |
| `SqueezeContent` | `domain/landing_page/content_schemas.py` | Esquema de contenido específico para páginas de captura (Squeeze). |
| `TransformerContent` | `domain/landing_page/content_schemas.py` | Esquema para páginas de transformación/venta. |
| `FlashOfferContent` | `domain/landing_page/content_schemas.py` | Esquema para ofertas flash de tiempo limitado. |
| `FeatureBullet` | `domain/landing_page/content_schemas.py` | Componente de lista de beneficios/características. |
| `Testimonial` | `domain/landing_page/content_schemas.py` | Componente de prueba social. |

---

## 8. Módulo Gallery (Gestión de Activos)
**Ubicación:** `backend/src/modules/gallery`
Almacenamiento y organización de imágenes y archivos.

### Modelos de Base de Datos (SQLAlchemy)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `GalleryImage` | `domain/entity.py` | Modelo base para imágenes generales con metadatos de IA. *Nota: Definido en capa de dominio pero hereda de Base.* |
| `OfferGalleryImageModel` | `infrastructure/models.py` | Imágenes asociadas específicamente a una oferta. |

### Modelos de Dominio (Pydantic)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `GalleryImageDto` | `domain/schemas.py` | DTO para listar imágenes en la interfaz de usuario. |

---

## 9. Shared & Infrastructure (Núcleo)
**Ubicación:** `backend/src/shared`
Entidades de soporte técnico transversal.

### Modelos de Base de Datos (SQLAlchemy)
| Entidad | Ubicación | Descripción |
| :--- | :--- | :--- |
| `AgentTrace` | `infrastructure/models.py` | Registro de ejecución de agentes (pasos, inputs, outputs) para depuración. |
| `LLMLog` | `infrastructure/models.py` | Auditoría de consumo de tokens y llamadas a APIs de LLM (OpenAI/Anthropic). |
| `PromptVersion` | `infrastructure/models.py` | Versionamiento de prompts del sistema. |
| `SensitiveData` | `infrastructure/models.py` | Almacen seguro para secretos encriptados. |
