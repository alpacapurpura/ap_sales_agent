# Plan de Implementación: Arquitectura de Canales Agnóstica (Multi-Channel Support)

Para cumplir con tu requerimiento de soportar Telegram hoy, ManyChat mañana y cualquier otra interfaz en el futuro, implementaremos el patrón de diseño **Ports and Adapters (Arquitectura Hexagonal)** en la capa de entrada/salida.

## 1. Patrón de Diseño Seleccionado: "Channel Adapter Pattern"

En lugar de atar tu lógica a una API específica (como hicimos inicialmente con WhatsApp), crearemos una **Capa de Abstracción de Canales**.

### Concepto Clave

El "Cerebro" (LangGraph) **no debe saber** si está hablando por Telegram, WhatsApp o una terminal. Solo debe entender un **"Mensaje Unificado"**.

### Diagrama de Flujo Propuesto

```Markdown
graph LR
    Telegram[Telegram Webhook] -->|JSON Específico| T_Adapter[Telegram Adapter]
    ManyChat[ManyChat Webhook] -->|JSON Específico| M_Adapter[ManyChat Adapter]
    
    T_Adapter -->|Normalización| Unified[Unified Message Model]
    M_Adapter -->|Normalización| Unified
    
    Unified --> Agent[Visionarias Brain (Core)]
    
    Agent -->|Respuesta Unificada| T_Adapter
    Agent -->|Respuesta Unificada| M_Adapter
    
    T_Adapter -->|API Call| TelegramAPI
    M_Adapter -->|API Call| ManyChatAPI
```

## 2. Cambios Estructurales

### 2.1. Nuevos Modelos Unificados (`src/core/schema.py`)

Definiremos objetos que representen la intención pura, sin "basura" de las plataformas externas.

* `IncomingMessage`: `user_id`, `text`, `metadata`, `source_channel`.

* `OutgoingMessage`: `user_id`, `text`, `message_type` (text, image, template).

### 2.2. Sistema de Adaptadores (`src/channels/`)

Crearemos una interfaz base y las implementaciones concretas.

* `src/channels/base.py`: Clase abstracta `BaseChannel` con métodos obligatorios:

  * `normalize(payload) -> IncomingMessage`

  * `send(response) -> None`

* `src/channels/telegram.py`: Implementación para tu prueba inmediata.

* `src/channels/whatsapp.py`: Refactorización de lo actual para cumplir el patrón.

### 2.3. Enrutamiento Dinámico (`src/api/routes.py`)

Expondremos endpoints limpios y separados para cada proveedor, pero que internamente invocan al mismo agente.

* `POST /webhooks/telegram` -> Usa `TelegramChannel`

* `POST /webhooks/whatsapp` -> Usa `WhatsAppChannel`

* `POST /webhooks/generic` -> Para integraciones futuras (ej. tu propia web).

## 3. Beneficios de esta Estrategia

1. **Pruebas Inmediatas**: Telegram es mucho más fácil de configurar y depurar que WhatsApp Business API. Podrás validar la lógica conversacional (S1->S6) en minutos.
2. **Preparado para ManyChat**: ManyChat suele enviar JSONs personalizados. Con este patrón, solo crearemos un `ManyChatAdapter` que mapee esos campos, sin tocar ni una línea del "Cerebro".
3. **Escalabilidad**: Puedes tener usuarios hablando por Telegram y WhatsApp simultáneamente; el sistema maneja ambos estados en paralelo sin conflictos.

## 4. Pasos de Ejecución

1. Crear `src/core/schema.py` con los modelos canónicos.
2. Crear `src/channels/base.py` y `src/channels/telegram.py`.
3. Actualizar `src/api/routes.py` para incluir el endpoint de Telegram.
4. Agregar configuración de Telegram (`TELEGRAM_BOT_TOKEN`) en `.env` y `config.py`.
5. Refactorizar la llamada al Agente para que use el modelo unificado en lugar de diccionarios crudos.

