# Goldens — Dataset de evaluación del sales agent

Directorio de golden conversations: conversaciones curadas que sirven como
ground truth para la suite de evaluación del sales agent (Story D).

---

## 1. Descripción general

Los goldens son conversaciones sintéticas **curadas manualmente** que representan
el comportamiento esperado del sales agent ante distintos tipos de clientes.

### ¿Qué es un golden?

Un golden es un archivo YAML que contiene:

- La transcripción completa de una conversación simulada
- El resultado esperado (terminación, herramientas invocadas, voz de marca)
- Metadatos de generación y curaduría
- Restricciones declarativas (herramientas prohibidas por tipo de persona)

### Paradigma synthetic-first

Los goldens **no provienen de sesiones reales de producción**. Se generan via:

1. Simulador de conversaciones (Story B) con personas archetype-aware (Story C)
2. Curaduría manual por Chris: selección + validación de los mejores candidatos

Esta estrategia evita fuga de PII de clientes reales y garantiza reproducibilidad.

### Estructura del directorio

```
goldens/
├── README.md                     # Este archivo
├── _schema.py                    # GoldenScenarioModel v1 (Pydantic frozen)
├── _schema_migrations.py         # Registro de migraciones de schema
├── {tenant_slug}/
│   ├── happy/
│   │   └── {golden_id}.yaml      # Conversación exitosa
│   ├── nurture/
│   │   └── {golden_id}.yaml      # Conversación de nurturing (objeciones)
│   └── unqualified/
│       └── {golden_id}.yaml      # Prospecto no calificado
└── (visionarias-smoke-golden.yaml)  # Golden legacy del smoke runner Story B
```

### Matriz de cobertura (15 celdas mínimas)

| Tenant | happy | nurture | unqualified |
|---|---|---|---|
| `tenant_coach_lat` | ≥1 | ≥1 | ≥1 |
| `tenant_medicina_estetica` | ≥1 | ≥1 | ≥1 |
| `tenant_clinica_dental` | ≥1 | ≥1 | ≥1 |
| `tenant_agencia_growth_video` | ≥1 | ≥1 | ≥1 |
| `tenant_agencia_automatizacion_ia` | ≥1 | ≥1 | ≥1 |

El coverage gate (`test_goldens_coverage.py`) verifica esta cobertura en CI.

---

## 2. Pipeline de generación

El proceso tiene dos fases:

### Fase 1 — Generación de candidatos

```bash
# Generar candidatos para todos los tenants (75 celdas, ~$5.40 estimado)
python backend/scripts/generate_golden_candidates.py \
  --output-dir backend/tests/agentic_evals/sales_agent/_artifacts/goldens_generation/run-$(date +%Y%m%d)

# Solo un tenant (3 celdas, ~$0.22)
python backend/scripts/generate_golden_candidates.py \
  --tenant tenant_coach_lat \
  --runs-per-cell 1 \
  --output-dir /tmp/goldens-test
```

El script genera una tabla Markdown con todos los candidatos ordenados por
score de calidad. Chris revisa la tabla en el IDE para seleccionar los mejores.

### Fase 2 — Curaduría y promoción manual

```bash
# Promover un candidato a golden
python backend/scripts/promote_golden.py \
  --simulation-id <uuid-del-candidato> \
  --golden-id coach-lat-happy-001 \
  --artifact-dir backend/tests/agentic_evals/sales_agent/_artifacts/goldens_generation/run-20260508 \
  --actor-profile-id lead-frio-impaciente-pe \
  --notes "Seleccionado por manejo claro de objeciones de precio"
```

El script escribe el YAML en la ruta correcta
(`goldens/{tenant_slug}/{persona_kind}/{golden_id}.yaml`) con validación
automática del schema y auto-derivación de campos desde la simulación.

---

## 3. Cómo agregar o refrescar un golden

### Agregar un nuevo golden

1. Ejecutar `generate_golden_candidates.py` con los filtros deseados
2. Revisar la tabla Markdown de candidatos generada
3. Seleccionar el mejor candidato por quality score + cobertura de objeciones
4. Ejecutar `promote_golden.py` con el simulation-id elegido
5. Verificar que el YAML generado pasa validación:
   ```bash
   cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/test_goldens_schema.py -v
   ```
6. Verificar cobertura de 15 celdas:
   ```bash
   cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/test_goldens_coverage.py -v
   ```
7. Verificar ausencia de PII:
   ```bash
   python backend/scripts/scan_goldens_pii.py backend/tests/agentic_evals/sales_agent/goldens/
   ```
8. Commitear con mensaje convencional:
   ```
   feat(goldens): add {tenant_slug}-{persona_kind}-{n} golden
   ```

### Refrescar un golden existente

Los goldens son inmutables post-commit (D16). El proceso de refresco es:

1. Eliminar el golden obsoleto del directorio
2. Generar nuevos candidatos para esa celda
3. Promover el nuevo candidato con el mismo `golden_id` (o nuevo `golden_id`)
4. Verificar schema + cobertura + PII (pasos 5-8 de arriba)
5. Commitear ambos cambios en el mismo commit (delete + promote)

---

## 4. Política de actualización

Los goldens **solo se actualizan por trigger manual** (Chris). Nunca se
regeneran automáticamente en CI.

### Señales de refresco recomendadas

| Señal | Acción |
|---|---|
| Story C schema bump (actor_profile_schema_version > 2) | Regenerar todas las celdas afectadas |
| Grader voice_fidelity score satura > 0.95 en ≥ 3 celdas | Agregar goldens más desafiantes |
| Revisión semestral (6 meses desde última curaduría) | Revisar relevancia + refrescar si hay drift |
| Nuevo tenant seed agregado a Story A | Agregar 3 goldens para el nuevo tenant |
| Cambio mayor en `personality_profiles.system_instruction` | Revisar celdas del tenant afectado |

### Lo que NO dispara regeneración

- Cambios en la lógica del sales agent que no afecten la voz de marca
- Actualizaciones de dependencias de terceros
- Cambios en el schema de evaluación (Stories E/F/G/H) que no afecten el schema del golden

---

## 5. Referencia del schema

El schema completo está definido en `_schema.py` (Pydantic v2, frozen).

### Campos clave de `GoldenScenarioModel`

| Campo | Tipo | Descripción |
|---|---|---|
| `schema_version` | `Literal[1]` | Cement de versión. Bump via `_schema_migrations.py` |
| `id` | `str` (slug) | Identificador estable: `{tenant}-{kind}-{n}` |
| `tenant_slug` | `GoldenTenantSlug` | Uno de los 5 tenant seeds Story A |
| `persona_kind` | `GoldenPersonaKind` | `happy` / `nurture` / `unqualified` |
| `actor_profile_id` | `str` | ID de persona Story C (referential integrity) |
| `actor_profile_schema_version` | `Literal[2]` | Congelado en v2 (immune a bumps Story C) |
| `dialect_code` | `str` | BCP-47, debe coincidir con `ARCHETYPE_DIALECT_MAP[tenant_slug]` |
| `transcript` | `list[GoldenTurnModel]` | Conversación completa (mínimo 2 turnos) |
| `expected_termination_reason` | `GoldenTerminationReason` | `GOAL_COMPLETION` / `MAX_TURNS` / `CUSTOMER_EXIT` |
| `expected_voice_attributes` | `list[str]` | Atributos de voz auto-extraídos del perfil de personalidad |
| `expected_tools_invoked` | `list[str]` | Herramientas esperadas durante la conversación |
| `forbidden_tools` | `list[str]` | Herramientas prohibidas (D17: `unqualified` → 3 herramientas de cierre bloqueadas) |
| `metadata` | `GoldenMetadataModel` | Trazabilidad: simulation_id, seed, costo, notas Chris |

Para ver el schema completo con validaciones:

```python
from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel
print(GoldenScenarioModel.model_json_schema())
```

---

## 6. Presupuesto de costo

| Concepto | Estimado | Límite |
|---|---|---|
| Generación completa (75 celdas, 1 run/celda) | ~$5.40 USD | $8.00 USD (hard cap) |
| Generación 1 tenant (3 celdas, 1 run/celda) | ~$0.22 USD | N/A |
| Generación 1 celda | ~$0.072 USD | N/A |

El script `generate_golden_candidates.py` verifica el presupuesto **antes** de
realizar llamadas al LLM. Si el estimado supera el hard cap de $8.00, el script
termina con exit code 2 sin consumir créditos.

---

## 7. Coverage gate

El gate de cobertura (`test_goldens_coverage.py`) verifica en CI:

- **15 celdas mínimas**: cada combinación `(tenant_slug × persona_kind)` tiene ≥ 1 golden
- **Máximo 30 goldens**: saturation cap D2 (rendimientos decrecientes por τ-Bench research)
- **No early-exit**: cuando hay múltiples celdas vacías, el mensaje de error lista **todas** (D-A-11)

Para ver el estado actual de cobertura:

```bash
cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/test_goldens_coverage.py -v
```

---

## 8. PII — Defensa en profundidad

Los goldens tienen **cero tolerancia a PII**. La defensa tiene dos capas:

### Capa 1 — Pre-commit hook (Section 9)

Bloquea el commit si algún YAML staged en `goldens/` contiene PII detectado por
los patrones en `backend/scripts/_pii_patterns.py`:

- Email (RFC 5322)
- Teléfono internacional (LatAm: AR/MX/PE)
- DNI AR / CUIT AR
- RUT CL
- DNI PE (con context guards para falsos positivos)
- CURP MX / RFC MX
- URLs internas Nicolify

### Capa 2 — Architecture fitness gate (CI)

`tests/architecture/test_goldens_no_committed_pii.py` corre `scan_goldens_pii.py`
sobre todo el directorio `goldens/` en cada build de CI.

### Política de whitelist

**No existe whitelist** para goldens (D-A-4, D10). Todo PII detectado es un bug.
Resolución: reemplazar con datos sintéticos o regenerar el golden desde cero.

Los datos sintéticos recomendados:

| Tipo | Sintético |
|---|---|
| Nombre | "Cliente Ejemplo", "Usuario Prueba" |
| Teléfono | "+99 0 1234 5678" |
| Email | "usuario@example.com" |
| DNI AR | "11.111.111" (fuera del rango válido) |

Para escanear manualmente:

```bash
python backend/scripts/scan_goldens_pii.py backend/tests/agentic_evals/sales_agent/goldens/
# Exit 0 = limpio | Exit 1 = PII detectado | Exit 2 = error de parseo
```
