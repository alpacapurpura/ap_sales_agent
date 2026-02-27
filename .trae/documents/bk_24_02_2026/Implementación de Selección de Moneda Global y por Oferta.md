# Implementación de Selección de Moneda y Configuración Regional

Este plan detalla los pasos para implementar la selección de moneda en el "Resumen de la Oferta" y la configuración global del sistema, asegurando persistencia, validación y una UX consistente.

## 1. Definición de Datos y Constantes (Frontend)
Crearemos una fuente de verdad para las monedas soportadas.
- **Crear `frontend/src/lib/constants/currencies.ts`**:
  - Exportar lista de monedas (USD, EUR, GBP, MXN, COP, etc.).
  - Incluir metadatos: código ISO, símbolo, nombre y bandera (emoji o path a svg).

## 2. Backend: Configuración General del Tenant
Habilitaremos el almacenamiento de la configuración regional en el modelo `Tenant`.
- **Esquemas (`backend/src/core/schema.py`)**:
  - Crear modelo Pydantic `GeneralSettings` con campo `default_currency`.
- **API (`backend/src/api/routers/settings.py`)**:
  - Implementar `GET /general` para leer `Tenant.config_json`.
  - Implementar `PATCH /general` para actualizar `Tenant.config_json`.
  - Validar que la moneda exista en la lista permitida.

## 3. Frontend: Módulo de Configuración
Implementaremos la UI para que el usuario defina su moneda base.
- **API Client (`frontend/src/lib/api/settings.ts`)**:
  - Funciones `getGeneralSettings` y `updateGeneralSettings`.
- **Componente (`frontend/src/components/settings/general-settings-form.tsx`)**:
  - Formulario con `CurrencySelector` (nuevo componente).
  - Carga la configuración inicial y guarda cambios.
- **Página (`frontend/src/app/(dashboard)/settings/page.tsx`)**:
  - Reemplazar el placeholder "Próximamente" en el tab "General" con `<GeneralSettingsForm />`.

## 4. Frontend: Selector de Moneda y Conversión
Componentes reutilizables y lógica de negocio.
- **Componente `CurrencySelector` (`frontend/src/components/ui/currency-selector.tsx`)**:
  - Select de Shadcn UI personalizado.
  - Muestra bandera + código.
  - Buscable (combobox).
- **Hook `useCurrencyConverter` (`frontend/src/hooks/use-currency-converter.ts`)**:
  - Lógica para obtener tasas de cambio (mock inicial o API gratuita como `open.er-api.com`).
  - Funciones para convertir montos y formatear precios.

## 5. Integración en Offer Summary
Actualizar el formulario de oferta para soportar múltiples monedas.
- **Tipos (`frontend/src/lib/api/offer.ts`)**:
  - Actualizar interfaz `Offer` para incluir `currency: string`.
  - Actualizar `offerApi.saveOffer` para enviar `currency` dentro del objeto `pricing` o al nivel raíz según esquema backend.
- **Componente (`frontend/src/components/offer-studio/offer-summary-form.tsx`)**:
  - Integrar `CurrencySelector`.
  - Al cambiar moneda: recalcular el precio numérico usando `useCurrencyConverter`.
  - Mostrar precio formateado.
  - Inicializar con la moneda guardada en la oferta, o la default del sistema si es nueva.

## 6. Backend: Persistencia de Oferta
Asegurar que el backend guarde la moneda en el producto.
- **Esquemas (`backend/src/core/schema.py`)**:
  - Actualizar esquema de entrada de Producto si es estricto.
- **Lógica**:
  - Verificar que `pricing` en DB guarde `{ amount: X, currency: Y }`.

## Verificación
- Confirmar que la moneda default se guarda y persiste.
- Confirmar que al crear una oferta, toma la moneda default.
- Confirmar que al cambiar moneda en oferta, el precio se actualiza correctamente.
- Validar persistencia de la moneda específica de la oferta.
