Voy a implementar un sistema de cambio de tema robusto y ajustar los colores para garantizar la legibilidad.

### 1. Instalación de Dependencias
- Instalaré `next-themes` en el frontend para gestionar el cambio entre modo claro y oscuro de forma persistente y compatible con Next.js.
- **Comando:** `npm install next-themes` (seguido de la reconstrucción del contenedor).

### 2. Creación de Componentes de Tema
Crearé dos nuevos componentes en `frontend/src/components/`:
- **`theme-provider.tsx`**: Un envoltorio que inyecta el contexto del tema a toda la aplicación.
- **`mode-toggle.tsx`**: Un botón interruptor (toggle) visible en la interfaz para que puedas cambiar manualmente entre modos.

### 3. Integración en la Arquitectura
- Modificaré **`frontend/src/app/providers.tsx`** para incluir el `ThemeProvider`. Esto asegura que toda la app tenga acceso al estado del tema sin ensuciar el `layout.tsx`.

### 4. Corrección de Estilos y Colores (`globals.css`)
Reescribiré las variables CSS para cumplir con tus preferencias de color y asegurar contraste alto (Accesibilidad AA/AAA):

**Modo Claro (Cream & White):**
- **Fondo:** Blanco puro o Crema muy suave (`hsl(60 20% 99%)`) para evitar fatiga visual por brillo excesivo.
- **Texto:** Gris oscuro/Carbón (`hsl(240 10% 3.9%)`). **Nunca negro puro**, para suavizar la lectura.

**Modo Oscuro (Slate & Blueish):**
- **Fondo:** Azul Grisáceo Oscuro (`hsl(222.2 47.4% 11.2%)` o similar). Evitaremos el negro absoluto (`#000`) para reducir el "smearing" en pantallas OLED y mejorar la profundidad.
- **Texto:** Blanco Hueso (`hsl(210 40% 98%)`).
- **Bordes/Inputs:** Tonos intermedios para que se distingan del fondo pero no brillen demasiado.

### 5. Verificación
- Verificaré que el texto sea siempre legible sobre su fondo correspondiente.
- Confirmaré que el botón de cambio funcione y persista la elección al recargar.
