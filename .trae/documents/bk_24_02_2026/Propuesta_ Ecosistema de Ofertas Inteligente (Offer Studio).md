# Plan Actualizado: Ecosistema de Ofertas & Value Ladder (Frontend + Backend)

Este plan incorpora la "Clase Maestra OFFER" y el sistema de Herencia Global solicitados, cerrando la brecha entre un simple "producto" y una "Oferta Híbrida Inteligente".

## 1. Estrategia de Herencia Global (Frontend)
Para cumplir con el requerimiento de "Heredar automática y decidir agregar/eliminar", implementaremos un **Sistema de Plantillas Globales**.
* **Configuración Global**: En `Settings > Sales Logic`, el usuario define "Prerrequisitos Globales" (ej: "Negocio Activo") y "Objeciones Comunes".
* **Comportamiento en Offer Studio**: Al crear una nueva oferta, el frontend leerá estos globales y poblará el estado inicial del formulario. El usuario podrá borrar o añadir sin afectar la global.

## 2. Evolución Final del Modelo de Datos (Backend)
Actualizaremos `Product` para reflejar exactamente la "Clase Maestra" provista.

* **Nuevos Campos en `Product`**:
  * `primary_outcome` (String): El resultado tangible.
  * `time_to_value` (String): "Resultados en 3 semanas".
  * `prerequisites` (JSONB): Lista de strings (Heredable).
  * `guarantee_terms` (Text): Explicación legal/ventas.
  * `includes_offers` (JSONB): Lista de UUIDs para "Value Stacking" (Modularización).
  * `pricing` (JSONB): Estructura estricta `Pricing_Structure` (Label, Total, Deposit, Installments, Savings).

* **Validación**:
  * Regla de Negocio: `Offer.min_financial_capacity <= Lead.financial_tier`.

## 3. Propuesta Frontend: "Offer Ecosystem Studio"
Ubicación: `src/features/offer-studio`

### Arquitectura del Wizard (5 Fases)

#### FASE 1: Identidad y Logística (Identity)
* **Inputs**: SKU, Nombre Público, Tipo (Enum), Delivery Model (Enum).
* **UX**: Selectores visuales (Cards) para el `DeliveryModel` con explicación ("DIY", "DWY", "DFY").

#### FASE 2: La Promesa (The Why)
* **Inputs**: Headline, Primary Outcome, Time to Value.
* **Avatar Match**: Selector múltiple de Avatares (Lead Match).

#### FASE 3: Value Stack & Modularidad (The What)
* **Componente "Bundle Builder"**:
    * "Incluir otra oferta": Buscador de productos existentes (para Value Stacking).
    * "Entregables Específicos": Lista dinámica de `DeliverableItem` (Nombre, Formato, Valor Percibido).
    * *Visualización*: Calculadora automática del "Valor Total Percibido" sumando los componentes.

#### FASE 4: Arquitectura Financiera (The How)
* **Componente "Pricing Engine"**:
    * Botón "Agregar Plan de Pago".
    * Inputs: Label ("Pago Único"), Monto, Cuotas, Depósito.
    * Toggle: "Is Default?"
    * *Preview*: Muestra cómo el Agente presentará el ahorro ("Ahorras $X").

#### FASE 5: Reglas de Venta (Gatekeeping & Risks)
* **Prerrequisitos**: Carga inicial desde Global -> Edición inline.
* **Garantía**: Selector de Tipo + Editor de Texto para los términos.
* **Downsell Logic**: Selector "Si dicen NO por precio, ofrecer: [Product Dropdown]".

## 4. Plan de Ejecución Inmediata
1.  **Backend**: Modificar `business.py` agregando los campos faltantes (`primary_outcome`, `includes_offers`, etc.) y ejecutar migración.
2.  **Frontend**: Crear la estructura base de `features/offer-studio`.
3.  **Frontend**: Implementar el formulario paso a paso conectando con los Enums y la nueva estructura.

