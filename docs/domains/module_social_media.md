---
module: Social Media
status: active
core_files:
    - "backend/src/modules/social_media/"
    - "frontend/src/features/marketing-studio/"
---

## 1. Propósito del Negocio (El "Por Qué")
Gestionar la presencia orgánica de la marca. Permite generar piezas gráficas, redactar posts con la voz de la marca, calendarizar contenido y moderar comentarios en plataformas como Instagram y Facebook.

## 2. Reglas de Negocio Estrictas (Business Rules)
- Aislamiento Orgánico: No tiene control sobre presupuestos de inversión publicitaria. Todo su alcance es orgánico.
- Aprobación de Contenido: El contenido generado por IA (OrganicPost) siempre debe tener un estado de revisión antes de ser publicado, a menos que el Tenant active "Auto-Pilot".

## 3. Mapa de Código (Rutas relativas a Front y Back para este módulo)
- Backend: backend/src/modules/social_media/
- Frontend: frontend/src/features/marketing-studio/

## 4. Casos Borde Conocidos (Edge Cases)
- Rate Limits de APIs Externas: Ser bloqueado temporalmente por Meta si la IA intenta responder a cientos de comentarios en menos de un minuto.
- Desconexión Abrupta: Tokens de acceso (OAuth) revocados por Meta o expirados silenciosamente, provocando que fallen las publicaciones programadas.