# Plan de Limpieza y Mantenibilidad

Este plan aborda la eliminación de archivos en desuso y la consolidación de código duplicado detectado durante la revisión.

## 1. Deprecación de Scripts Raíz
Se renombrarán los siguientes scripts de utilidad que no tienen referencias en el código base ni en la configuración de Docker:
- `debug_traces.py` -> `debug_traces.py.deprecated`
- `debug_session.py` -> `debug_session.py.deprecated`
- `debug_embeddings.py` -> `debug_embeddings.py.deprecated`
- `debug_db.py` -> `debug_db.py.deprecated`
- `fix_db.py` -> `fix_db.py.deprecated`
- `seed_db.py` -> `seed_db.py.deprecated`

## 2. Eliminación de Código Duplicado
Se ha detectado que `src/services/whatsapp.py` es una implementación redundante y sin uso (no importada en ninguna parte), mientras que la implementación robusta reside en `src/channels/whatsapp.py`.
- Renombrar `src/services/whatsapp.py` -> `src/services/whatsapp.py.deprecated` para evitar confusión futura.

## 3. Recomendaciones Adicionales (Sin cambios automáticos)
- **Enums para Estados:** En `src/services/repository.py`, los estados del funnel ("S1_Rapport", "awareness") están "hardcoded". Se recomienda crear un Enum en `src/core/schema.py` para tipado fuerte.
- **Tipado Estricto:** Completar los type hints de retorno en métodos de `Repository`.
