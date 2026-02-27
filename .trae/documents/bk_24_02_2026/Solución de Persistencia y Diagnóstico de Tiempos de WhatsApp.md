# Diagnóstico Manual de Infraestructura (Evolution API)

Atendiendo a tu solicitud, vamos a aislar el problema verificando manualmente el comportamiento del contenedor `visionarias_whatsapp` antes de tocar código.

## 1. Prueba Manual de Tiempos y Estado
Ejecutaré una secuencia de comandos controlada desde la terminal para simular lo que hace el backend, pero con visibilidad total:

1.  **Limpieza**: Borraré manualmente la instancia `6347e21e-8112-4aa1-80d3-6adaa73bf6f9`.
2.  **Disparo**: Crearé la instancia vía `curl` desde dentro de la red Docker.
3.  **Monitoreo**:
    *   Observaré los logs de `visionarias_whatsapp` para detectar el momento exacto en que dice "Browser Launched" y "QR Code Generated".
    *   Cronometraré cuánto tarda desde el comando `create` hasta que el QR está disponible.
    *   Verificaré si el navegador realmente levanta o si hay un "crash" silencioso.

## 2. Análisis de Resultados
*   **Si tarda > 40s**: Confirmaremos que es un tema de rendimiento del entorno local (Docker/WSL) y simplemente debemos aumentar los timeouts en el frontend.
*   **Si es rápido (<10s) pero falla**: Confirmaremos un error en la comunicación Backend <-> Frontend.
*   **Si no levanta**: Confirmaremos un problema en la configuración del contenedor Evolution.

## 3. Implementación (Post-Análisis)
Una vez tengamos el dato duro del tiempo de inicio, procederé a re-aplicar la lógica de persistencia y diagnóstico en el código, ajustada a la realidad de tu entorno.