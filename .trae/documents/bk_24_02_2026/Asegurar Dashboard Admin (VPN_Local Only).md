# Plan de Seguridad: Dashboard Administrativo "Solo VPN/Local"

Para cumplir con el requerimiento de aislar completamente el panel de administración (`src/admin`) y seguir las mejores prácticas de seguridad SaaS, implementaremos una estrategia de **"Defensa en Profundidad"**:

1.  **Nivel Red (Docker):** Desconectaremos el contenedor del Admin del proxy público (Traefik) y lo obligaremos a escuchar solo en la interfaz local (`localhost`).
2.  **Nivel Acceso (VPN/Túnel):** Estableceremos el protocolo de acceso mediante Túnel SSH o VPN (Tailscale), garantizando que solo usuarios autenticados en la red privada puedan llegar al puerto.

## Pasos de Implementación

### 1. Modificar `docker-compose.yml`
Editaremos la configuración del servicio `admin_dashboard_prod` para:
*   **Eliminar Etiquetas Traefik:** Borrar las secciones `labels` que exponen el servicio a través de `traefik.http.routers.admin...`. Esto elimina la ruta pública `admin.tudominio.com`.
*   **Restringir Puertos:** Añadir un binding explícito a `127.0.0.1`.
    *   *Antes:* Sin puertos (o expuesto vía red interna a Traefik).
    *   *Ahora:* `ports: - "127.0.0.1:8501:8501"`.
    *   *Efecto:* El puerto 8501 solo aceptará conexiones que se originen dentro del mismo servidor. Si alguien intenta acceder a `IP_PUBLICA:8501`, será rechazado.

### 2. Documentar Protocolo de Acceso Seguro
Crearé un archivo de reglas `rules/admin-access.md` que servirá como guía para tu equipo, documentando dos métodos de acceso:

*   **Método A: Túnel SSH (Inmediato y Estándar)**
    *   No requiere instalar nada nuevo.
    *   Comando: `ssh -L 8501:127.0.0.1:8501 usuario@servidor`
    *   Uso: Abrir `http://localhost:8501` en tu navegador local.
*   **Método B: Tailscale VPN (Recomendado para Equipos)**
    *   Instalar Tailscale en el servidor y en las laptops del equipo.
    *   Usar `tailscale serve` para exponer el puerto local a la red privada (Tailnet).

### 3. Verificación
*   Confirmar que el dominio público ya no responde.
*   Confirmar que el acceso local (vía SSH) funciona correctamente.

## ¿Por qué esta solución?
*   **Elimina la superficie de ataque:** Al no estar en Traefik ni en 0.0.0.0, es invisible para escáneres de internet y ataques DDoS a la capa de aplicación.
*   **Cumplimiento:** Sigue el principio de "Privilegio Mínimo" y "Seguridad por Diseño".
