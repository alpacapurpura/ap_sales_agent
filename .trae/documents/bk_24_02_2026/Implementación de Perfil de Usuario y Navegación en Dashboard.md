# Mejora de UX: Perfil de Usuario y Navegación

Basado en la investigación de sistemas agénticos (como ManyChat) y las mejores prácticas de UX, propongo la siguiente solución que respeta el principio KISS (Keep It Simple, Stupid) y aprovecha la infraestructura de Clerk existente.

## 1. Estrategia de Diseño (Propuesta)
En sistemas agénticos, el perfil no es solo "datos personales", sino el **Contexto del Usuario** para el agente.
*   **Identidad (Clerk)**: No duplicaremos formularios. Usaremos los datos de Clerk (Nombre, Email, Avatar) en modo lectura, con un botón para "Gestionar Cuenta" que abre el modal nativo de Clerk. Esto es seguro y familiar.
*   **Contexto del Sistema**: Agregaremos campos visuales para **Zona Horaria** (crítico para agentes que agendan o envían mensajes) e **Idioma**.
*   **Navegación**: El sidebar mostrará la identidad real y actuará como acceso directo.

## 2. Plan de Implementación

### A. Componente `ProfileView` (Nuevo)
Crearé un nuevo componente `src/components/settings/profile-view.tsx` que contendrá:
1.  **Tarjeta de Identidad**:
    *   Avatar grande (Clerk).
    *   Nombre completo y Correo (Solo lectura).
    *   Botón "Editar Perfil" (Invoca `clerk.openUserProfile()`).
2.  **Tarjeta de Preferencias (Contexto)**:
    *   **Zona Horaria**: Detectada automáticamente (ej. "America/Santiago"). Importante para la IA.
    *   **Idioma**: "Español" (Predefinido).
    *   **ID de Usuario**: Útil para soporte/depuración (pequeño y copiable).

### B. Página de Configuración (`settings/page.tsx`)
1.  Convertir a **Client Component** (`"use client"`) para manejar estados de navegación.
2.  Habilitar la pestaña **"Perfil"**.
3.  Implementar lógica para leer el parámetro de URL `?tab=profile` y abrir la pestaña correcta automáticamente desde el sidebar.

### C. Sidebar (`app-sidebar.tsx`)
1.  Integrar el hook `useUser` de Clerk.
2.  Reemplazar el texto estático "Cuenta" por el **Nombre del Usuario**.
3.  Reemplazar "Gestión de perfil" por el **Email**.
4.  Hacer que toda la sección sea un enlace (`Link`) a `/settings?tab=profile`.

## 3. Beneficios
*   **Cero Fricción**: El usuario no llena nada, la información ya está ahí.
*   **Transparencia**: El usuario ve qué datos tiene el agente (Timezone, Email).
*   **Consistencia**: Se usa la UI de Clerk para ediciones complejas (password, 2FA), manteniendo nuestra UI limpia.
