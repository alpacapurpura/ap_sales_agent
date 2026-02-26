# Informe de Auditoría Frontend

## 1. Resumen Ejecutivo
Este documento detalla los hallazgos de la auditoría técnica realizada al código fuente del frontend. Se han identificado problemas críticos de rendimiento y arquitectura que requieren atención inmediata, así como oportunidades de optimización para mejorar la experiencia del usuario y la mantenibilidad del código.

## 2. Problemas Críticos (Prioridad 1)
Estos problemas afectan directamente el rendimiento o la estabilidad de la aplicación y deben resolverse con urgencia.
- **Bloqueo en `layout.tsx`**: Uso de `await currentUser()` que bloquea el renderizado inicial.
- **Versiones 'latest' en `package.json`**: El uso de versiones no fijas ('latest') introduce riesgos de inestabilidad y falta de reproducibilidad en los entornos.
- **Archivo Barril en `frontend/src/features/brand/index.ts`**: Puede causar problemas de tree-shaking y aumentar el tamaño del bundle innecesariamente.

## 3. Problemas de Alta Prioridad (Prioridad 2)
Estos problemas tienen un impacto significativo en el rendimiento o las mejores prácticas de Next.js.
- **Uso innecesario de 'use client'**: Detectado en `SalesPage`, `ObjectionsPage` y `KnowledgePage`. Esto impide la renderización en el servidor (SSR) de estos componentes.
- **Fetching manual con `useEffect`**: Uso de `useEffect` para la obtención de datos en `useOffer.ts` y `useBrandSettings.ts` en lugar de usar Server Components o librerías de data fetching como TanStack Query.
- **Falta de importaciones dinámicas**: `OfferEditor` y `LandingPageEditor` deberían cargarse dinámicamente (`dynamic imports`) para reducir el tamaño del bundle inicial.

## 4. Problemas de Prioridad Media/Baja
Mejoras sugeridas para la calidad del código y optimizaciones menores.
- **Uso de `<img>` en lugar de `next/image`**: Se detectó en 19 archivos. `next/image` ofrece optimización automática de imágenes.
- **Falta de uso de `React.cache`**: Para memoizar peticiones de datos en el servidor y evitar duplicidad.

## 5. Correcciones Aplicadas
Mejoras y correcciones ya implementadas durante la sesión.
- **Limpieza de `console.log`**: Se eliminaron logs innecesarios para limpiar la salida de la consola.
- **Optimización de Componentes**: Se optimizaron `TeamList` y `OfferLivePreview` para mejorar su rendimiento.
