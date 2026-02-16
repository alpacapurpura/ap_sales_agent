# Guía de Acceso al Admin de Producción (Windows -> VPS Ubuntu)

Esta guía explica cómo conectar tu máquina local (Windows) al panel administrativo de Streamlit en el VPS de producción para gestionar Tenants y Usuarios.

## 1. Requisitos Previos

- **IP del VPS**: `161.132.41.191`
- **Puerto SSH**: `22022`
- **Usuario**: `root`
- Tener la llave SSH configurada en tu máquina Windows.
- Terminal recomendada: PowerShell o Git Bash.

## 2. Establecer Túnel SSH

El panel administrativo corre en el puerto `8501` del VPS pero **no está expuesto a internet** por seguridad. Debemos crear un "túnel" para acceder como si estuviera en tu PC.

### Opción A: Desde WSL / Ubuntu (Recomendado)
Si tienes tus llaves SSH en WSL (`/home/chris/.ssh/id_rsa`), **debes ejecutar este comando desde tu terminal de Ubuntu (WSL)**, no desde PowerShell.

```bash
# Ejecutar en tu terminal de WSL
ssh -L 8501:127.0.0.1:8501 -p 22022 -i /home/chris/.ssh/id_rsa root@161.132.41.191
```

### Opción B: Desde Windows (PowerShell)
Si necesitas usar PowerShell, debes tener la llave privada en Windows (`C:\Users\TuUsuario\.ssh\id_rsa`). Si solo la tienes en WSL, usa la Opción A.

```powershell
# Solo si la llave está configurada en Windows
ssh -L 8501:127.0.0.1:8501 -p 22022 root@161.132.41.191
```

> **Explicación**:
> *   `-L 8501:127.0.0.1:8501`: "Todo lo que yo envíe a mi localhost:8501, mándalo al 127.0.0.1:8501 del servidor remoto".
> *   Mantén esta terminal **abierta** mientras necesites usar el admin.

## 3. Encender Servicios en el VPS

Una vez dentro del servidor (en la terminal del paso anterior), navega a la carpeta y levanta los servicios usando la configuración de **PRODUCCIÓN**.

1.  Ir al directorio:
    ```bash
    cd /opt/ap_sales_agent
    ```

2.  Ejecutar Docker Compose.
    
    ⚠️ **IMPORTANTE**: En producción siempre debemos especificar `-f docker-compose.prod.yml` y `--env-file .env.prod`.

    **Opción A: Encender TODO el sistema** (Recomendado si el sitio público también debe estar online)
    ```bash
    docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
    ```

    **Opción B: Encender SOLO Admin y Backend** (Modo mantenimiento/ahorro de recursos)
    Si solo entras a configurar algo y no necesitas el frontend público (`frontend` service):
    ```bash
    # Levantamos: admin, backend (API) y sus dependencias (DBs)
    docker compose -f docker-compose.prod.yml --env-file .env.prod up -d admin backend postgres qdrant redis
    ```

3.  Verificar estado:
    ```bash
    docker compose -f docker-compose.prod.yml ps
    ```
    Deberías ver los contenedores `visionarias_admin`, `visionarias_brain`, `visionarias_postgres`, etc., en estado **Up**.

## 4. Acceder al Panel

1.  Vuelve a tu navegador en Windows.
2.  Ingresa a: **[http://localhost:8501](http://localhost:8501)**
3.  Verás la interfaz de Streamlit cargando.

## 5. Gestión de Tenants y Usuarios

Una vez dentro del panel:

1.  Ve al menú lateral **"🏢 Tenants (Clientes)"**.
2.  **Crear Cliente**:
    - Despliega "➕ Nuevo Cliente".
    - Llena Nombre, Slug y Configuración.
    - Click en "Crear Cliente".
3.  **Crear Usuario Admin para el Cliente**:
    - Selecciona el cliente en "Listado de Clientes".
    - Baja a **"👥 Usuarios de [Nombre Cliente]"**.
    - Despliega "➕ Crear Nuevo Usuario".
    - Ingresa credenciales.
    - El sistema lo registrará automáticamente en **Clerk** y en la base de datos local.

## 6. Cerrar Sesión y Apagar

1.  **En el VPS**:
    Si solo encendiste los servicios para esta tarea y quieres apagarlos:
    ```bash
    docker compose -f docker-compose.prod.yml stop
    ```
    *(Si el sitio debe seguir online, no ejecutes esto).*

2.  **En Windows**:
    Escribe `exit` en la terminal para desconectarte del VPS y luego cierra la ventana de PowerShell.

## 7. Solución de Problemas (Troubleshooting)

### Error: `UndefinedColumn ... column tenants.clerk_org_id does not exist`
Este error ocurre cuando el código está actualizado pero la base de datos no tiene las últimas columnas. Debes ejecutar las migraciones.

**Solución**:
Ejecuta esto en el VPS (dentro de `/opt/ap_sales_agent`):

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```
Luego reinicia el admin:
```bash
docker compose -f docker-compose.prod.yml restart admin
```
