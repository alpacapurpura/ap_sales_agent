# Despliegue Local (Manual)

Este método te permite desplegar actualizaciones a producción **sin usar GitHub Actions** ni pagar por minutos de cómputo en la nube. Tu propia computadora actúa como el "servidor de construcción" y envía los cambios directamente al servidor.

## Requisitos Previos

1.  **Docker Instalado**: Debes tener Docker corriendo en tu máquina local.
2.  **Acceso SSH Configurado**: Debes tener tu llave SSH (`id_rsa`) en `/home/chris/.ssh/id_rsa` y acceso verificado al servidor `161.132.41.191`.
3.  **Archivo .env.prod**: Debes tener el archivo `.env.prod` en la raíz del proyecto con las variables de producción actualizadas.

## Pasos para Desplegar

1.  Abre una terminal en la raíz del proyecto (`AISALESHT`).
2.  Ejecuta el siguiente comando:

```bash
./despliegue/local/deploy_local.sh
```

## ¿Qué hace este script?

1.  **Lee Configuración**: Carga las variables de entorno de `.env.prod`.
2.  **Compila (Build)**: Crea las imágenes Docker de `backend` y `frontend` usando el CPU de tu laptop.
3.  **Transfiere**: Comprime las imágenes y las envía por un "tubo" SSH directo al servidor, evitando subir gigabytes a un registro intermedio.
4.  **Actualiza Config**: Copia el `docker-compose.prod.yml` y el `.env.prod` al servidor.
5.  **Reinicia**: Se conecta al servidor y reinicia los contenedores con las nuevas imágenes.

## Monitoreo

Para ver si todo salió bien, el script te mostrará logs en tiempo real. Si quieres verificar el estado del servidor después del despliegue:

```bash
# Entrar al servidor
ssh -p 22022 root@161.132.41.191

# Ver contenedores corriendo
docker ps

# Ver logs del backend
docker logs -f visionarias_brain

# Ver logs del frontend
docker logs -f visionarias_client
```
