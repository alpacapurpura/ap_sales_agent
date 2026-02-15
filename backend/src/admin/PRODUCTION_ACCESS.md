# Guía de Acceso a Producción y Gestión de Usuarios

Esta guía detalla los pasos para conectarse al servidor, encender los servicios necesarios y gestionar usuarios desde el panel administrativo.

## 1. Conexión al Servidor (SSH)

Para acceder al panel administrativo (Streamlit) que corre en el puerto `8501` del servidor, recomendamos usar un **Túnel SSH**. Esto te permite ver el panel en tu navegador local (`localhost`) de forma segura.

Ejecuta el siguiente comando en tu terminal local (PowerShell o Terminal):

```bash
# Conexión directa a producción
ssh -L 8501:localhost:8501 -p 22022 root@161.132.41.191
```

Una vez conectado, navega a la carpeta del proyecto:

```bash
cd /opt/ap_sales_agent
```

## 2. Encender los Servicios

Si los contenedores están apagados para ahorrar recursos, debes encenderlos. El panel administrativo depende de la Base de Datos y la API.

```bash
# Opción A: Encender todo el stack (Recomendado para asegurar que todo funcione)
docker compose up -d

# Opción B: Encender solo lo necesario para administración (Si tienes perfiles configurados)
# docker compose up -d admin_dashboard_dev api_dev postgres redis
```

Verifica que los contenedores estén corriendo:

```bash
docker ps
```
Deberías ver `visionarias_admin_dev`, `visionarias_brain_dev` y `visionarias_postgres` en estado "Up".

## 3. Crear Tenants y Usuarios

1. Abre tu navegador web e ingresa a: **[http://localhost:8501](http://localhost:8501)**
2. En el menú lateral, selecciona **"🏢 Tenants (Clientes)"**.
3. **Para crear un nuevo Tenant**:
   - Despliega la sección "➕ Nuevo Cliente".
   - Llena los datos (Nombre, Slug, Configuración del Agente).
   - Haz clic en "Crear Cliente".
4. **Para crear un Usuario Administrador**:
   - En la misma página, baja a "Listado de Clientes".
   - Selecciona el cliente recién creado en el desplegable "Seleccionar Cliente para Editar".
   - Baja a la sección **"👥 Usuarios de [Nombre Cliente]"**.
   - Despliega "➕ Crear Nuevo Usuario".
   - Ingresa Nombre, Email y Contraseña.
   - Haz clic en "Crear Usuario".
   
   > **Nota**: El sistema creará automáticamente el usuario en el proveedor de identidad (Clerk) y lo vinculará a este Tenant, configurando los permisos necesarios.

## 4. Apagar los Servicios

Una vez termines tus tareas administrativas, puedes apagar los contenedores para detener el consumo de recursos:

```bash
docker compose stop
```

O si deseas eliminar los contenedores (manteniendo los datos en volúmenes):

```bash
docker compose down
```
