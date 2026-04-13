# Phase 3: Interview in Sidebar + Offer Creation with IA

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire interview card callbacks (currently no-ops), add dynamic interview config by archetype, inject intelligence rules into the interview prompt, add "Crear con asistente IA" to the offer wizard, make interview pages redirect to sidebar, and add focus-mode awareness to WithCopilot.

**Architecture:** Frontend callbacks delegate to existing `sendCardAction()` in `useCopilotChat`. Backend generates archetype-specific interview configs at `startInterview` time. Intelligence rules are appended to the existing `copilot_interview.j2` template. The offer wizard creates the offer in DB, navigates to the editor, and activates interview in sidebar via store actions.

**Tech Stack:** React 18, Zustand, Next.js App Router, FastAPI, Jinja2 templates, Pydantic v2, pytest, Vitest

---

## File Map

### Frontend (modify)
- `frontend/src/features/copilot/components/messages/AssistantMessage.tsx` — wire card callbacks
- `frontend/src/features/copilot/hooks/useCopilotChat.ts` — add `sendCheckpointAction` helper
- `frontend/src/features/copilot/components/cards/interview-complete-card.tsx` — sidebar-aware redirect
- `frontend/src/features/offer-studio/components/wizard/CreateOfferWizard.tsx` — add "Crear con asistente IA" button + callback prop
- `frontend/src/features/offer-studio/components/dashboard/offer-studio-dashboard.tsx` — handle IA creation flow
- `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/interview/page.tsx` — redirect to sidebar
- `frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/interview/page.tsx` — redirect to sidebar
- `frontend/src/features/copilot/components/WithCopilot.tsx` — focus-mode AI badge

### Backend (modify)
- `backend/src/modules/copilot/domain/interview_config.py` — add `get_offer_interview_config()` factory
- `backend/src/modules/copilot/domain/interview_configs/offer_config.py` — archetype-specific blocks
- `backend/src/modules/copilot/application/services/interview_service.py` — use dynamic config for offer domain
- `backend/src/modules/copilot/infrastructure/prompts/templates/copilot_interview.j2` — intelligence rules

### Tests
- `frontend/src/features/copilot/components/messages/__tests__/AssistantMessage.test.tsx`
- `frontend/src/features/copilot/components/__tests__/WithCopilot.test.tsx`
- `frontend/src/features/offer-studio/components/wizard/__tests__/CreateOfferWizard.test.tsx`
- `backend/tests/modules/copilot/test_interview_config.py`
- `backend/tests/modules/copilot/test_interview_service.py`

---

## Task 1: Wire AlternativesCard & ClarifyCard callbacks

**Files:**
- Modify: `frontend/src/features/copilot/components/messages/AssistantMessage.tsx:78-108`
- Test: `frontend/src/features/copilot/components/messages/__tests__/AssistantMessage.test.tsx`

The `AssistantMessage` component renders interview cards with no-op callbacks. We need to accept `sendCardAction` as a prop and wire it to each card. The parent passes it from `useCopilotChat`.

- [ ] **Step 1: Write test for AlternativesCard callback wiring**

Create `frontend/src/features/copilot/components/messages/__tests__/AssistantMessage.test.tsx`:

```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AssistantMessage } from "../AssistantMessage";
import type { CopilotMessage } from "../../../store/copilot-store";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "test-tenant" }),
}));

function makeMessage(overrides: Partial<CopilotMessage> = {}): CopilotMessage {
  return {
    id: "msg-1",
    role: "assistant",
    content: "Test message",
    timestamp: Date.now(),
    ...overrides,
  };
}

describe("AssistantMessage card callbacks", () => {
  it("calls sendCardAction with selected alternative text", () => {
    const sendCardAction = vi.fn();
    const msg = makeMessage({
      uiActions: [
        {
          type: "alternatives_card",
          question: "Pick one",
          alternatives: [
            { id: "a1", title: "Option A", description: "Desc A" },
            { id: "a2", title: "Option B", description: "Desc B" },
          ],
          allow_custom: false,
          card_status: "pending",
        },
      ],
    });

    render(<AssistantMessage message={msg} sendCardAction={sendCardAction} />);

    // Select option A
    fireEvent.click(screen.getByText("Option A"));
    // Click "Seleccionar"
    fireEvent.click(screen.getByRole("button", { name: /seleccionar/i }));

    expect(sendCardAction).toHaveBeenCalledWith("msg-1", 0, "Selecciono: Option A");
  });

  it("calls sendCardAction with clarify resolution", () => {
    const sendCardAction = vi.fn();
    const msg = makeMessage({
      uiActions: [
        {
          type: "clarify_card",
          clarify_items: [
            { field_path: "field.x", issue: "Ambiguous", options: ["Yes", "No"] },
          ],
          card_status: "pending",
        },
      ],
    });

    render(<AssistantMessage message={msg} sendCardAction={sendCardAction} />);
    fireEvent.click(screen.getByText("Yes"));

    expect(sendCardAction).toHaveBeenCalledWith("msg-1", 0, "Yes");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/copilot/components/messages/__tests__/AssistantMessage.test.tsx`
Expected: FAIL — `sendCardAction` prop doesn't exist yet.

- [ ] **Step 3: Add sendCardAction prop and wire AlternativesCard + ClarifyCard**

In `frontend/src/features/copilot/components/messages/AssistantMessage.tsx`:

Add `sendCardAction` to the props interface:
```tsx
interface AssistantMessageProps {
  message: CopilotMessage;
  isStreaming?: boolean;
  sendCardAction?: (messageId: string, actionIndex: number, text: string) => void;
}
```

Update the function signature:
```tsx
export function AssistantMessage({ message, isStreaming, sendCardAction }: AssistantMessageProps) {
```

Replace AlternativesCard no-ops (lines 92-93):
```tsx
onSelect={(altId) => {
  const alt = action.alternatives?.find((a) => a.id === altId);
  if (alt && sendCardAction) {
    sendCardAction(message.id, idx, `Selecciono: ${alt.title}`);
  }
}}
onCustom={() => {
  if (sendCardAction) {
    sendCardAction(message.id, idx, "Prefiero otra opción personalizada");
  }
}}
```

Replace ClarifyCard no-op (line 106):
```tsx
onResolve={(resolution) => {
  if (sendCardAction) {
    sendCardAction(message.id, idx, resolution);
  }
}}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/copilot/components/messages/__tests__/AssistantMessage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/copilot/components/messages/AssistantMessage.tsx frontend/src/features/copilot/components/messages/__tests__/AssistantMessage.test.tsx
git commit -m "feat(copilot): wire AlternativesCard and ClarifyCard callbacks in AssistantMessage"
```

---

## Task 2: Wire CheckpointCard callbacks

**Files:**
- Modify: `frontend/src/features/copilot/components/messages/AssistantMessage.tsx:119-120`
- Modify: `frontend/src/features/copilot/hooks/useCopilotChat.ts`
- Test: `frontend/src/features/copilot/components/messages/__tests__/AssistantMessage.test.tsx`

CheckpointCard needs two actions: "confirm" (advance block) and "revise" (go back). Confirm uses `sendCardAction` with status "confirmed". Revise uses status "revising".

- [ ] **Step 1: Add checkpoint tests**

Append to `AssistantMessage.test.tsx`:

```tsx
describe("CheckpointCard callbacks", () => {
  it("calls sendCardAction with confirmed status on confirm", () => {
    const sendCardAction = vi.fn();
    const msg = makeMessage({
      uiActions: [
        {
          type: "checkpoint_card",
          block_id: "promise",
          block_label: "Promesa",
          summary: { headline: "Test" },
          health_score: 75,
          blocks_progress: { completed: 2, total: 6 },
          card_status: "pending",
        },
      ],
    });

    render(<AssistantMessage message={msg} sendCardAction={sendCardAction} />);
    fireEvent.click(screen.getByRole("button", { name: /perfecto, sigamos/i }));

    expect(sendCardAction).toHaveBeenCalledWith("msg-1", 0, "Confirmo, sigamos al siguiente bloque");
  });

  it("calls sendCardAction with revise text on revise", () => {
    const sendCardAction = vi.fn();
    const msg = makeMessage({
      uiActions: [
        {
          type: "checkpoint_card",
          block_id: "promise",
          block_label: "Promesa",
          summary: { headline: "Test" },
          health_score: 75,
          blocks_progress: { completed: 2, total: 6 },
          card_status: "pending",
        },
      ],
    });

    render(<AssistantMessage message={msg} sendCardAction={sendCardAction} />);
    fireEvent.click(screen.getByRole("button", { name: /ajustar algo/i }));

    expect(sendCardAction).toHaveBeenCalledWith("msg-1", 0, "Quiero ajustar algo en este bloque");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/copilot/components/messages/__tests__/AssistantMessage.test.tsx`
Expected: FAIL — checkpoint callbacks still no-ops.

- [ ] **Step 3: Wire CheckpointCard callbacks**

In `AssistantMessage.tsx`, replace the checkpoint no-ops (lines 119-120):

```tsx
onConfirm={() => {
  if (sendCardAction) {
    sendCardAction(message.id, idx, "Confirmo, sigamos al siguiente bloque");
  }
}}
onRevise={() => {
  if (sendCardAction) {
    sendCardAction(message.id, idx, "Quiero ajustar algo en este bloque");
  }
}}
```

Also update `useCopilotChat.ts` — in `_handleUIAction`, add checkpoint-specific handling to update `interviewProgress` when a checkpoint is confirmed:

```tsx
// In _handleUIAction switch, add before default:
case "checkpoint_card":
  store.addUIActionToLastAssistant(action);
  // Update interview progress from checkpoint data
  if (action.blocks_progress) {
    const currentProgress = store.interviewProgress;
    if (currentProgress) {
      store.setInterviewProgress({
        ...currentProgress,
        blocksCompleted: [
          ...currentProgress.blocksCompleted.slice(0, action.blocks_progress.completed),
        ],
      });
    }
  }
  return;
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/copilot/components/messages/__tests__/AssistantMessage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/copilot/components/messages/AssistantMessage.tsx frontend/src/features/copilot/hooks/useCopilotChat.ts frontend/src/features/copilot/components/messages/__tests__/AssistantMessage.test.tsx
git commit -m "feat(copilot): wire CheckpointCard confirm/revise callbacks"
```

---

## Task 3: Pass sendCardAction from chat container to AssistantMessage

**Files:**
- Modify: the component that renders `<AssistantMessage>` — find and wire `sendCardAction` from `useCopilotChat()`

The `AssistantMessage` now accepts `sendCardAction` but the parent that renders it must pass it. Find where `AssistantMessage` is rendered and wire the prop.

- [ ] **Step 1: Find where AssistantMessage is rendered**

Run: `cd frontend && npx grep -rn "AssistantMessage" src/features/copilot/components/ --include="*.tsx" | grep -v "__tests__" | grep -v "messages/AssistantMessage"`

Look for the parent component — likely `CopilotChat.tsx` or similar. It should already call `useCopilotChat()` which returns `sendCardAction`.

- [ ] **Step 2: Wire sendCardAction prop**

In the parent component that renders `<AssistantMessage>`, destructure `sendCardAction` from `useCopilotChat()` and pass it:

```tsx
const { sendMessage, sendCardAction, stopStreaming } = useCopilotChat();

// ... in the render:
<AssistantMessage
  message={msg}
  isStreaming={isStreaming && idx === messages.length - 1}
  sendCardAction={sendCardAction}
/>
```

- [ ] **Step 3: Run frontend type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS (no type errors)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/copilot/components/
git commit -m "feat(copilot): pass sendCardAction from chat container to AssistantMessage"
```

---

## Task 4: Make InterviewCompleteCard sidebar-aware

**Files:**
- Modify: `frontend/src/features/copilot/components/cards/interview-complete-card.tsx`

Currently the card always says "Ver Brand Studio" with a hard-coded label. It should be domain-aware and in sidebar mode it should clear interview state + close expanded sidebar instead of navigating.

- [ ] **Step 1: Update InterviewCompleteCard**

Replace the content of `frontend/src/features/copilot/components/cards/interview-complete-card.tsx`:

```tsx
"use client";

import { useRouter, useParams } from "next/navigation";
import { useCopilotStore } from "../../store/copilot-store";

interface InterviewCompleteCardProps {
  healthScore: number;
  redirect: string;
}

const DOMAIN_LABELS: Record<string, string> = {
  "/brand-studio": "Brand Studio",
  "/offer-studio": "Offer Studio",
};

export function InterviewCompleteCard({ healthScore, redirect }: InterviewCompleteCardProps) {
  const router = useRouter();
  const params = useParams();
  const tenantId = params.tenantId as string;
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const clearInterview = useCopilotStore((s) => s.clearInterview);

  const label = DOMAIN_LABELS[redirect] ?? "el editor";

  const handleClick = () => {
    clearInterview();
    setSidebarState("open");
    router.push(`/${tenantId}${redirect}`);
  };

  return (
    <div className="rounded-xl border border-green-500 bg-green-900/20 p-4 text-center">
      <div className="text-2xl font-bold text-green-500">{healthScore}%</div>
      <div className="mt-1 text-xs text-green-400">¡Tu perfil está completo!</div>
      <button
        onClick={handleClick}
        className="mt-3 rounded-md bg-green-600 px-4 py-2 text-xs font-medium text-white hover:bg-green-700"
      >
        Ver {label} →
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Run type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/copilot/components/cards/interview-complete-card.tsx
git commit -m "feat(copilot): make InterviewCompleteCard sidebar-aware and domain-generic"
```

---

## Task 5: Dynamic interview config by archetype (backend)

**Files:**
- Create: `backend/tests/modules/copilot/test_dynamic_interview_config.py`
- Modify: `backend/src/modules/copilot/domain/interview_config.py`
- Modify: `backend/src/modules/copilot/domain/interview_configs/offer_config.py`

The spec requires that when `startInterview("offer", entity_id)` is called, the interview config is generated dynamically based on the offer's archetype. We add a `get_offer_interview_config(archetype)` factory that returns blocks adapted to the archetype.

- [ ] **Step 1: Write test for dynamic config generation**

Create `backend/tests/modules/copilot/test_dynamic_interview_config.py`:

```python
"""Tests for dynamic interview config generation by archetype."""

import pytest

from src.modules.copilot.domain.interview_configs.offer_config import (
    get_offer_interview_config,
    OFFER_INTERVIEW_CONFIG,
)


class TestDynamicInterviewConfig:
    """Test dynamic interview config generation."""

    def test_producto_config_has_product_details_block(self):
        config = get_offer_interview_config("producto")
        block_ids = [b.id for b in config.bloques]
        assert "product_details" in block_ids
        assert "program_details" not in block_ids

    def test_programa_config_has_program_details_block(self):
        config = get_offer_interview_config("programa")
        block_ids = [b.id for b in config.bloques]
        assert "program_details" in block_ids
        assert "product_details" not in block_ids

    def test_servicio_config_has_service_details_block(self):
        config = get_offer_interview_config("servicio")
        block_ids = [b.id for b in config.bloques]
        assert "service_details" in block_ids

    def test_membresia_config_has_subscription_details_block(self):
        config = get_offer_interview_config("membresia")
        block_ids = [b.id for b in config.bloques]
        assert "subscription_details" in block_ids

    def test_experiencia_config_has_event_details_block(self):
        config = get_offer_interview_config("experiencia")
        block_ids = [b.id for b in config.bloques]
        assert "event_details" in block_ids

    def test_universal_blocks_always_present(self):
        """strategy, promise, psychology are always first; value_stack, pricing, closing always last."""
        for archetype in ("producto", "programa", "servicio", "membresia", "experiencia"):
            config = get_offer_interview_config(archetype)
            block_ids = [b.id for b in config.bloques]
            # First 3 universal
            assert block_ids[0] == "strategy"
            assert block_ids[1] == "promise"
            assert block_ids[2] == "psychology"
            # Last 3 universal
            assert block_ids[-3] == "value_stack"
            assert block_ids[-2] == "pricing"
            assert block_ids[-1] == "closing"

    def test_unknown_archetype_returns_base_config(self):
        """Unknown archetype uses static OFFER_INTERVIEW_CONFIG as fallback."""
        config = get_offer_interview_config("unknown")
        assert config.domain == "offer"
        assert config is OFFER_INTERVIEW_CONFIG

    def test_config_domain_is_offer(self):
        config = get_offer_interview_config("producto")
        assert config.domain == "offer"

    def test_total_blocks_with_archetype(self):
        """3 universal + 1 archetype + 3 universal final = 7 blocks."""
        config = get_offer_interview_config("producto")
        assert len(config.bloques) == 7
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_dynamic_interview_config.py -x -q --tb=short`
Expected: FAIL — `get_offer_interview_config` doesn't exist.

- [ ] **Step 3: Implement `get_offer_interview_config` in offer_config.py**

Replace the content of `backend/src/modules/copilot/domain/interview_configs/offer_config.py` with:

```python
"""Offer interview configuration — dynamic by archetype."""

from src.modules.copilot.domain.interview_config import (
    InterviewBlock,
    InterviewConfig,
    register_interview_config,
)

# ── Universal blocks (all archetypes) ────────────────────────────────

_UNIVERSAL_FIRST = [
    InterviewBlock(
        id="strategy",
        label="Estrategia & Avatar",
        campos_objetivo=[
            "public_name", "archetype", "delivery_model",
            "value_level", "format_hint",
        ],
        prompt_context=(
            "Define QUÉ es este offer y DÓNDE encaja en el ladder de valor. "
            "¿Es un lead magnet, producto de activación, o transformación core? "
            "Identifica arquetipo, modelo de entrega (DIY, DWY, DFY), "
            "y asegúrate de que el nombre sea memorable y orientado al resultado."
        ),
    ),
    InterviewBlock(
        id="promise",
        label="Promesa & Resultado",
        campos_objetivo=[
            "headline_promise", "primary_outcome",
            "time_to_value", "target_avatar_match",
        ],
        prompt_context=(
            "Construye la PROMESA — resultado específico y medible. "
            "headline_promise: MAX 15 palabras. primary_outcome: lo que cambia "
            "en la vida del cliente DESPUÉS. time_to_value: ¿en cuánto tiempo ven resultados?"
        ),
    ),
    InterviewBlock(
        id="psychology",
        label="Psicología de Venta",
        campos_objetivo=[
            "marketing_pain_points", "marketing_desires", "objections",
        ],
        prompt_context=(
            "Mapea la psicología de compra: dolor que activa la búsqueda, "
            "deseo que motiva la acción, objeciones que frenan la decisión. "
            "Para cada objeción: trigger_phrases, tipo, estrategia de rebuttal, respuesta concreta."
        ),
    ),
]

_UNIVERSAL_FINAL = [
    InterviewBlock(
        id="value_stack",
        label="Stack de Valor",
        campos_objetivo=[
            "deliverables", "includes_offers",
            "access_duration_text", "support_duration_days",
        ],
        prompt_context=(
            "Construye el VALUE STACK: qué recibe el cliente, cuánto vale cada pieza, "
            "cómo anclar el precio. Cada deliverable: nombre, formato, cantidad, valor percibido."
        ),
        coverage_threshold=0.7,
    ),
    InterviewBlock(
        id="pricing",
        label="Precios & Garantía",
        campos_objetivo=[
            "pricing_options", "price_pay_in_full",
            "guarantee_type", "guarantee_terms",
        ],
        prompt_context=(
            "Diseña estructura de precio, opciones de pago y garantía. "
            "Aplica anclaje, fraccionamiento, comparación. "
            "Garantía: condicional vs incondicional, alineada con archetype."
        ),
        coverage_threshold=0.7,
    ),
    InterviewBlock(
        id="closing",
        label="Cierre & Acción",
        campos_objetivo=[
            "onboarding_action", "prerequisites",
            "requires_application", "anti_avatar_keywords",
        ],
        prompt_context=(
            "Define el CIERRE: onboarding, calificación, urgencia legítima. "
            "¿Qué pasa después de comprar? ¿Prerrequisitos? ¿Aplicación o compra directa? "
            "Anti-avatar: ¿para quién NO es?"
        ),
        coverage_threshold=0.6,
    ),
]

# ── Archetype-specific blocks ────────────────────────────────────────

ARCHETYPE_BLOCKS: dict[str, InterviewBlock] = {
    "producto": InterviewBlock(
        id="product_details",
        label="Detalles del Producto",
        campos_objetivo=[
            "product_format", "product_modules", "product_duration",
            "product_updates_policy", "product_bonuses",
        ],
        prompt_context=(
            "Detalla el producto digital: formato (video, PDF, audio), módulos o secciones, "
            "duración total, política de actualizaciones, y bonuses incluidos."
        ),
    ),
    "programa": InterviewBlock(
        id="program_details",
        label="Detalles del Programa",
        campos_objetivo=[
            "program_duration_weeks", "program_sessions", "program_methodology",
            "program_community", "program_certification",
        ],
        prompt_context=(
            "Detalla el programa: duración en semanas, sesiones (en vivo/grabadas), "
            "metodología, comunidad de alumnos, y certificación al completar."
        ),
    ),
    "servicio": InterviewBlock(
        id="service_details",
        label="Detalles del Servicio",
        campos_objetivo=[
            "service_scope", "service_deliverables_timeline",
            "service_communication_channels", "service_revisions_policy",
        ],
        prompt_context=(
            "Detalla el servicio: alcance, timeline de entregables, "
            "canales de comunicación, y política de revisiones."
        ),
    ),
    "membresia": InterviewBlock(
        id="subscription_details",
        label="Detalles de la Membresía",
        campos_objetivo=[
            "membership_billing_cycle", "membership_content_cadence",
            "membership_exclusive_perks", "membership_cancellation_policy",
        ],
        prompt_context=(
            "Detalla la membresía: ciclo de cobro, cadencia de contenido nuevo, "
            "beneficios exclusivos para miembros, y política de cancelación."
        ),
    ),
    "experiencia": InterviewBlock(
        id="event_details",
        label="Detalles de la Experiencia",
        campos_objetivo=[
            "event_format", "event_location", "event_capacity",
            "event_agenda_highlights", "event_networking",
        ],
        prompt_context=(
            "Detalla la experiencia/evento: formato (presencial/virtual/híbrido), "
            "ubicación, capacidad, highlights de la agenda, y oportunidades de networking."
        ),
    ),
}

# ── Static fallback (backward-compatible) ────────────────────────────

OFFER_BLOCKS = [
    *_UNIVERSAL_FIRST,
    *_UNIVERSAL_FINAL,
]

OFFER_INTERVIEW_CONFIG = InterviewConfig(
    domain="offer",
    objetivo="Diseñar un offer irresistible, diferenciado, y alineado con el ladder de valor del negocio",
    bloques=OFFER_BLOCKS,
    output_schema_path="modules.offer.domain.offer.Offer",
    datos_previos_fields=[
        "public_name", "archetype", "pricing_options", "headline_promise",
    ],
    tono="Eres un estratega de producto con experiencia en info-productos, SaaS, y servicios premium.",
    expertise_template="offer_expertise",
    document_extraction_template="offer_doc_extraction",
    rag_collection=None,
    initial_research_enabled=True,
    context_loader="offer_context",
)

register_interview_config("offer", OFFER_INTERVIEW_CONFIG)


def get_offer_interview_config(archetype: str) -> InterviewConfig:
    """Generate interview config adapted to the offer's archetype.

    Returns the static OFFER_INTERVIEW_CONFIG for unknown archetypes.
    """
    archetype_block = ARCHETYPE_BLOCKS.get(archetype)
    if archetype_block is None:
        return OFFER_INTERVIEW_CONFIG

    blocks = [*_UNIVERSAL_FIRST, archetype_block, *_UNIVERSAL_FINAL]

    return InterviewConfig(
        domain="offer",
        objetivo=OFFER_INTERVIEW_CONFIG.objetivo,
        bloques=blocks,
        output_schema_path=OFFER_INTERVIEW_CONFIG.output_schema_path,
        datos_previos_fields=OFFER_INTERVIEW_CONFIG.datos_previos_fields,
        tono=OFFER_INTERVIEW_CONFIG.tono,
        expertise_template=OFFER_INTERVIEW_CONFIG.expertise_template,
        document_extraction_template=OFFER_INTERVIEW_CONFIG.document_extraction_template,
        rag_collection=OFFER_INTERVIEW_CONFIG.rag_collection,
        initial_research_enabled=OFFER_INTERVIEW_CONFIG.initial_research_enabled,
        context_loader=OFFER_INTERVIEW_CONFIG.context_loader,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_dynamic_interview_config.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/copilot/domain/interview_configs/offer_config.py backend/tests/modules/copilot/test_dynamic_interview_config.py
git commit -m "feat(copilot): dynamic interview config by offer archetype"
```

---

## Task 6: Interview service uses dynamic config for offer domain

**Files:**
- Create: `backend/tests/modules/copilot/test_interview_service_dynamic.py`
- Modify: `backend/src/modules/copilot/application/services/interview_service.py`

When `start_interview(domain="offer", entity_id=...)` is called, the service should load the offer entity, read its archetype, and generate the dynamic config.

- [ ] **Step 1: Write test for dynamic config in service**

Create `backend/tests/modules/copilot/test_interview_service_dynamic.py`:

```python
"""Tests for interview service dynamic offer config."""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.modules.copilot.application.services.interview_service import InterviewService


class TestInterviewServiceDynamicConfig:
    """Test that start_interview uses archetype-specific config for offers."""

    @patch("src.modules.copilot.application.services.interview_service.InterviewSessionRepository")
    @patch("src.modules.copilot.application.services.interview_service.ConversationRepository")
    def test_offer_with_entity_id_uses_dynamic_config(self, mock_conv_repo, mock_session_repo):
        db = MagicMock()
        service = InterviewService(db)
        service.session_repo.get_active_by_domain.return_value = None

        tenant_id = uuid4()
        user_id = uuid4()
        entity_id = uuid4()

        with patch(
            "src.modules.copilot.application.services.interview_service._load_offer_archetype",
            return_value="programa",
        ):
            result = service.start_interview(
                tenant_id=tenant_id,
                user_id=user_id,
                domain="offer",
                entity_id=entity_id,
            )

        assert result["session_id"] is not None
        # The config should have program_details block
        config = result["config"]
        block_ids = [b["id"] if isinstance(b, dict) else b.id for b in config.get("bloques", [])]
        assert "program_details" in block_ids

    @patch("src.modules.copilot.application.services.interview_service.InterviewSessionRepository")
    @patch("src.modules.copilot.application.services.interview_service.ConversationRepository")
    def test_offer_without_entity_uses_static_config(self, mock_conv_repo, mock_session_repo):
        db = MagicMock()
        service = InterviewService(db)
        service.session_repo.get_active_by_domain.return_value = None

        tenant_id = uuid4()
        user_id = uuid4()

        result = service.start_interview(
            tenant_id=tenant_id,
            user_id=user_id,
            domain="offer",
        )

        assert result["session_id"] is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_service_dynamic.py -x -q --tb=short`
Expected: FAIL — `_load_offer_archetype` doesn't exist.

- [ ] **Step 3: Modify interview_service.py to use dynamic config**

In `backend/src/modules/copilot/application/services/interview_service.py`, add the archetype loader and modify `start_interview`:

Add import at top:
```python
from src.modules.copilot.domain.interview_configs.offer_config import get_offer_interview_config
```

Add helper function before the class:
```python
def _load_offer_archetype(db: Session, tenant_id: UUID, entity_id: UUID) -> str | None:
    """Load offer archetype from DB. Returns None if not found."""
    from src.modules.offer.infrastructure.models.offer_model import OfferModel

    result = db.execute(
        select(OfferModel.archetype).where(
            OfferModel.id == entity_id,
            OfferModel.tenant_id == tenant_id,
        )
    )
    row = result.scalar_one_or_none()
    return row if row else None
```

Add `select` import:
```python
from sqlalchemy import select
```

In `start_interview`, replace `config = get_interview_config(domain)` with:
```python
# Dynamic config for offers based on archetype
if domain == "offer" and entity_id:
    archetype = _load_offer_archetype(self.db, tenant_id, entity_id)
    config = get_offer_interview_config(archetype or "")
else:
    config = get_interview_config(domain)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_service_dynamic.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 5: Run full backend tests**

Run: `cd backend && .venv/bin/pytest -x -q --tb=short`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/copilot/application/services/interview_service.py backend/tests/modules/copilot/test_interview_service_dynamic.py
git commit -m "feat(copilot): interview service uses dynamic config for offer domain"
```

---

## Task 7: Intelligence rules in interview system prompt

**Files:**
- Modify: `backend/src/modules/copilot/infrastructure/prompts/templates/copilot_interview.j2`

Add the 7 intelligence rules from spec section 6. Three of the four existing rules are already present (GLOBAL CAPTURE, NEVER REPEAT, VISIBLE INTELLIGENCE). We need to add COVERAGE ADAPTATION, BULK EXTRACTION, USER'S ORDER, and FOCUS CONSTRAINT.

- [ ] **Step 1: Update copilot_interview.j2**

Replace the content of `backend/src/modules/copilot/infrastructure/prompts/templates/copilot_interview.j2`:

```jinja2
--- INTERVIEW MODE ACTIVE ---
Current block: {{ current_block_label }} ({{ current_block_id }})
Progress: {{ blocks_completed_count }}/{{ total_blocks }} blocks completed
Coverage for current block: {{ coverage_pct }}%

{% if coverage_pct >= 80 %}
HIGH COVERAGE: This block is mostly filled (from documents or earlier conversation).
Present a summary of what you have, ask if it is correct, and advance quickly.
Do NOT ask all questions — just confirm and adjust.
{% elif coverage_pct > 0 %}
PARTIAL COVERAGE: Some fields are already filled.
Acknowledge what you have, ask ONLY for what is missing.
{% else %}
EMPTY BLOCK: Follow the full interview protocol for this block.
{% endif %}

Mapa global (accumulated data):
{{ mapa_global | tojson(indent=2) }}

{% if block_coverage_status %}
Coverage by block:
{% for block_id, cov in block_coverage_status.items() %}- {{ block_id }}: {{ cov }}%
{% endfor %}
{% endif %}

FUNDAMENTAL RULES:
1. GLOBAL CAPTURE: Extract ALL data the user mentions to ANY section using
   extract_structured. The mapa_global is your memory. Never let information
   pass without capturing it.

2. NEVER REPEAT: Check mapa_global before asking. If you already have a datum,
   do not ask again. Confirm briefly and ask ONLY what is missing.

3. COVERAGE ADAPTATION: When entering a block, evaluate how much you already
   have. If >80%: confirm and advance quickly. If >0%: acknowledge what you
   have, ask for missing parts. If 0%: full interview questions.

4. BULK EXTRACTION: When the user uploads documents or URLs, extract against
   ALL sections simultaneously. Then adapt the interview to what was filled.

5. USER'S ORDER: The user can be messy. They may talk about pricing when
   you're on promise. They may send audio with info about 5 mixed sections.
   Your job is to understand, classify, capture, and lose nothing.

6. VISIBLE INTELLIGENCE: When you capture data for another section, confirm
   briefly: "Anoté los detalles de programa que mencionaste. Los revisaremos
   cuando lleguemos." Then return to the current topic.

7. FOCUS CONSTRAINT: Every response must relate to the focused entity. If the
   user asks something unrelated, acknowledge briefly and redirect: "Interesante,
   pero ahora estamos enfocados en tu oferta. Cuando terminemos, puedo ayudarte
   con eso."

ONE QUESTION AT A TIME: Ask one focused question per message. Wait for the
answer before asking the next.
--- END INTERVIEW MODE ---
```

- [ ] **Step 2: Run backend lint**

Run: `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`
Expected: PASS (template file not linted, but verify no Python issues)

- [ ] **Step 3: Commit**

```bash
git add backend/src/modules/copilot/infrastructure/prompts/templates/copilot_interview.j2
git commit -m "feat(copilot): add 7 intelligence rules to interview system prompt"
```

---

## Task 8: "Crear con asistente IA" button in CreateOfferWizard

**Files:**
- Modify: `frontend/src/features/offer-studio/components/wizard/CreateOfferWizard.tsx`
- Test: `frontend/src/features/offer-studio/components/wizard/__tests__/CreateOfferWizard.test.tsx`

Add a second button "Crear con asistente IA" next to "Crear Oferta" on the final wizard step. This calls a new `onCreateWithIA` callback prop.

- [ ] **Step 1: Write test for IA button**

Create `frontend/src/features/offer-studio/components/wizard/__tests__/CreateOfferWizard.test.tsx`:

```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { CreateOfferWizard } from "../CreateOfferWizard";

// Mock dependencies
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("test-token") }),
}));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "test-tenant" }),
}));
vi.mock("@/features/tenant/context/tenant-locale-context", () => ({
  useTenantLocale: () => ({ currency: "USD", timezone: "UTC" }),
}));

describe("CreateOfferWizard IA button", () => {
  it("renders 'Crear con asistente IA' button on final step (no editions)", async () => {
    const onCreateOffer = vi.fn();
    const onCreateWithIA = vi.fn();

    render(
      <CreateOfferWizard
        open={true}
        onOpenChange={() => {}}
        onCreateOffer={onCreateOffer}
        onCreateWithIA={onCreateWithIA}
      />,
    );

    // Step 1: select archetype (Producto — no editions step)
    fireEvent.click(screen.getByText("Producto Digital"));

    // Step 2: skip format
    fireEvent.click(screen.getByText(/saltar este paso/i));

    // Step 3: fill name
    const nameInput = screen.getByLabelText(/nombre de la oferta/i);
    fireEvent.change(nameInput, { target: { value: "Mi Curso" } });
    fireEvent.click(screen.getByText("Siguiente"));

    // Step 4 (final for producto): should have both buttons
    expect(screen.getByText("Crear Oferta")).toBeTruthy();
    expect(screen.getByText("Crear con asistente IA")).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/offer-studio/components/wizard/__tests__/CreateOfferWizard.test.tsx`
Expected: FAIL — `onCreateWithIA` prop doesn't exist and button text not found.

- [ ] **Step 3: Add onCreateWithIA prop and button**

In `frontend/src/features/offer-studio/components/wizard/CreateOfferWizard.tsx`:

Add to `CreateOfferWizardProps`:
```tsx
interface CreateOfferWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateOffer: (data: WizardResult) => Promise<void>;
  onCreateWithIA?: (data: WizardResult) => Promise<void>;
  creating?: boolean;
}
```

Update destructuring:
```tsx
export function CreateOfferWizard({ open, onOpenChange, onCreateOffer, onCreateWithIA, creating = false }: CreateOfferWizardProps) {
```

Add import for `Sparkles`:
```tsx
import { ArrowLeft, ArrowRight, Loader2, SkipForward, Rocket, Sparkles } from "lucide-react";
```

Add handler:
```tsx
const handleCreateWithIA = async () => {
  if (!selectedArchetype || !offerName.trim() || !onCreateWithIA) return;
  await onCreateWithIA({
    archetype: selectedArchetype,
    format_hint: formatHint || undefined,
    name: offerName.trim(),
    is_lead_magnet: effectiveLeadMagnet,
    has_editions: showsEditionsStep ? hasEditions : undefined,
    headline_promise: headlinePromise || undefined,
    status: OfferStatus.DRAFT,
    delivery_model: selectedDeliveryModel,
    value_level: selectedValueLevel,
    specific_details: selectedSpecificDetails,
  });
};
```

In the footer, add the IA button next to "Crear Oferta" in all final-step locations. For the `{step === 4 && !showsEditionsStep}` block (line 509-526), replace with:
```tsx
{step === 4 && !showsEditionsStep && (
  <>
    <Button
      variant="outline"
      onClick={handleCreate}
      disabled={creating || !offerName.trim()}
    >
      Completar despues
    </Button>
    {onCreateWithIA && (
      <Button
        variant="secondary"
        onClick={handleCreateWithIA}
        disabled={creating || !offerName.trim()}
      >
        <Sparkles className="mr-1 h-3 w-3" />
        Crear con asistente IA
      </Button>
    )}
    <Button
      onClick={handleCreate}
      disabled={creating || !offerName.trim()}
    >
      {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
      Crear Oferta
    </Button>
  </>
)}
```

Apply the same pattern to `{step === finalStep && finalStep === 5}` (line 527-544):
```tsx
{step === finalStep && finalStep === 5 && (
  <>
    <Button
      variant="outline"
      onClick={handleCreate}
      disabled={creating || !offerName.trim()}
    >
      Completar despues
    </Button>
    {onCreateWithIA && (
      <Button
        variant="secondary"
        onClick={handleCreateWithIA}
        disabled={creating || !offerName.trim()}
      >
        <Sparkles className="mr-1 h-3 w-3" />
        Crear con asistente IA
      </Button>
    )}
    <Button
      onClick={handleCreate}
      disabled={creating || !offerName.trim()}
    >
      {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
      Crear Oferta
    </Button>
  </>
)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/offer-studio/components/wizard/__tests__/CreateOfferWizard.test.tsx`
Expected: PASS

- [ ] **Step 5: Run type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/offer-studio/components/wizard/CreateOfferWizard.tsx frontend/src/features/offer-studio/components/wizard/__tests__/CreateOfferWizard.test.tsx
git commit -m "feat(offer-studio): add 'Crear con asistente IA' button to wizard"
```

---

## Task 9: Wire IA creation flow in offer-studio-dashboard

**Files:**
- Modify: `frontend/src/features/offer-studio/components/dashboard/offer-studio-dashboard.tsx`

When "Crear con asistente IA" is clicked, the dashboard handler should:
1. Create the offer in DB (same as `handleCreateOffer`)
2. Navigate to `/offer-studio/offer/{id}`
3. Activate interview in sidebar: `setFocusEntity`, `startInterview`, `setInterviewSession`, `setSidebarState("expanded")`

- [ ] **Step 1: Add the IA handler and pass it to CreateOfferWizard**

In `offer-studio-dashboard.tsx`, add imports:
```tsx
import { startInterview } from "@/features/copilot/api/interview-api";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";
```

Add the handler after `handleCreateOffer`:
```tsx
const handleCreateOfferWithIA = async (wizardData: WizardResult) => {
  setCreating(true);
  try {
    const token = await getToken();
    if (!token) throw new Error("No authenticated");

    const newOffer = await offerApi.createOffer({
      public_name: wizardData.name,
      archetype: wizardData.archetype,
      format_hint: wizardData.format_hint,
      is_lead_magnet: wizardData.is_lead_magnet,
      has_editions: wizardData.has_editions,
      headline_promise: wizardData.headline_promise,
      status: wizardData.status,
      delivery_model: wizardData.delivery_model,
      offer_value_level: wizardData.value_level,
      specific_details: wizardData.specific_details,
    } as any, token);

    if (newOffer.id) {
      setIsWizardOpen(false);

      // Activate interview in sidebar
      const store = useCopilotStore.getState();
      store.setFocusEntity({
        domain: "offer",
        entityId: newOffer.id,
        label: wizardData.name,
      });

      const interview = await startInterview(token, "offer", newOffer.id);
      store.setInterviewSession(interview.session_id);
      store.setConversationId(interview.conversation_id);
      store.addMessage({
        id: crypto.randomUUID(),
        role: "assistant",
        content: interview.initial_message,
        timestamp: Date.now(),
      });
      store.setSidebarState("expanded");

      navigate(`/${tenantId}/offer-studio/offer/${newOffer.id}`);
    }
  } catch (err) {
    console.error("Error creating offer with IA:", err);
  } finally {
    setCreating(false);
  }
};
```

Pass it to CreateOfferWizard:
```tsx
<CreateOfferWizard
  open={isWizardOpen}
  onOpenChange={setIsWizardOpen}
  onCreateOffer={handleCreateOffer}
  onCreateWithIA={handleCreateOfferWithIA}
  creating={creating}
/>
```

- [ ] **Step 2: Run type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/offer-studio/components/dashboard/offer-studio-dashboard.tsx
git commit -m "feat(offer-studio): wire IA creation flow — create offer + activate interview in sidebar"
```

---

## Task 10: Interview pages become thin redirectors

**Files:**
- Modify: `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/interview/page.tsx`
- Modify: `frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/interview/page.tsx`

These pages should redirect to the main studio page and activate the interview in the sidebar. Since they're server components, they use `redirect()` from `next/navigation`.

- [ ] **Step 1: Update brand-studio interview page**

Replace `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/interview/page.tsx`:

```tsx
import { redirect } from "next/navigation";

interface PageProps {
  params: Promise<{ tenantId: string }>;
  searchParams: Promise<{ session?: string }>;
}

export default async function InterviewPage({ params, searchParams }: PageProps) {
  const { tenantId } = await params;
  const { session } = await searchParams;

  // Redirect to brand-studio with interview query param for sidebar activation
  const target = session
    ? `/${tenantId}/brand-studio?interview=${session}`
    : `/${tenantId}/brand-studio`;

  redirect(target);
}
```

- [ ] **Step 2: Update offer-studio interview page**

Replace `frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/interview/page.tsx`:

```tsx
import { redirect } from "next/navigation";

interface PageProps {
  params: Promise<{ tenantId: string }>;
  searchParams: Promise<{ offerId?: string; session?: string }>;
}

export default async function OfferInterviewPage({ params, searchParams }: PageProps) {
  const { tenantId } = await params;
  const { session, offerId } = await searchParams;

  // Redirect to offer editor/dashboard with interview query param for sidebar activation
  const base = offerId
    ? `/${tenantId}/offer-studio/offer/${offerId}`
    : `/${tenantId}/offer-studio`;

  const target = session ? `${base}?interview=${session}` : base;

  redirect(target);
}
```

- [ ] **Step 3: Run type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/interview/page.tsx frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/interview/page.tsx
git commit -m "refactor(copilot): interview pages redirect to studio with sidebar activation"
```

---

## Task 11: WithCopilot focus-mode AI badge

**Files:**
- Modify: `frontend/src/features/copilot/components/WithCopilot.tsx`
- Test: `frontend/src/features/copilot/components/__tests__/WithCopilot.test.tsx`

In focus mode, when `focusEntity` matches the field's domain, fields modified by copilot should show a persistent "IA" badge until the user manually edits. The badge uses the existing `copilot:field-update` event.

- [ ] **Step 1: Write test for AI badge**

Create `frontend/src/features/copilot/components/__tests__/WithCopilot.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { WithCopilot } from "../WithCopilot";
import { useCopilotStore } from "../../store/copilot-store";

describe("WithCopilot AI badge", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      selectedFields: [],
      focusEntity: null,
    });
  });

  it("shows IA badge when field updated via copilot in focus mode", () => {
    // Set focus mode
    useCopilotStore.setState({
      focusEntity: { domain: "offer", entityId: "123", label: "Test" },
    });

    render(
      <WithCopilot fieldId="headline" fieldLabel="Headline" getValue={() => "val"}>
        <input />
      </WithCopilot>,
    );

    // Dispatch field-update event
    act(() => {
      window.dispatchEvent(
        new CustomEvent("copilot:field-update", {
          detail: { fieldId: "headline", newValue: "AI value" },
        }),
      );
    });

    expect(screen.getByText("IA")).toBeTruthy();
  });

  it("does NOT show IA badge when not in focus mode", () => {
    render(
      <WithCopilot fieldId="headline" fieldLabel="Headline" getValue={() => "val"}>
        <input />
      </WithCopilot>,
    );

    act(() => {
      window.dispatchEvent(
        new CustomEvent("copilot:field-update", {
          detail: { fieldId: "headline", newValue: "AI value" },
        }),
      );
    });

    expect(screen.queryByText("IA")).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/copilot/components/__tests__/WithCopilot.test.tsx`
Expected: FAIL — no "IA" badge rendered.

- [ ] **Step 3: Add AI badge to WithCopilot**

In `frontend/src/features/copilot/components/WithCopilot.tsx`:

Add state for AI modification tracking:
```tsx
const [aiModified, setAiModified] = useState(false);
const focusEntity = useCopilotStore((s) => s.focusEntity);
const inFocusMode = focusEntity !== null;
```

Modify the existing `copilot:field-update` listener to also set `aiModified`:
```tsx
useEffect(() => {
  const handler = (e: Event) => {
    const detail = (e as CustomEvent).detail as {
      fieldId: string;
      newValue: string;
    };
    if (detail.fieldId === fieldId) {
      setIsHighlighted(true);
      setTimeout(() => setIsHighlighted(false), 2500);
      // In focus mode, mark field as AI-modified
      if (inFocusMode) {
        setAiModified(true);
      }
    }
  };

  window.addEventListener("copilot:field-update", handler);
  return () => window.removeEventListener("copilot:field-update", handler);
}, [fieldId, inFocusMode]);
```

Add a listener to clear the badge on manual edit (user input events):
```tsx
useEffect(() => {
  if (!aiModified || !containerRef.current) return;

  const clearBadge = () => setAiModified(false);
  const container = containerRef.current;

  container.addEventListener("input", clearBadge);
  return () => container.removeEventListener("input", clearBadge);
}, [aiModified]);
```

Add the badge element in the JSX, after the pill toggle button:
```tsx
{/* AI badge — shown when field was modified by copilot in focus mode */}
{aiModified && inFocusMode && (
  <span className="absolute -top-3.5 left-3 z-10 rounded-full bg-purple-600 px-1.5 py-0.5 text-[9px] font-bold text-white shadow-sm">
    IA
  </span>
)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/copilot/components/__tests__/WithCopilot.test.tsx`
Expected: PASS

- [ ] **Step 5: Run type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/copilot/components/WithCopilot.tsx frontend/src/features/copilot/components/__tests__/WithCopilot.test.tsx
git commit -m "feat(copilot): WithCopilot shows IA badge for AI-modified fields in focus mode"
```

---

## Task 12: Full test suite verification

**Files:** None (verification only)

- [ ] **Step 1: Run backend lint**

Run: `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`
Expected: PASS

- [ ] **Step 2: Run backend tests**

Run: `cd backend && .venv/bin/pytest -x -q --tb=short`
Expected: PASS

- [ ] **Step 3: Run frontend type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 4: Run frontend lint**

Run: `cd frontend && npx eslint src/`
Expected: PASS (or only pre-existing warnings)

- [ ] **Step 5: Run frontend tests**

Run: `cd frontend && npx vitest run`
Expected: PASS

- [ ] **Step 6: Run architecture tests**

Run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
Expected: PASS

---

## Dependency Graph

```
Task 1 (AlternativesCard + ClarifyCard callbacks)
  └─> Task 2 (CheckpointCard callbacks)
      └─> Task 3 (Wire sendCardAction from parent)
          └─> Task 4 (InterviewCompleteCard sidebar-aware)

Task 5 (Dynamic config by archetype)
  └─> Task 6 (Service uses dynamic config)

Task 7 (Intelligence rules) — independent

Task 8 (Wizard IA button)
  └─> Task 9 (Wire IA flow in dashboard)

Task 10 (Interview page redirectors) — independent

Task 11 (WithCopilot AI badge) — independent

Task 12 (Full verification) — depends on all above
```

**Parallel groups for subagent execution:**
- **Group A (frontend cards):** Tasks 1 → 2 → 3 → 4
- **Group B (backend config):** Tasks 5 → 6
- **Group C (backend prompt):** Task 7
- **Group D (wizard + flow):** Tasks 8 → 9
- **Group E (redirectors):** Task 10
- **Group F (AI badge):** Task 11

Groups B, C, E, F are independent. Group D is independent of A but should run after B (so the backend supports the flow). Task 12 is serial after all.
