He diagnosticado la causa de la "desaparición" de tus datos en Postgres.

### Diagnóstico

1. **Problema de Permisos (Root Cause)**: Al ejecutar `ls -la` en la carpeta de datos (`./data/postgres_data`), recibí un error `Permission denied`. Esto sucede porque Docker ejecuta Postgres como usuario `postgres` (o root internamente), y al crear la carpeta en el host (tu máquina), le asigna permisos restrictivos que tu usuario normal no puede leer/escribir fácilmente, o peor aún, Docker no pudo escribir correctamente la primera vez y falló silenciosamente o creó una nueva estructura vacía al no poder acceder a la anterior.
2. **Configuración de** **`init_db`** **(Destructiva)**: En `src/services/database.py`, la función `init_db()` tiene estas líneas:

   ```python
   Base.metadata.drop_all(bind=engine)  # <--- BORRA TODO
   Base.metadata.create_all(bind=engine)
   ```

   Si tu contenedor se reinicia y, por alguna razón, el script de entrada (entrypoint) o alguna lógica de arranque llama a `init_db` automáticamente (común en entornos "dev"), **borrará todas las tablas cada vez que levantes el servicio**.
3. **Persistencia vs Reinicio**: Aunque arreglamos los volúmenes en `docker-compose.yml` (ahora apuntan a `./data/postgres_data`), si el código de la aplicación decide hacer un "hard reset" al arrancar, la persistencia del volumen no importa: el código borra los datos *dentro* del volumen persistente.

### Solución Propuesta

1. **Desactivar el Borrado Automático**: Modificaré `src/services/database.py` para que `init_db()` **NO ejecute** **`drop_all()`** por defecto. Solo debe crear tablas si no existen (`create_all` es seguro, `drop_all` no).
2. **Verificar Entrypoint**: Asegurarme de que el sistema no esté forzando un reinicio de DB innecesario.

### Plan de Acción

1. **Modificar** **`src/services/database.py`**: Comentar o eliminar la línea `Base.metadata.drop_all(bind=engine)` dentro de `init_db`. Esto evitará que futuros reinicios borren tu progreso.

Esto garantiza que la persistencia física (Docker Volumes) sea respetada por la lógica de la aplicación (Python).
