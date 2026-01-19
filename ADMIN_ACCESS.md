# Acceso Seguro al Dashboard Administrativo

> **Estado de Seguridad:** ALTO 🔒
> El acceso público al panel de administración ha sido deshabilitado.
> El servicio solo escucha en `127.0.0.1:8501` dentro del servidor.

Para acceder al panel de administración (`src/admin`), debes utilizar uno de los siguientes métodos seguros.

## Método 1: Túnel SSH (Recomendado para Acceso Rápido)

Este método no requiere instalar software adicional si ya tienes acceso SSH al servidor.

1.  **Establecer el Túnel:**
    Ejecuta el siguiente comando desde tu terminal local (PowerShell, Terminal, Bash):
    ```bash
    # Sintaxis: ssh -L [PuertoLocal]:127.0.0.1:[PuertoRemoto] usuario@servidor
    ssh -L 8501:127.0.0.1:8501 chris@tuserver.com
    ```
    *Reemplaza `chris@tuserver.com` con tus credenciales reales.*

2.  **Acceder:**
    Abre tu navegador web y visita:
    [http://localhost:8501](http://localhost:8501)

    *Mientras la terminal SSH esté abierta, el túnel estará activo.*

## Método 2: VPN con Tailscale (Recomendado para Equipos)

Tailscale crea una red privada segura (Mesh VPN) entre tus dispositivos.

### Configuración en el Servidor (Solo una vez)
1.  Instala Tailscale: `curl -fsSL https://tailscale.com/install.sh | sh`
2.  Inicia sesión: `sudo tailscale up`
3.  **Exponer el servicio local a la red Tailscale:**
    Como el contenedor Docker solo escucha en `127.0.0.1`, debes usar `tailscale serve` para compartirlo con la red VPN:
    ```bash
    sudo tailscale serve --bg 8501 http://127.0.0.1:8501
    ```

### Acceso desde tu Computadora
1.  Instala Tailscale en tu laptop/PC.
2.  Conéctate a la misma red (mismo usuario/organización).
3.  Obtén la "MagicDNS" o IP de Tailscale del servidor (ej. `visionarias-server`).
4.  Abre en el navegador:
    `http://visionarias-server:8501` (o la IP de Tailscale).

---

## Solución de Problemas

*   **"Connection Refused" en localhost:8501:**
    *   Verifica que el túnel SSH esté activo.
    *   Verifica que el contenedor esté corriendo: `docker ps | grep admin`.
*   **El dominio público da error 404 o 502:**
    *   **Correcto.** Esto es el comportamiento esperado. Ya no existe ruta pública.
