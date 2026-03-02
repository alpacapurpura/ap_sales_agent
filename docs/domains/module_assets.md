---
module: Módulo Transversal Assets
status: active
core_files: []
---

## 1. Propósito del Negocio (El "Por Qué")
- Gestión centralizada de archivos estáticos (imágenes, PDFs, audios, galerías).

## 2. Reglas de Negocio Estrictas (Business Rules)
- Todo archivo entrante debe tener validación rigurosa de MIME-type para evitar inyecciones de código malicioso.
- Los otros módulos (offer, brand) solo deben guardar URLs o referencias UUID provistas por este módulo, nunca el archivo binario per se.

## 3. Mapa de Código (Rutas relativas a Front y Back para este módulo)
- Backend: backend/src/modules/assets/
- Frontend: Utils compartidas y visualizadores de Media en el UI.

## 4. Casos Borde Conocidos (Edge Cases)
- Almacenamiento Desbordado: Subida de videos pesados que saturan el disco local si no hay políticas estrictas de subida directa a S3/CDN o límites de tamaño por Tenant.