# Admin Streamlit - Acceso via SSH Tunnel (Produccion)

Panel de administracion Streamlit para operaciones de superadmin (crear tenants, etc.).
Solo accesible via SSH tunnel — sin exposicion publica.

## Arquitectura

```
[Tu PC localhost:8501] --SSH Tunnel--> [Servidor:127.0.0.1:8501] --> [Container: visionarias_admin:8501]
```

- El contenedor solo escucha en `127.0.0.1` (no accesible desde internet)
- Se levanta bajo el profile `admin` (no arranca con el resto de servicios)
- `restart: "no"` — si se cae o reinicias el server, no vuelve a subir solo

## Paso a paso

### 1. Conectarte al servidor y levantar el contenedor

```bash
# SSH al servidor
ssh tu-usuario@tu-servidor

# Ir al directorio del proyecto
cd /ruta/al/proyecto

# Levantar SOLO el admin (profile "admin")
docker compose -f docker-compose.prod.yml --env-file .env.prod --profile admin up -d admin
```

Verifica que esta corriendo:

```bash
docker ps --filter name=visionarias_admin
```

### 2. Abrir el SSH tunnel desde tu maquina local

En una **nueva terminal local** (no en el servidor):

```bash
ssh -L 8501:localhost:8501 tu-usuario@tu-servidor
```

Esto mapea tu `localhost:8501` al puerto `8501` del servidor (que a su vez va al contenedor).

> **Tip:** Puedes agregar `-N -f` para que el tunnel corra en background sin abrir shell:
> ```bash
> ssh -N -f -L 8501:localhost:8501 tu-usuario@tu-servidor
> ```

### 3. Acceder al panel

Abre en tu navegador:

```
http://localhost:8501
```

Streamlit deberia cargar normalmente como si fuera local.

### 4. Cuando termines: bajar el contenedor

Desde el servidor (o por SSH):

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod --profile admin stop admin
```

O si quieres eliminarlo completamente:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod --profile admin down --remove-orphans
```

Y cierra el tunnel SSH (si usaste `-N -f`, busca el proceso):

```bash
# Encontrar el PID del tunnel
ps aux | grep "ssh -N -f -L 8501"

# Matarlo
kill <PID>
```

## Atajo SSH (opcional)

Agrega esto a tu `~/.ssh/config` local para simplificar:

```
Host nicolify-prod
    HostName tu-servidor-ip-o-dominio
    User tu-usuario
    IdentityFile ~/.ssh/tu-key-privada

Host nicolify-admin
    HostName tu-servidor-ip-o-dominio
    User tu-usuario
    IdentityFile ~/.ssh/tu-key-privada
    LocalForward 8501 localhost:8501
```

Despues solo necesitas:

```bash
# Tunnel + shell
ssh nicolify-admin

# O solo tunnel en background
ssh -N -f nicolify-admin
```

## Troubleshooting

| Problema | Solucion |
|---|---|
| `localhost:8501` no carga | Verificar que el container esta corriendo: `docker ps --filter name=visionarias_admin` |
| `bind: Address already in use` al hacer SSH | Ya hay un tunnel abierto. Busca el proceso: `lsof -i :8501` y matalo |
| Container se cae inmediatamente | Revisar logs: `docker logs visionarias_admin` |
| Streamlit muestra error de conexion a API | Verificar que el backend esta corriendo: `docker ps --filter name=visionarias_brain` |

## Seguridad

- El puerto 8501 **nunca** esta expuesto publicamente (bind a `127.0.0.1`)
- La autenticacion es via SSH keys (no password)
- El contenedor solo vive mientras lo necesitas (profile `admin`, restart `no`)
- No hay labels de Traefik — no hay ruta publica
