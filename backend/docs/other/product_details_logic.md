# Guía de Interpretación: ProductDetails para Agentes IA

Este documento define la lógica de negocio y comportamiento esperado del Agente IA al interactuar con ofertas del tipo `ProductDetails`.

## Concepto
`ProductDetails` modela **Activos Estáticos**.
*   **Filosofía**: "Compra (o registro) -> Entrega Inmediata".
*   **Intervención Humana**: Nula o logística.

---

## 1. Interpretación de Logística (FulfillmentType)

El campo `fulfillment_type` es el cerebro de la operación. El Agente debe leerlo para decidir qué datos pedir y qué prometer.

### A. DIRECT_DOWNLOAD
*   **Qué es**: Un archivo simple (PDF, Ebook, Audio).
*   **Comportamiento del Agente**:
    1.  **NO** pedir dirección física.
    2.  **NO** crear cuentas de usuario complejas.
    3.  **Promesa**: "En cuanto confirmes, te envío el link de descarga a tu correo".
    4.  **Cierre**: Rápido. Es una transacción de baja fricción.

### B. EXTERNAL_PLATFORM_ACCESS
*   **Qué es**: Acceso a un LMS (Kajabi, Hotmart) o herramienta (Notion).
*   **Comportamiento del Agente**:
    1.  **Explicar**: "El acceso te llegará por correo desde [Plataforma]".
    2.  **Gestionar Expectativas**: "Revisa tu carpeta de Spam si no lo ves en 5 minutos".
    3.  **Valor**: Vender el acceso a la plataforma como algo "Premium".

### C. PHYSICAL_SHIPPING
*   **Qué es**: Algo tangible (Libro, Hoodie, Caja).
*   **Comportamiento del Agente (CRÍTICO)**:
    1.  **Activar Flujo de Datos**: Debe invocar pasos para pedir:
        *   Dirección completa (Calle, Ciudad, CP).
        *   País (para calcular `shipping_cost`).
    2.  **Verificar Stock**: Antes de prometer, chequear `stock_quantity`.
    3.  **Ansiedad de Espera**: Indicar tiempos estimados de envío si están disponibles en metadata.

---

## 2. Estrategia de Venta (Psychology Specs)

Utiliza los atributos del producto para persuadir.

### A. `estimated_consumption_time_minutes`
Usa este dato para **minimizar el esfuerzo percibido**.
*   *Si es bajo (< 30 min)*: "Es una guía súper práctica, en solo 15 minutos tendrás la estrategia lista."
*   *Si es alto (> 120 min)*: "Es una Masterclass completa y profunda, ideal para bloquear una tarde de estudio."

### B. `format` (DigitalFormat)
Usa el formato para tangibilizar el valor.
*   **PDF**: "Guía de referencia rápida".
*   **VIDEO**: "Clase inmersiva".
*   **NOTION**: "Sistema de gestión listo para usar".

---

## 3. Manejo de Errores y Edge Cases

### Stock Agotado (`stock_quantity == 0`)
*   **Si es Físico**: NO vender. Ofrecer: "Lo siento, se agotaron los Hoodies. ¿Te anoto en la lista de espera para el próximo drop?"
*   **Si es Digital**: Esto no debería pasar (stock infinito), a menos que sea una "Oferta Limitada por Cupos" artificial.

### Falta de URL (`access_url` vacío)
*   Si el producto es Digital y no tiene URL, es un **Error de Configuración**.
*   **Acción del Agente**: Reportar error interno al Admin, y decirle al usuario: "Estoy verificando el enlace de descarga, dame un momento". (No romper la inmersión).

---

## Resumen de Reglas de Oro

1.  **Digital = URL Obligatoria**.
2.  **Físico = Dirección Obligatoria**.
3.  **Físico = Chequear Stock**.
4.  **Venta = Minimizar Esfuerzo (Time) + Maximizar Valor (Format)**.
