# Solución Integral de Arquitectura y Dependencias

He realizado una auditoría completa de tu código frontend (`components/ui`, `layout`, etc.) y he identificado todas las dependencias faltantes que están causando el "bucle de errores".

## 1. Auditoría de Dependencias
Al escanear tus archivos `.tsx` y compararlos con `package.json`, encontré las siguientes discrepancias:

| Componente | Dependencia Requerida | Estado Actual | Acción |
| :--- | :--- | :--- | :--- |
| `Tooltip` | `@radix-ui/react-tooltip` | **Faltante** | Agregar |
| `Separator` | `@radix-ui/react-separator` | **Faltante** | Agregar |
| `Sheet` | `@radix-ui/react-dialog` | Instalada | Ninguna |
| `Accordion` | `@radix-ui/react-accordion` | Instalada | Ninguna |
| `Dialog` | `@radix-ui/react-dialog` | Instalada | Ninguna |
| `ScrollArea` | `@radix-ui/react-scroll-area` | Instalada | Ninguna |
| `Tabs` | `@radix-ui/react-tabs` | Instalada | Ninguna |
| `Avatar` | `@radix-ui/react-avatar` | Instalada | Ninguna |

## 2. Plan de Ejecución
Para resolver esto de raíz y evitar que vuelva a suceder:

1.  **Actualización Masiva de `package.json`**:
    - Agregaré `@radix-ui/react-tooltip` y `@radix-ui/react-separator` directamente a tu archivo de configuración.

2.  **Implementación de Workflow Robusto (Makefile)**:
    - Crearé un archivo `Makefile` en la raíz del proyecto.
    - **Por qué**: Docker y tu Host tienen carpetas `node_modules` aisladas. Si instalas en uno, falta en el otro. El Makefile sincronizará ambos con un solo comando.
    - **Comando Nuevo**: `make install-front p=paquete` (Instala en ambos lugares automáticamente).
    - **Comando de Rescate**: `make fix-front` (Re-sincroniza todo si pierdes trazabilidad).

## 3. Resultado Esperado
- El error de compilación desaparecerá inmediatamente.
- Tendrás un mecanismo estándar (`make`) para instalar librerías futuras sin romper el entorno.
