# Checklist de Calidad: Closer Studio

## Estándares de Código
- [ ] **Nombres de Archivos:** Kebab-case para archivos (`lead-card.tsx`), PascalCase para componentes.
- [ ] **Exportaciones:** Barriles (`index.ts`) usados correctamente en features.
- [ ] **Tipado:** No usar `any`. Interfaces definidas en `types/`.

## Arquitectura Backend
- [ ] **Separación de Responsabilidades:** `LeadModel` NO debe importar directamente `CustomerModel` si cruza límites de módulo (usar IDs), pero como es SQL Join, la relación ORM es aceptable si están en el mismo monolito. *Nota: En este proyecto usamos Monolito Modular, las FKs son permitidas.*
- [ ] **Transacciones:** La creación de Lead + Customer debe ser atómica.

## UX/UI
- [ ] **Loading States:** Skeletons visibles mientras carga la data del cliente.
- [ ] **Error Handling:** Si falla la carga del cliente, mostrar fallback en la tarjeta del lead.
- [ ] **Responsive:** El Kanban/Lista debe funcionar en móvil (quizás transformándose en lista vertical).

## Migración
- [ ] **Backup:** Backup de BD realizado antes de correr migraciones.
- [ ] **Idempotencia:** Los scripts de migración pueden correrse varias veces sin duplicar datos.
- [ ] **Verificación:** `SELECT count(*)` coincide antes y después de la migración.
