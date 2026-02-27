Entendido. Procederé con la instalación automática. Si la terminal requiere confirmación, la manejaré o te avisaré.

**Pasos de Ejecución:**

1.  **Generar Componentes**: Ejecutaré `npx shadcn@latest add radio-group select switch` en el directorio `frontend`. Esto creará los archivos faltantes (`radio-group.tsx`, `select.tsx`, `switch.tsx`).
2.  **Actualizar Contenedor**: Ejecutaré `docker compose --profile development up -d --build client_dashboard` para que el entorno Docker instale las nuevas dependencias de Radix UI.
3.  **Validar**: Comprobaré que el servidor levante sin errores de "Module not found".

Procedo de inmediato.