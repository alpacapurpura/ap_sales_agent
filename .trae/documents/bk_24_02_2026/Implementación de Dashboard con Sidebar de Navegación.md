
# Rediseño del Dashboard: Estilo Hostinger/Cloudflare

Para lograr una navegación intuitiva y escalable (preparada para agregar gestión de archivos y más), implementaré una **Arquitectura de Shell (Cascarón)** con una barra lateral persistente. Este es el estándar de la industria (usado por Hostinger, Cloudflare, Vercel) porque permite acceder rápidamente a cualquier sección sin perder contexto.

## Propuesta Visual y Funcional

1.  **Barra Lateral (Sidebar) Inteligente:**
    *   **Navegación Principal:** Menú vertical a la izquierda con iconos claros (Lucide React).
    *   **Secciones:**
        *   📊 **Resumen:** Estadísticas generales (Tu Home actual).
        *   📚 **Conocimiento:** (Nueva) Gestión de archivos y fuentes de datos.
        *   🔍 **Auditoría:** (Actual) Inspector de trazas y chats.
        *   ⚙️ **Configuración:** Ajustes del agente.
    *   **Estado Activo:** Indicadores visuales claros de en qué sección estás.

2.  **Cabecera (Header) Unificada:**
    *   Migas de pan (Breadcrumbs) para saber dónde estás.
    *   Perfil de usuario (UserButton de Clerk) siempre visible.
    *   Toggle de Tema (Claro/Oscuro).

3.  **Reorganización Técnica (Route Groups):**
    *   Moveré las páginas actuales dentro de un grupo `(dashboard)` para que todas compartan automáticamente este nuevo diseño, sin tener que copiar y pegar el menú en cada página.

## Resultado Esperado
Tendrás un panel profesional donde agregar la sección de "Archivos" será tan simple como crear una nueva página, y el menú se encargará del resto.
