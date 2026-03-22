# Documento de Vision de Producto: Nicolify (MVP)

## Vision del Producto

Nicolify es una plataforma SaaS con arquitectura multitenant y modelo AaaS (Agent as a Service). Su objetivo es automatizar el ciclo de vida completo de marketing y ventas (captacion, calificacion, cierre y fidelizacion) para emprendedores y pequenos negocios mediante Agentes de IA, para lograr liberarlos de tiempo y estres gestionando la operacion comercial como todo un equipo de Marketing y Ventas Ad-hoc a precio de un pasante.

## Mercado Objetivo

- Target: Creadores de contenido, Infoproductores, "Negocios de Experto". Servicios digitales y profesionales.
- Dolor principal: Falta de tiempo y conocimientos tecnicos para gestionar el embudo de marketing y ventas, integrar multiples herramientas y escalar la atencion al cliente.

## Consideraciones de Arquitectura (High-Level)

- Asumimos que el usuario es bueno en su negocio, pero no tiene por que conocer de todo el mundo de marketing y ventas, pero como necesitamos mucha informacion suya para tener una arquitectura de marca y oferta de servicios unica, hacemos que el camino sea muy sencillo a traves de la ayuda de la IA.
- SaaS Multitenant (aislamiento de datos por cliente).
- Dashboard web para el dueno de negocio, que le permite editar cualquier al minimo detalle cualquier componente de su negocio de forma manual.
- Botones de ayuda IA y carga de informacion para el proceso de autocompletado de formularios (Brand, Offer) con IA.
- Data Vis: Renderizado de graficos complejos (Sankey diagrams) con data extraida de las conexiones.
- Agente IA conversacional para el negocio: Lo llamamos "Copilot"
- Agente IA conversacional para leads y customers que actua como representante de la empresa en Soporte, Atencion, Marketing y Ventas (SDR and Online Sales).

## Desglose de Epicas (Funcionalidades Core)

### Modulo Brand Studio
Motor de Estrategia de Marca. Flujo de formularios dinamicos e inteligentes que capturan la identidad de la marca del usuario. Incluye funcionalidades como el scraping web (si el cliente tiene un website) donde obtenemos toda la informacion de la marca para evitar duplicar esfuerzos. Tambien tiene la opcion de cargar cualquier informacion que posea de su negocio. Se revisa todo y se hace una ingenieria inversa para crear una arquitectura de marca potente.

### Modulo Offer Studio
Offer Ladder Builder. Herramienta visual para estructurar la escalera de valor (servicios gratuitos, low-ticket, high-ticket). Dependiendo del tipo de Negocio se muestra un Offer Ladder u Otro. Le permite ver de un solo vistazo si esta tomando todos los posibles espacios de dolor de los distintos tipos de cliente que puede tener su negocio.

Para cada Offer individual, se tiene un Blueprint de Producto diferente, el cual es un conjunto de formularios con un asistente guiado para estructurar un producto o servicio especifico con toda la informacion del mismo.

### Generacion Automatica de Activos (Asset Generation)
Desde el Offer Studio y el Brand Studio:
- **Landing Pages**: Generacion automatica de paginas de aterrizaje basadas en la informacion del Blueprint (requiere plantillas dinamicas). Acceso desde el offer individual.
- **Material Promocional**: Generacion de copies (para contenido en redes, publicidad e ideas de videos) y assets (Flyers, Imagenes, Brochures) sugeridos para redes sociales. Acceso desde el Offer Individual y el Brand Studio.

### Modulo Growth Studio
Visualizacion end-to-end del desempeno actual del Marketing y las Ventas del negocio a traves de un Diagrama Interactivo: Visualizacion end-to-end del embudo basado en el modelo Bowtie (Vistas -> Leads -> Clientes -> Reventas).

- **Action Triggers**: Capacidad de hacer clic en cualquier nodo del diagrama y desplegar un "right slider" para "tomar accion" (ej. crear una campana nueva, ajustar un copy) e inyectar esos cambios directamente en las fuentes (Ads, correos).

### Modulo Sales Studio
Hub operativo donde el dueno de negocio monitorea y opera todas sus ventas como si tuviera su propio equipo comercial.

### Sales Agent (AI SDR)
Agente IA autonomo que actua como representante comercial del negocio. Alimentado por Brand Studio y Offer Studio, conversa con leads, pre-califica, maneja objeciones, agenda citas, envia links de pago, da seguimiento y envia informacion ad-hoc a cada cliente para aportarle valor. Es el mejor setter (SDR), consultor comercial y vendedor que un negocio puede contratar: inteligente, perspicaz y proactivo.

- **Modulo de Agendamiento Automatico**: Sistema interno integrado con Google Calendar, que permite al Sales Agent asignar reuniones basadas en la disponibilidad del usuario. Tambien cuenta con una landing page a medida con la disponibilidad del "vendedor" (clon de Calendly) de forma que el mismo lead separe su cita.

### Modulo de Configuracion (Ecosistema)
Para que todo funcione, el sistema debe conectarse con distintos sistemas externos. En este modulo el usuario conecta (APIs/Webhooks) sus Redes, Sistemas, etc.:
- Meta Business Suite, Instagram, TikTok, Facebook
- Manychat, Telegram
- Shopify, Mercado Pago, Payoneer, PayPal
- Google Calendar, Gmail, Mailerlite
