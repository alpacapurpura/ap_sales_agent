# Habilitar Acceso a "Personalidad IA" en Dashboard

Para que puedas acceder a la herramienta de clonación de chats desde el dashboard, añadiré un acceso directo en la barra lateral de navegación.

## Plan de Cambios

### 1. Actualizar `AppSidebar` (Frontend)
Editaré el archivo `frontend/src/components/layout/app-sidebar.tsx` para agregar la nueva opción en el menú principal.

*   **Nueva Sección:** Agregaré "Personalidad IA" (o "Estilo") al array `navItems`.
*   **Icono:** Usaré el icono `MessageSquare` o `Sparkles` para representarlo.
*   **Ruta:** Apuntará a `/onboarding/style`.

```typescript
// Cambio propuesto en navItems:
{
  title: "Personalidad IA",
  href: "/onboarding/style",
  icon: MessageSquare, // Importar de lucide-react
}
```

### 2. Verificar Rutas
Confirmaré que la página `/onboarding/style` esté accesible y no bloqueada por layouts anidados incorrectos (ya verifiqué que existe en `app/(dashboard)/onboarding/style/page.tsx`, lo cual es correcto porque hereda el layout del dashboard).

---

**Respuesta a tu pregunta:**
Actualmente la opción **no está visible** porque, aunque creamos la página, no pusimos el botón en el menú.
Voy a agregar el botón **"Personalidad IA"** en el menú lateral izquierdo, justo debajo de "Avatares", para que puedas entrar con un clic.
