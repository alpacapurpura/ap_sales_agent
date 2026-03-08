# Reglas de Comentarios en el Código para IA
- **Prohibido explicar sintaxis:** Nunca expliques funciones estándar del lenguaje o framework. Asume un lector con nivel Senior.
- **Enfócate en el "Por Qué":** Comenta EXCLUSIVAMENTE razones de negocio, decisiones arquitectónicas o lógicas no convencionales.
- **Documenta lo invisible:** Detalla casos límite (edge cases), parches temporales o limitaciones de APIs externas.
- **Etiquetas obligatorias:** Usa prefijos explícitos para alertar al desarrollador y al motor de búsqueda: `// WORKAROUND:`, `// CONTEXTO:`, `// HACK:`, `// DEBT:`.
- **Docstrings tácticos:** Usa JSDoc/Docstrings (o equivalente) ÚNICAMENTE para interfaces públicas, endpoints y utilidades core compartidas, detallando el propósito general para la indexación RAG.
- **Cero código comentado:** Prohibido dejar bloques de código muerto o comentado (`// const test = ...`). Bórralo; para eso existe Git.
- **Actualización estricta:** Si modificas una línea de código, es tu obligación absoluta actualizar o eliminar los comentarios adyacentes si ya no aplican.