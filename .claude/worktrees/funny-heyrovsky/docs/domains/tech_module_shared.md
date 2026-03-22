---
module: Technical Module Shared
status: active
core_files: []
---

## 1. Propósito del Negocio (El "Por Qué")
- Contener el ADN transversal del negocio. Aquí viven las entidades base (Base model de SQLAlchemy), Value Objects comunes y utilidades compartidas que deben ser accesibles para todos los demás módulos sin generar acoplamiento directo entre ellos.

## 2. Reglas de Negocio Estrictas (Business Rules)
- Regla de Dependencias: shared PUEDE importar utilidades de core, pero NUNCA debe importar nada que pertenezca a las carpetas en modules.
- Mailing Genérico: Contiene la función técnica agnóstica (send_email() en src/shared/mailing/) que ejecuta el envío físico. Absorbe la complejidad técnica para que los módulos de negocio (CRM, Scheduling, IAM) solo se enfoquen en qué redactar y a quién enviar.

## 3. Mapa de Código (Rutas relativas a Front y Back para este módulo)
- Backend: backend/src/shared/

## 4. Casos Borde Conocidos (Edge Cases)
- Modificaciones Críticas: Al ser la base compartida y ser importado por todos los módulos, un cambio en un esquema aquí (por ejemplo, en el Base model) puede quebrar la compilación o las migraciones en toda la aplicación de manera no aislada (Efecto dominó).