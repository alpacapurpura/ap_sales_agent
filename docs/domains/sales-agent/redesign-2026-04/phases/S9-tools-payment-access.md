# S9 · Tools: Payment lifecycle + grant access

## Objetivo

Sales_agent vende: genera link de pago per lead+offer, verifica si pagó (push o pull), otorga acceso automático cuando paid (key/link/código vía `connections`). Mercado Pago, Stripe, otros via strategy pattern. Idempotencia natural + auditoría completa.

## Dependencias

- S7 (voz de marca para mensajes).
- S8 cerrado (algunos flows mezclan booking + payment — ej: pagar y agendar).

## Criterios de éxito

1. Tools en `sales_agent/application/tools/payment/`:
   - `create_payment_link(lead_id, offer_id, amount, currency, channel)` → URL + payment_id.
   - `verify_payment_status(lead_id, payment_id)` → status enum.
   - `grant_access(lead_id, offer_id, payment_id)` — gates: payment must be PAID. Atomic.
2. Webhook IN providers (Mercado Pago, Stripe) → `PaymentStatusChangedEvent`.
3. Cron `verify_pending_payments_task` para race / webhook miss.
4. `grant_access` invoca `connections` module para entregar:
   - Email con credenciales / link de acceso
   - Activar flujo Manychat de bienvenida
   - Crear acceso en plataforma cliente (LMS / member area)
   - Etc. — plug per `AccessProvider`.
5. Idempotency natural key: `(tenant_id, lead_id, offer_id, payment_id)`. Partial unique index.
6. Closer Studio muestra payment status + access status per lead.
7. Mensajes en voz de marca (consume slot 4).
8. Spanish neutro LATAM default.
9. Tests + arch tests + quality gates verdes.
10. Auditoría: `payment_grant_audit` table (append-only).

## Research mandate

### Queries WebSearch obligatorias

1. `Mercado Pago API checkout preference 2026 webhook IPN signature verification` — endpoint vigente + auth.
2. `Stripe Payment Links API 2026 metadata lead tracking webhook signature` — equivalente.
3. `payment idempotency key best practice SaaS 2026` — patterns.
4. `LATAM payment provider comparison 2026 Pix Mercado Pago Mach Khipu` — providers regionales.
5. `granting digital product access automation post-payment LATAM` — UX best practice.

### Tessl tiles

- N/A primaria. Si query identifica librería oficial Mercado Pago → instalar.

### Lectura obligatoria

- Aprendizajes S7, S8.
- `backend/src/modules/sales_agent/application/agents/sales/enrollment_tools.py` — patrón existente.
- `backend/src/modules/sales_agent/domain/enrollment.py`.
- `backend/src/modules/sales_agent/api/enrollments.py`.
- `backend/src/modules/connections/` — cómo entregar acceso.
- `backend/src/modules/offer/` — qué define una offer (precio, currency, access type).

### Hallazgos research

> COMPLETAR.

---

## Diseño

### `PaymentProvider` Protocol

```python
class PaymentProvider(Protocol):
    async def create_payment_link(...) -> PaymentLink: ...
    async def verify_payment(payment_id: str) -> PaymentStatus: ...
    async def parse_webhook(payload, signature) -> PaymentEvent: ...

PROVIDERS: dict[str, PaymentProvider] = {
    "mercado_pago": MercadoPagoProvider(),
    "stripe": StripeProvider(),
    # add: pix, khipu, ...
}
```

### Tool `create_payment_link`

```python
@tool
async def create_payment_link(
    lead_id: UUID,
    offer_id: UUID,
    channel: str | None = None,
) -> dict:
    """Crea link de pago para que el lead compre la oferta."""
    tenant_id = get_tenant_id()
    offer = await offer_repo.get(tenant_id, offer_id)
    provider = payment_provider_for_tenant(tenant_id)
    link = await provider.create_payment_link(
        amount=offer.price, currency=offer.currency,
        metadata={"tenant_id": tenant_id, "lead_id": lead_id, "offer_id": offer_id},
    )
    await payment_link_repo.upsert(...)  # idempotency natural key
    await event_bus.publish(PaymentLinkCreatedEvent.create(...))
    return link.as_tool_response()
```

### Tool `grant_access`

```python
@tool
async def grant_access(
    lead_id: UUID,
    offer_id: UUID,
    payment_id: UUID,
) -> dict:
    """Gates: payment must be PAID. Atómico via locked row + idempotency."""
    tenant_id = get_tenant_id()
    async with db.transaction():
        payment = await payment_repo.get_for_update(payment_id, tenant_id)
        if payment.status != PaymentStatus.PAID:
            return {"granted": False, "reason": f"payment_status={payment.status}"}
        existing = await access_audit_repo.get(
            tenant_id, lead_id, offer_id, payment_id,
        )
        if existing:  # idempotency
            return {"granted": True, "audit_id": existing.id, "duplicate": True}
        access_provider = access_provider_for_offer(offer)  # email / manychat / lms / ...
        delivery = await access_provider.deliver(lead_id, offer_id)
        audit = await access_audit_repo.create(...)
        await event_bus.publish(AccessGrantedEvent.create(...))
        return {"granted": True, "audit_id": audit.id, "delivery": delivery}
```

### Webhook IN

```python
@router.post("/webhooks/payment/{provider}")
async def payment_webhook(provider: str, payload: bytes, signature: str = Header(...)):
    parsed = PROVIDERS[provider].parse_webhook(payload, signature)
    # signature verification mandatory
    await event_bus.publish(PaymentStatusChangedEvent.create(
        tenant_id=parsed.tenant_id, payment_id=parsed.payment_id,
        new_status=parsed.status, occurred_at=parsed.when,
    ))
```

### Subscriber: auto-grant on PAID

```python
@subscribes_to(PaymentStatusChangedEvent)
async def auto_grant_on_paid(event):
    if event.new_status == PaymentStatus.PAID:
        # Invoca grant_access tool
        ...
```

NOTA: auto-grant es opt-in per offer (`offer.auto_grant_on_payment`). Algunas ofertas requieren verificación humana antes.

### Audit table

```sql
CREATE TABLE IF NOT EXISTS payment_grant_audit (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    lead_id UUID NOT NULL,
    offer_id UUID NOT NULL,
    payment_id UUID NOT NULL,
    delivery_method TEXT NOT NULL,  -- email / manychat / lms / ...
    delivery_payload JSONB,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    granted_by TEXT NOT NULL  -- 'auto' / user_id si manual
);
CREATE UNIQUE INDEX uq_payment_grant_natural_key ON payment_grant_audit(
    tenant_id, lead_id, offer_id, payment_id
);
```

Idempotency natural key.

---

## Plan TDD

### RED tests

1. `tests/modules/sales_agent/tools/payment/test_create_payment_link.py`:
   - MP provider devuelve link con metadata correcta.
   - Idempotency: 2x mismo lead+offer → mismo link si pendiente.

2. `tests/modules/sales_agent/tools/payment/test_grant_access_idempotent.py`:
   - 2x grant_access → solo 1 audit row.
   - 2x → solo 1 access delivery.
   - Payment NOT PAID → grant returns {granted: False}.

3. `tests/modules/sales_agent/api/test_payment_webhooks.py`:
   - MP webhook con signature válida → event published.
   - Signature inválida → 401.
   - Replay → idempotent (no double event).

4. `tests/modules/sales_agent/workers/test_verify_pending_payments.py`:
   - Pull provider state si webhook missed.

5. `tests/modules/sales_agent/test_auto_grant_on_paid.py`:
   - Offer con auto_grant=true → access granted on PAID.
   - Offer con auto_grant=false → no auto, requiere human.

6. `tests/architecture/test_payment_audit_immutable.py`:
   - No UPDATE en `payment_grant_audit` table.
   - No DELETE excepto retention worker.

---

## Implementación step-by-step

1. `PaymentProvider` Protocol + dataclasses.
2. MercadoPagoProvider (research first).
3. StripeProvider.
4. Migración: `payment_link`, `payment_grant_audit` tables.
5. Tools `create_payment_link`, `verify_payment_status`, `grant_access`.
6. Webhook endpoints con signature verification.
7. Cron `verify_pending_payments_task`.
8. Subscriber `auto_grant_on_paid`.
9. Extender `connections` para `AccessProvider` interface.
10. Closer Studio FE: payment + access tabs.
11. Smoke live: MP sandbox → pagar → verify auto-grant.

---

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Webhook signature spoof | Mandatory verification. Test invalid signature → 401. |
| Race: webhook + cron verify entregan acceso 2x | Idempotency unique index. Test cobertura. |
| Currency mismatch (offer USD, MP cobra ARS) | Resolver currency desde `offer` SSoT, NO inferir. Document FX. |
| `grant_access` falla parcial (email enviado pero LMS down) | Distributed transaction NO usar; saga pattern: deliver atomic + retry per channel. |
| PII en webhooks (CC last4, etc.) | Sanitize antes de loggear / persistir. |
| Provider rate limits | Backoff + queue. Use ARQ retries con exponential. |

---

## Tech debt watchpoints

- Si `connections` no expone `deliver_access(channel, lead, payload)` semantics → coordinar.
- Si `enrollment_tools.py` ya hace algo similar → DRY: refactor a esta capa o flag.
- Si `offer` no tiene campo `access_type` → escalar (no hardcodear).
- Si tenant config payment tokens no encryption-at-rest → CRITICAL.

---

## Ajustes vs plan original

> COMPLETAR.
