# Auditoría del Offer Studio (Enfoque Offer Ladder)
> **Alcance:** Offer Studio (Sistema de Ofertas y Value Ladder) para Microempresarios y Solopreneurs.
> **Fecha:** 24 de Marzo de 2026
> **Marcos de Referencia (Frameworks) Aplicados:** 
> - Value Ladder (Brunson) [PRIMARY]
> - Grand Slam Offer (Hormozi) [PRIMARY]
> - Impact & Critical Event (Winning by Design) [PRIMARY]
> - Productization (Casel) [SECONDARY]

## Resumen Ejecutivo
El **Offer Studio** actual tiene una base estructural excelente: la clasificación en 7 niveles (`OfferValueLevel` de 0 a 6) y el soporte polimórfico (`OfferType` y `*Details`) construyen un esqueleto sólido para la metodología "Offer Ladder". Sin embargo, **trata a las ofertas como productos aislados en lugar de una escalera psicológica conectada**. Para un solopreneur, el sistema actual carece de mecanismos para definir *límites estrictos* (scope creep), *superar la inercia del cliente* (eventos críticos) y *forzar la ascensión activa* (puentes lógicos entre un nivel y el siguiente). Esto limita drásticamente la capacidad de un agente de ventas (SDR) para cerrar ventas con urgencia y hacer *upselling* de manera natural.

---

## Hallazgos y Oportunidades de Mejora

### CRÍTICO — El Agente de Ventas (SDR) no puede funcionar sin esto

- [ ] **[C-01] Ausencia de Mecanismos de Ascensión en la Escalera de Valor** (Framework: Brunson)
  - **Brecha**: Actualmente existen `upsell_offer_id` y `downsell_offer_id`, pero no hay un "puente lógico". Sabemos *qué* vender después, pero no *por qué* ni *cuándo*.
  - **Impacto**: El SDR intentará hacer *cross-sell* de manera forzada. En la metodología Offer Ladder, la compra del Nivel N debe crear o revelar el problema que resuelve el Nivel N+1.
  - **Recomendación**: Añadir campos `ascension_trigger` (Ej: "El cliente ya validó su oferta pero ahora no tiene tiempo para entregarla") y `ascension_pitch` (El guion o ángulo de transición) al modelo base de `Offer`.
  - **Archivos Afectados**: `backend/src/modules/offer/domain/offer.py`, `frontend/src/features/offer-studio/types/schema.ts`

- [ ] **[C-02] Falta de Evento Crítico y Costo de Inacción (Urgencia)** (Framework: WbD)
  - **Brecha**: El sistema captura `marketing_pain_points` y `marketing_desires`, pero omite el "Trigger". ¿Por qué el cliente compraría *hoy* y no en 3 meses?
  - **Impacto**: Sin un evento crítico, el SDR no puede generar urgencia genuina. El prospecto dirá "Lo pensaré" y el agente no tendrá munición lógica para rebatir.
  - **Recomendación**: Añadir `critical_event_triggers: List[str]` (Ej: "Se acerca la temporada de impuestos", "Acaba de perder un cliente clave") y `cost_of_inaction: str` al esquema de psicología de la oferta. Modificar el prompt de generación de psicología para extraer esto.
  - **Archivos Afectados**: `backend/src/modules/offer/domain/offer.py`, `frontend/src/features/offer-studio/types/schema.ts`, `offer_psychology_generator.j2`

### ALTO — Degradación Significativa de Calidad

- [ ] **[H-01] Falta de Ecuación de Valor: Esfuerzo y Sacrificio** (Framework: Hormozi)
  - **Brecha**: La ecuación de Hormozi es: *(Resultado Soñado x Probabilidad) / (Tiempo x Esfuerzo)*. Tenemos `primary_outcome` y `time_to_value`, pero falta el Esfuerzo.
  - **Impacto**: Un solopreneur vende frecuentemente servicios DFY (Done For You). El SDR no puede contrastar el enorme valor de un servicio High-Ticket vs un curso barato si no puede articular *lo que el cliente se ahorra de hacer*.
  - **Recomendación**: Añadir `effort_mitigated` o `sacrifice_avoided: List[str]` (Ej: "No tienes que aprender a programar", "No pasas horas editando video").
  - **Archivos Afectados**: `backend/src/modules/offer/domain/offer.py`

- [ ] **[H-02] Límites de Alcance (Scope Creep) en Servicios Productizados** (Framework: Casel)
  - **Brecha**: El esquema `ServiceDetails` incluye `deliverables_list`, pero omite las exclusiones.
  - **Impacto**: El mayor enemigo de un microempresario que vende servicios es el "scope creep" (trabajo extra no pagado). Si el SDR no sabe qué está *fuera* de la oferta, puede prometer cosas que arruinarán el margen del emprendedor.
  - **Recomendación**: Añadir `out_of_scope_items: List[str]` al modelo `ServiceDetails`.
  - **Archivos Afectados**: `backend/src/modules/offer/domain/details.py`, `frontend/src/features/offer-studio/types/schema.ts`

### MEDIO — Oportunidad de Mejora Estructural

- [ ] **[M-01] Carencia de "Proof Stack" (Prueba Social Específica)** (Framework: Hormozi / Keller)
  - **Brecha**: La autoridad de marca general existe, pero no hay un campo para la "Probabilidad de Éxito" percibida *específica* de esta oferta.
  - **Impacto**: Hace que las ofertas High-Ticket sean difíciles de justificar para el SDR sin casos de estudio precisos.
  - **Recomendación**: Añadir `proof_stack: List[str]` (Ej: "300 alumnos graduados", "Promedio de 3x ROI en 30 días") en `Offer`.

---

## Matriz de Cobertura Metodológica

| Framework | Peso | Cobertura | Brechas Clave |
|-----------|--------|----------|----------|
| **Value Ladder (Brunson)** | PRIMARY | 4/6 Elementos | Faltan "Triggers" de ascensión y lógica de continuidad explícita. |
| **Grand Slam (Hormozi)** | PRIMARY | 3/5 Elementos | Falta métrica de Esfuerzo/Sacrificio y Probabilidad Percibida. |
| **Impact & Event (WbD)** | PRIMARY | 1/4 Elementos | Falta el Evento Crítico, Impacto Racional e Impacto Emocional. |
| **Productization (Casel)** | SECONDARY | 4/5 Elementos | Faltan Exclusiones (Out of Scope) estrictas. |

---

## Score de Preparación del Agente SDR

Si el Agente SDR solo tuviera estos campos para cerrar una venta hoy:

| Pregunta del SDR | ¿Respondible? | Campo(s) Origen | Brecha a Cubrir |
|-------------|-------------|-----------------|-----|
| "¿Con quién estoy hablando?" | SÍ | `target_avatar_match` | Ninguna. |
| **"¿Cuál es su trigger para comprar HOY?"** | **NO** | - | Falta `critical_event_triggers`. |
| "¿Qué está en juego si no actúan?" | PARCIAL | `marketing_pain_points` | Falta `cost_of_inaction` (Impacto explícito). |
| "¿Qué estoy vendiendo exactamente?" | SÍ | `primary_outcome`, `deliverables` | Ninguna. |
| **"¿Por qué deberían creer que esto funciona?"**| **NO** | - | Falta `proof_stack` de la oferta. |
| "¿Qué objeciones pondrán?" | SÍ | `objections` | Ninguna (excelente implementación actual). |
| **"¿Cómo creo urgencia?"** | **NO** | - | Depende del evento crítico faltante. |
| "¿Cuál es el proceso post-venta?" | SÍ | `onboarding_action` | Ninguna. |

**Score General de SDR: 5/8 preguntas completamente respondibles.**

---

## Próximos Pasos (Priorizados para el Equipo de Desarrollo)

1. **[C-02] Urgencia y Ventas:** Agregar `critical_event_triggers` y `cost_of_inaction` en la entidad `Offer` y ajustar el prompt en `offer_psychology_generator.j2` para que la IA extraiga el "Por qué comprar ahora".
2. **[H-02] Protección del Solopreneur:** Agregar `out_of_scope_items` (Lo que NO incluye) al `ServiceDetails` para proteger el tiempo del microempresario frente al agente de ventas.
3. **[C-01] Conectar la Escalera:** Implementar `ascension_trigger` en la oferta para dar contexto al `upsell_offer_id`, dándole al SDR un motivo conversacional natural para vender el siguiente peldaño de la escalera.
4. **[H-01] Ecuación Hormozi Completa:** Introducir campos de mitigación de esfuerzo (`effort_mitigated`) para contrastar ofertas DIY (hazlo tú mismo) vs DFY (hecho por ti).
