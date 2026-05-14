# Story 11 — Vitalia bootstrap

> **Outcome:** luana-platform-migration · **Sequence:** 11/14 · **Parallel-safe**

## What

Bootstrap brand `vitalia` (medical/dental/wellness clinics) consumiendo Luana v0.1.0+.

## Setup

1. Repo `luana-platform/vitalia` (skeleton from Story 1)
2. Clerk App #2 (Vitalia signup + JWT issuer)
3. K8s cluster + Postgres + Qdrant + Redis + LiteLLM Proxy svc
4. Domain (vitalia.health o similar)

## `vertical-medical/` package

Vertical-specific code (NO core):

### Tools (sales_agent + copilot extensions)
- `prepaid_payment_check` — verifica payment_status antes confirm booking
- `treatment_followup_check` — chequea adherencia tratamiento
- `medical_consent_request` — pide consentimiento informado pre-procedimiento
- `appointment_reschedule_with_doctor` — re-agenda con disponibilidad doctor

### Extractors (copilot)
- `MedicalKBExtractor` — extrae historia médica desde documentos PDF
- `DentalHistoryExtractor` — historia dental específica

### Workflows (copilot)
- `TreatmentFollowupWorkflow` — sigue plan tratamiento turn-by-turn

### Knowledge base packs
- `medical_kb_dental_v1` (dental terminology, procedures, common questions)
- `medical_kb_psychology_v1`
- `medical_kb_psychiatry_v1`

### Guardrails
- HIPAA-lite legal disclaimers en respuestas sensibles
- No diagnóstico LLM directo (referir a doctor)

### Channel adapters
- Payment gateway prepaid (Stripe Healthcare-flagged + MercadoPago + tokenized)

## BrandConfig

```python
LUANA_BRAND_CONFIG = {
    "name": "Vitalia",
    "domain": "vitalia.health",
    "theme_tokens": {...vitalia colors + fonts...},
    "features": {"voice_cloning": False},
    "brand_studio": {
        "enabled_sections": ["identity", "contact", "team", "testimonials"],
        "field_overrides": {"voice_archetype": {"required": False}},
    },
    "offer_studio": {"preset_pack": "medical_services_v1"},
    "scheduling": {"booking_policy": "vitalia_prepaid_required"},
    "plan_tiers": {
        "solo_doctor": {"price": 49, ...},
        "clinic": {"price": 199, ...},
        "multi_site": {"price": 599, ...},
    },
    "clerk_app": {"id": "VITALIA_CLERK_APP_ID", "publishable_key": "...", "secret_key_env": "VITALIA_CLERK_SECRET"},
    "sidebar_routes": [{"path": "/treatments", "label": "Tratamientos", "vertical_only": True}],
}
```

## Routes brand-specific (no core)

- `/treatments/` (CRUD treatments)
- `/treatments/{id}/followup` (treatment follow-up dashboard)
- `/medical-compliance` (admin)
- `/patients/` (CDP medical-flavor)

## Acceptance

- Vitalia deployed a su K8s cluster
- 2-3 clínicas piloto pueden signup + crear cuenta + completar Brand Studio simplificado + crear primera oferta `medical_services` + agendar booking con prepaid → cobrar → tener cita
- Sales agent responde correctamente con voz Vitalia (default archetype, no voice cloning)
- Compliance guardrails ON (smoke test prompt-injection)

## Effort: 25-35 tickets, ~3-4 sem (parallel)
