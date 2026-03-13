# Changelog Templates — Nicolify

Cada release genera DOS changelogs:
1. **Técnico** → para el historial del repo (CHANGELOG.md) y el equipo
2. **De usuario/negocio** → para comunicar a los clientes (fundadoras, tenants)

---

## Template: Changelog Técnico

```markdown
# Changelog Técnico — v{version}
**Fecha:** {fecha}
**Rama base:** main
**Commits incluidos:** {hash_inicial}...{hash_final}

## Breaking Changes
- [BREAKING] {descripción del cambio que rompe compatibilidad}

## Nuevas Funcionalidades
- `{módulo}`: {descripción técnica concisa}

## Bug Fixes
- `{módulo}`: {descripción del bug y la fix}

## Refactorizaciones
- `{módulo}`: {descripción del cambio interno}

## Infraestructura / DevOps
- {descripción de cambios de infra, Docker, CI/CD}

## Base de Datos
- Nuevas migraciones: `{nombre_migracion}`
- Cambios de esquema: {descripción}

## Dependencias
- Agregadas: {paquete@version}
- Actualizadas: {paquete@old → paquete@new}
- Eliminadas: {paquete}

## Notas para Deploy
- [ ] Ejecutar `alembic upgrade head` {si/no}
- [ ] Actualizar variables de entorno: {VARIABLE_NUEVA}
- [ ] Reiniciar servicios: {lista de servicios}
```

---

## Template: Changelog de Usuario / Negocio

Este es el que se comunica a las fundadoras (clientes del SaaS).
**Tono:** directo, beneficio-primero, sin jerga técnica. En español.

```markdown
# Nicolify — Novedades v{version}
**Fecha de actualización:** {fecha_legible}

¡Hola! Aquí tienes las novedades de esta versión de Nicolify:

## ✨ Novedades

### {Nombre del Feature en Términos de Negocio}
{Descripción de 2-3 líneas explicando QUÉ puede hacer ahora el usuario que antes no podía,
y cuál es el beneficio para su negocio. Sin términos técnicos.}

Ejemplo:
### Agente de ventas con memoria de conversación mejorada
Tu agente de IA ahora recuerda mejor el contexto de las conversaciones anteriores,
lo que le permite dar respuestas más personalizadas y cerrar ventas con mayor efectividad.

## 🐛 Mejoras y Correcciones
- {Descripción simple de una mejora o fix, en términos de experiencia de usuario}
- {Otra mejora}

## 🔧 Cambios que debes conocer
{Sección opcional. Solo si hay algo que el usuario necesita hacer o que cambia su flujo de trabajo.}

---
¿Tienes preguntas sobre estas novedades? Contáctanos en {canal_de_soporte}.
```

---

## Dónde guardar los changelogs

- **Técnico:** `docs/releases/v{version}/CHANGELOG_TECH.md`
- **Usuario:** `docs/releases/v{version}/CHANGELOG_USERS.md`
- **Raíz:** Actualizar `CHANGELOG.md` con el resumen técnico de cada release

## Cómo determinar el contenido

Para generar automáticamente los changelogs:

1. Obtener commits: `git log <ultimo-tag>..HEAD --pretty=format:"%h %s" --no-merges`
2. Clasificar por tipo de commit (feat/fix/refactor/etc.)
3. Mapear módulos técnicos → términos de negocio:

| Módulo técnico | Término de negocio |
|----------------|-------------------|
| `sales_agent` | Agente de ventas IA |
| `audit` | Panel de monitoreo de conversaciones |
| `brand` | Configuración de identidad de marca |
| `offer` | Catálogo de productos/servicios |
| `connections` | Integraciones (Telegram, WhatsApp, etc.) |
| `crm` | Gestión de leads y clientes |
| `scheduling` | Sistema de agenda y citas |
| `landing` / `assets` | Páginas de ventas |
