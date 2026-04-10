# Email Automations UX Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Automatizaciones tab with per-email pipeline, health scores, CTOR/unsubs columns, info tooltips on every metric, and a sidebar detail panel — matching the HTML mockup at `docs/mockups/email-automations-redesign.html`.

**Architecture:** Three-level progressive disclosure: (L1) redesigned table with health scores, (L2) inline accordion with visual email pipeline per automation, (L3) `DetailPanel` sidebar per email. All data comes from the existing `GET /automations` MailerLite call — no new API calls, only extracting the `steps[]` array that's currently discarded.

**Tech Stack:** Backend: FastAPI + SQLAlchemy 2.0 async + Pydantic v2. Frontend: Next.js 15 App Router + React 19 + Shadcn UI + Tailwind + Vitest. TDD mandatory — tests first for every layer.

**Spec:** `docs/superpowers/specs/2026-04-10-email-automations-ux-redesign.md`
**Mockup:** `docs/mockups/email-automations-redesign.html`

---

## File Map

### Backend — Modify
- `backend/src/modules/analytics/infrastructure/providers/mailerlite_provider.py` — extract `steps[]` detail, read `enabled` for status
- `backend/src/modules/analytics/application/dto/email_dashboard_dto.py` — add `AutomationStepDTO`, extend `EmailAutomationDTO` with `click_to_open_rate`, `unsubscribes`, `steps`
- `backend/src/modules/analytics/application/services/email_dashboard_service.py` — fix `active_subscribers` (completed+in_queue), fix `completion_rate` (actual not CTOR), fix `status` (from extra), populate `steps` from extra

### Backend — Modify (tests)
- `backend/tests/modules/analytics/test_mailerlite_provider_enhanced.py` — tests for step extraction
- `backend/tests/modules/analytics/test_email_dashboard_service.py` — tests for bug fixes + new fields

### Frontend — Modify
- `frontend/src/features/growth-studio/types/mail-types.ts` — add `AutomationStep`, extend `EmailAutomation`
- `frontend/src/features/growth-studio/api/mail-api.ts` — map new fields in `mapEmailAutomation`

### Frontend — Create
- `frontend/src/features/growth-studio/utils/automation-health.ts` — `computeHealthScore()` + `diagnoseStep()`
- `frontend/src/features/growth-studio/utils/automation-metric-info.ts` — central dictionary of metric descriptions for tooltips
- `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/AutomationPipeline.tsx` — horizontal email pipeline with drop-off
- `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/AutomationStepSidebar.tsx` — DetailPanel with per-email metrics
- `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/MetricInfoTooltip.tsx` — reusable `ⓘ` tooltip component

### Frontend — Modify
- `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailAutomatizacionesTab.tsx` — rewrite table + accordion + sidebar integration

### Frontend — Create (tests)
- `frontend/src/features/growth-studio/utils/__tests__/automation-health.test.ts`
- `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/__tests__/AutomationPipeline.test.tsx`
- `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/__tests__/AutomationStepSidebar.test.tsx`

### Frontend — Modify (tests)
- `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/__tests__/MailTabs.test.tsx` — update for new table columns

---

## Phase 1: Backend — Data Layer

### Task 1: Extend DTOs

**Files:**
- Modify: `backend/src/modules/analytics/application/dto/email_dashboard_dto.py`

- [ ] **Step 1: Read current DTO file to locate `EmailAutomationDTO`**

Run: Read `backend/src/modules/analytics/application/dto/email_dashboard_dto.py` lines 144-170

Expected: find `class EmailAutomationDTO(BaseModel)` around line 147.

- [ ] **Step 2: Add `AutomationStepDTO` and extend `EmailAutomationDTO`**

Replace the existing `EmailAutomationDTO` block with:

```python
class AutomationStepDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    step_id: str
    step_number: int
    type: str  # "email" | "delay" | "condition"
    subject: str | None = None
    from_name: str | None = None
    emails_sent: int = 0
    unique_opens: int = 0
    open_rate: float = 0.0
    unique_clicks: int = 0
    click_rate: float = 0.0
    unsubscribes: int = 0
    bounces: int = 0
    screenshot_url: str | None = None
    preview_url: str | None = None
    delay_value: int | None = None
    delay_unit: str | None = None


class EmailAutomationDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    automation_id: str
    name: str
    automation_type: str  # welcome | nurture | reengagement | post_compra | other
    status: str  # active | paused
    active_subscribers: int = 0  # Now: completed + in_queue (ingresados)
    completed: int = 0
    emails_sent: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    click_to_open_rate: float = 0.0
    completion_rate: float = 0.0
    unsubscribes: int = 0
    steps: list[AutomationStepDTO] = []
```

- [ ] **Step 3: Run lint and verify imports OK**

Run: `cd backend && .venv/bin/ruff check src/modules/analytics/application/dto/email_dashboard_dto.py --no-cache`

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add backend/src/modules/analytics/application/dto/email_dashboard_dto.py
git commit -m "feat(analytics): add AutomationStepDTO and extend EmailAutomationDTO with ctor/unsubs/steps"
```

---

### Task 2: Provider — Write test for step extraction

**Files:**
- Modify: `backend/tests/modules/analytics/test_mailerlite_provider_enhanced.py`

- [ ] **Step 1: Append a new test class for step extraction at end of file**

Add at the end of the file:

```python
class TestAutomationStepExtraction:
    """Tests for per-step email data extraction in _extract_automations."""

    def _build_mock_automation(self) -> dict:
        """Build a mock MailerLite /automations response object with steps."""
        return {
            "id": "auto-123",
            "name": "BIENVENIDA: nuevas inscritas",
            "enabled": True,
            "stats": {
                "sent": 18,
                "completed_subscribers_count": 4,
                "subscribers_in_queue_count": 5,
                "open_rate": {"float": 0.85, "string": "85.0%"},
                "click_rate": {"float": 0.42, "string": "42.0%"},
                "click_to_open_rate": {"float": 0.49, "string": "49.0%"},
                "unsubscribes_count": 1,
            },
            "steps": [
                {
                    "id": "step-1",
                    "type": "email",
                    "subject": "¡Bienvenida!",
                    "from_name": "Visionarias",
                    "email": {
                        "screenshot_url": "https://img.example/1.png",
                        "preview_url": "https://preview.example/1",
                        "stats": {
                            "sent": 9,
                            "unique_opens_count": 9,
                            "open_rate": {"float": 1.0, "string": "100%"},
                            "unique_clicks_count": 9,
                            "click_rate": {"float": 1.0, "string": "100%"},
                            "unsubscribes_count": 0,
                            "hard_bounces_count": 0,
                            "soft_bounces_count": 0,
                        },
                    },
                },
                {
                    "id": "step-2",
                    "type": "delay",
                    "unit": "days",
                    "value": 2,
                },
                {
                    "id": "step-3",
                    "type": "email",
                    "subject": "Próximos pasos",
                    "from_name": "Visionarias",
                    "email": {
                        "screenshot_url": None,
                        "preview_url": "https://preview.example/3",
                        "stats": {
                            "sent": 4,
                            "unique_opens_count": 3,
                            "open_rate": {"float": 0.75, "string": "75%"},
                            "unique_clicks_count": 1,
                            "click_rate": {"float": 0.25, "string": "25%"},
                            "unsubscribes_count": 1,
                            "hard_bounces_count": 0,
                            "soft_bounces_count": 0,
                        },
                    },
                },
            ],
        }

    def test_extracts_steps_into_extra(self):
        """Provider extra must contain steps array with per-email data."""
        from src.modules.analytics.infrastructure.providers.mailerlite_provider import (
            MailerLiteProvider,
        )

        provider = MailerLiteProvider()
        mock_auto = self._build_mock_automation()

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json = lambda: {"data": [mock_auto]}
        mock_response.raise_for_status = lambda: None
        mock_client.get = AsyncMock(return_value=mock_response)

        metrics = _run(
            provider._extract_automations(
                mock_client,
                {},
                {},
                date(2026, 4, 1),
                date(2026, 4, 10),
                "email-nurture",
            )
        )

        assert len(metrics) > 0
        first = metrics[0]
        assert first.extra["source"] == "automation"
        assert "steps" in first.extra
        steps = first.extra["steps"]
        assert len(steps) == 3
        assert steps[0]["type"] == "email"
        assert steps[0]["subject"] == "¡Bienvenida!"
        assert steps[0]["emails_sent"] == 9
        assert steps[0]["open_rate"] == 100.0
        assert steps[0]["click_rate"] == 100.0
        assert steps[0]["screenshot_url"] == "https://img.example/1.png"
        assert steps[0]["preview_url"] == "https://preview.example/1"
        assert steps[1]["type"] == "delay"
        assert steps[1]["delay_value"] == 2
        assert steps[1]["delay_unit"] == "days"
        assert steps[2]["unsubscribes"] == 1

    def test_reads_enabled_flag_for_status(self):
        """automation_status must read the enabled flag, not hardcoded."""
        from src.modules.analytics.infrastructure.providers.mailerlite_provider import (
            MailerLiteProvider,
        )

        provider = MailerLiteProvider()
        paused_auto = self._build_mock_automation()
        paused_auto["enabled"] = False

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json = lambda: {"data": [paused_auto]}
        mock_response.raise_for_status = lambda: None
        mock_client.get = AsyncMock(return_value=mock_response)

        metrics = _run(
            provider._extract_automations(
                mock_client,
                {},
                {},
                date(2026, 4, 1),
                date(2026, 4, 10),
                "email-nurture",
            )
        )

        assert metrics[0].extra["automation_status"] == "paused"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_mailerlite_provider_enhanced.py::TestAutomationStepExtraction -x -v`

Expected: FAIL — current provider only stores `steps_count`, not the full `steps` array. Status is hardcoded.

- [ ] **Step 3: Commit the failing test**

```bash
git add backend/tests/modules/analytics/test_mailerlite_provider_enhanced.py
git commit -m "test(analytics): add failing tests for automation step extraction and status flag"
```

---

### Task 3: Provider — Implement step extraction

**Files:**
- Modify: `backend/src/modules/analytics/infrastructure/providers/mailerlite_provider.py:935-965`

- [ ] **Step 1: Add helper function at top of file (below imports, before class)**

Find the line where `classify_automation_type` is defined (around line 135). Right before it, add:

```python
def _parse_rate(raw) -> float:
    """MailerLite returns {'float': 0.625, 'string': '62.5%'} or bare float."""
    if isinstance(raw, dict):
        return float(raw.get("float", 0.0)) * 100
    return float(raw) * 100 if raw else 0.0


def _extract_step_data(steps: list[dict]) -> list[dict]:
    """Extract per-step data from MailerLite automation steps array.

    Returns list of step dicts with normalized fields for storage in extra.
    Email steps include full stats; delay steps include value+unit.
    """
    result = []
    for idx, step in enumerate(steps):
        step_type = step.get("type", "email")
        base = {
            "step_id": str(step.get("id", f"step-{idx}")),
            "step_number": idx + 1,
            "type": step_type,
        }
        if step_type == "email":
            email_obj = step.get("email", {}) or {}
            stats = email_obj.get("stats", {}) or {}
            base.update({
                "subject": step.get("subject", "") or "",
                "from_name": step.get("from_name", "") or "",
                "emails_sent": int(stats.get("sent", 0) or 0),
                "unique_opens": int(stats.get("unique_opens_count", 0) or 0),
                "open_rate": _parse_rate(stats.get("open_rate", 0)),
                "unique_clicks": int(stats.get("unique_clicks_count", 0) or 0),
                "click_rate": _parse_rate(stats.get("click_rate", 0)),
                "unsubscribes": int(stats.get("unsubscribes_count", 0) or 0),
                "bounces": int(stats.get("hard_bounces_count", 0) or 0)
                    + int(stats.get("soft_bounces_count", 0) or 0),
                "screenshot_url": email_obj.get("screenshot_url"),
                "preview_url": email_obj.get("preview_url"),
                "delay_value": None,
                "delay_unit": None,
            })
        elif step_type == "delay":
            base.update({
                "subject": None,
                "from_name": None,
                "emails_sent": 0,
                "unique_opens": 0,
                "open_rate": 0.0,
                "unique_clicks": 0,
                "click_rate": 0.0,
                "unsubscribes": 0,
                "bounces": 0,
                "screenshot_url": None,
                "preview_url": None,
                "delay_value": int(step.get("value", 0) or 0),
                "delay_unit": step.get("unit"),
            })
        else:
            base.update({
                "subject": None,
                "from_name": None,
                "emails_sent": 0,
                "unique_opens": 0,
                "open_rate": 0.0,
                "unique_clicks": 0,
                "click_rate": 0.0,
                "unsubscribes": 0,
                "bounces": 0,
                "screenshot_url": None,
                "preview_url": None,
                "delay_value": None,
                "delay_unit": None,
            })
        result.append(base)
    return result
```

- [ ] **Step 2: Update `_extract_automations` to use the new helper and fix status**

Find the `extra` dict block around line 957 and replace it with:

```python
            extra = {
                "source": "automation",
                "automation_name": name,
                "automation_status": "active" if auto.get("enabled", True) else "paused",
                "automation_type": classify_automation_type(name),
                "completed_subscribers": completed,
                "subscribers_in_queue": in_queue,
                "steps_count": len(steps),
                "steps": _extract_step_data(steps),
            }
```

- [ ] **Step 3: Run the test from Task 2**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_mailerlite_provider_enhanced.py::TestAutomationStepExtraction -x -v`

Expected: PASS (both tests).

- [ ] **Step 4: Run full provider test file to verify no regression**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_mailerlite_provider_enhanced.py -x -q --tb=short`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/analytics/infrastructure/providers/mailerlite_provider.py
git commit -m "feat(analytics): extract per-step email data from MailerLite automations"
```

---

### Task 4: Service — Write test for automation bug fixes

**Files:**
- Modify: `backend/tests/modules/analytics/test_email_dashboard_service.py`

- [ ] **Step 1: Find the existing test class for automations**

Run: Grep `test_get_automations\|class TestEmailAutomations\|def test.*automation` in `backend/tests/modules/analytics/test_email_dashboard_service.py`

Expected: locate existing automation-related tests or insertion point.

- [ ] **Step 2: Add new test class at the end of the file**

Append:

```python
class TestAutomationBugFixes:
    """Tests for the 3 automation data bugs fixed in the UX redesign."""

    def _seed_automation_rows(
        self,
        db,
        tenant_id: UUID,
        automation_id: str = "auto-abc",
        automation_name: str = "BIENVENIDA test",
        completed_subs: int = 4,
        in_queue_subs: int = 5,
        status: str = "active",
        steps: list[dict] | None = None,
    ):
        """Helper: insert per-automation official_metrics rows."""
        from datetime import date

        from src.modules.analytics.infrastructure.models.official_metric_model import (
            OfficialMetricModel,
        )

        extra = {
            "source": "automation",
            "automation_name": automation_name,
            "automation_status": status,
            "automation_type": "welcome",
            "completed_subscribers": completed_subs,
            "subscribers_in_queue": in_queue_subs,
            "steps_count": len(steps) if steps else 0,
            "steps": steps or [],
        }

        metric_rows = [
            ("emails_sent", 18.0, "count"),
            ("open_rate", 85.0, "percentage"),
            ("click_rate", 42.0, "percentage"),
            ("click_to_open_rate", 49.0, "percentage"),
            ("unsubscribes", 1.0, "count"),
        ]
        for name, value, unit in metric_rows:
            db.add(
                OfficialMetricModel(
                    tenant_id=tenant_id,
                    channel_slug="email-nurture",
                    provider="mailerlite",
                    metric_name=name,
                    value=value,
                    unit=unit,
                    metric_date=date(2026, 4, 5),
                    campaign_id=automation_id,
                    extra=extra,
                )
            )
        db.commit()

    async def test_active_subscribers_equals_completed_plus_queue(
        self, email_dashboard_service, db, tenant_id
    ):
        """Bug fix: active_subscribers was 0 because it only read in_queue."""
        self._seed_automation_rows(
            db, tenant_id, completed_subs=4, in_queue_subs=5
        )

        response = await email_dashboard_service.get_automations(tenant_id, "30d")

        assert len(response.automations) == 1
        auto = response.automations[0]
        assert auto.active_subscribers == 9  # 4 completed + 5 in_queue

    async def test_completion_rate_is_actual_completion_not_ctor(
        self, email_dashboard_service, db, tenant_id
    ):
        """Bug fix: completion_rate was mapping click_to_open_rate."""
        self._seed_automation_rows(
            db, tenant_id, completed_subs=4, in_queue_subs=6
        )

        response = await email_dashboard_service.get_automations(tenant_id, "30d")

        auto = response.automations[0]
        # 4 / (4+6) * 100 = 40.0, NOT 49.0 (which was the CTOR)
        assert auto.completion_rate == 40.0
        assert auto.click_to_open_rate == 49.0  # CTOR lives in its own field

    async def test_status_reads_from_extra_not_hardcoded(
        self, email_dashboard_service, db, tenant_id
    ):
        """Bug fix: status was always 'active' regardless of extra."""
        self._seed_automation_rows(db, tenant_id, status="paused")

        response = await email_dashboard_service.get_automations(tenant_id, "30d")

        assert response.automations[0].status == "paused"

    async def test_unsubscribes_populated(
        self, email_dashboard_service, db, tenant_id
    ):
        """New field: unsubscribes must come from the unsubscribes metric row."""
        self._seed_automation_rows(db, tenant_id)

        response = await email_dashboard_service.get_automations(tenant_id, "30d")

        assert response.automations[0].unsubscribes == 1

    async def test_steps_populated_from_extra(
        self, email_dashboard_service, db, tenant_id
    ):
        """New field: steps must be parsed from extra.steps."""
        mock_steps = [
            {
                "step_id": "s1",
                "step_number": 1,
                "type": "email",
                "subject": "¡Hola!",
                "from_name": "Yo",
                "emails_sent": 9,
                "unique_opens": 9,
                "open_rate": 100.0,
                "unique_clicks": 5,
                "click_rate": 55.5,
                "unsubscribes": 0,
                "bounces": 0,
                "screenshot_url": "https://img/1.png",
                "preview_url": "https://preview/1",
                "delay_value": None,
                "delay_unit": None,
            },
            {
                "step_id": "s2",
                "step_number": 2,
                "type": "delay",
                "subject": None,
                "from_name": None,
                "emails_sent": 0,
                "unique_opens": 0,
                "open_rate": 0.0,
                "unique_clicks": 0,
                "click_rate": 0.0,
                "unsubscribes": 0,
                "bounces": 0,
                "screenshot_url": None,
                "preview_url": None,
                "delay_value": 2,
                "delay_unit": "days",
            },
        ]
        self._seed_automation_rows(db, tenant_id, steps=mock_steps)

        response = await email_dashboard_service.get_automations(tenant_id, "30d")

        auto = response.automations[0]
        assert len(auto.steps) == 2
        assert auto.steps[0].subject == "¡Hola!"
        assert auto.steps[0].emails_sent == 9
        assert auto.steps[0].open_rate == 100.0
        assert auto.steps[0].screenshot_url == "https://img/1.png"
        assert auto.steps[1].type == "delay"
        assert auto.steps[1].delay_value == 2
        assert auto.steps[1].delay_unit == "days"
```

- [ ] **Step 3: Verify the service fixture exists or add it**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_email_dashboard_service.py -x -v --collect-only 2>&1 | head -40`

Expected: fixture `email_dashboard_service`, `db`, `tenant_id` are available. If not, check `backend/tests/modules/analytics/conftest.py` for the existing service tests and copy the pattern. If fixtures differ, adjust the test signatures to match existing fixture names.

- [ ] **Step 4: Run the new tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_email_dashboard_service.py::TestAutomationBugFixes -x -v`

Expected: FAIL — current service has bugs and missing fields.

- [ ] **Step 5: Commit the failing tests**

```bash
git add backend/tests/modules/analytics/test_email_dashboard_service.py
git commit -m "test(analytics): add failing tests for automation bug fixes and new fields"
```

---

### Task 5: Service — Fix bugs and populate new fields

**Files:**
- Modify: `backend/src/modules/analytics/application/services/email_dashboard_service.py:479-552`

- [ ] **Step 1: Update `_get_automation_list` with bug fixes**

Replace the entire `_get_automation_list` method with:

```python
    async def _get_automation_list(
        self,
        tenant_id: UUID,
        start: date,
        end: date,
    ) -> list[EmailAutomationDTO]:
        """Build automation list from official_metrics with campaign_id grouping.

        Filters by extra->>'source' = 'automation' to distinguish from campaigns.
        Bug fixes applied:
        - active_subscribers = completed + in_queue (was just in_queue)
        - completion_rate = actual (was CTOR)
        - status reads from extra (was hardcoded 'active')
        Populates new fields: click_to_open_rate, unsubscribes, steps.
        """
        stmt = (
            select(
                OfficialMetricModel.campaign_id,
                OfficialMetricModel.metric_name,
                func.sum(OfficialMetricModel.value).label("total_value"),
                func.max(cast(OfficialMetricModel.extra, String)).label("extra"),
                func.max(OfficialMetricModel.metric_date).label("last_date"),
            )
            .where(
                OfficialMetricModel.tenant_id == tenant_id,
                OfficialMetricModel.channel_slug == CHANNEL_SLUG,
                OfficialMetricModel.metric_date >= start,
                OfficialMetricModel.metric_date <= end,
                OfficialMetricModel.campaign_id.isnot(None),
                OfficialMetricModel.campaign_id != "",
                OfficialMetricModel.extra.op("->>")("source") == "automation",
            )
            .group_by(
                OfficialMetricModel.campaign_id,
                OfficialMetricModel.metric_name,
            )
        )
        result = self._db.execute(stmt)
        rows = result.all()

        # Group by campaign_id (= automation_id)
        autos_map: dict[str, dict] = {}
        for row in rows:
            aid = row.campaign_id
            if aid not in autos_map:
                extra = json.loads(row.extra) if row.extra else {}
                completed = int(extra.get("completed_subscribers", 0))
                in_queue = int(extra.get("subscribers_in_queue", 0))
                autos_map[aid] = {
                    "automation_id": aid,
                    "name": extra.get("automation_name", aid),
                    "automation_type": extra.get("automation_type", "workflow"),
                    "status": extra.get("automation_status", "active"),
                    "completed": completed,
                    "ingresados": completed + in_queue,  # FIX: was just in_queue
                    "steps_raw": extra.get("steps", []),
                    "metrics": {},
                }
            metrics_dict = autos_map[aid]["metrics"]
            if isinstance(metrics_dict, dict):
                metrics_dict[row.metric_name] = row.total_value

        automations: list[EmailAutomationDTO] = []
        for adata in autos_map.values():
            m = adata.get("metrics", {})
            if not isinstance(m, dict):
                m = {}
            completed = int(adata.get("completed", 0))
            ingresados = int(adata.get("ingresados", 0))
            completion_rate = (
                round(completed / ingresados * 100, 1) if ingresados > 0 else 0.0
            )

            steps_raw = adata.get("steps_raw", [])
            steps = [AutomationStepDTO(**s) for s in steps_raw] if isinstance(steps_raw, list) else []

            automations.append(
                EmailAutomationDTO(
                    automation_id=str(adata["automation_id"]),
                    name=str(adata["name"]),
                    automation_type=str(adata["automation_type"]),
                    status=str(adata["status"]),
                    emails_sent=int(m.get("emails_sent", 0)),
                    open_rate=round(float(m.get("open_rate", 0)), 1),
                    click_rate=round(float(m.get("click_rate", 0)), 1),
                    click_to_open_rate=round(float(m.get("click_to_open_rate", 0)), 1),
                    completion_rate=completion_rate,
                    completed=completed,
                    active_subscribers=ingresados,
                    unsubscribes=int(m.get("unsubscribes", 0)),
                    steps=steps,
                )
            )
        return automations
```

- [ ] **Step 2: Add `AutomationStepDTO` import at the top of the file**

Find the existing import block for DTOs (around line 23) and update:

```python
from src.modules.analytics.application.dto.email_dashboard_dto import (
    ActivityHeatmapCellDTO,
    AutomationStepDTO,  # NEW
    BounceBreakdownDTO,
    EmailAudienceResponseDTO,
    EmailAutomationDTO,
    EmailAutomationsResponseDTO,
    EmailCampaignDTO,
    EmailCampaignsResponseDTO,
```

(Keep the rest of the imports as they were.)

- [ ] **Step 3: Run the service tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_email_dashboard_service.py::TestAutomationBugFixes -x -v`

Expected: all 5 tests pass.

- [ ] **Step 4: Run the full analytics test suite to verify no regressions**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/ -x -q --tb=short`

Expected: all tests pass (or only pre-existing failures unrelated to this change).

- [ ] **Step 5: Run lint**

Run: `cd backend && .venv/bin/ruff check src/modules/analytics/ --no-cache`

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/analytics/application/services/email_dashboard_service.py
git commit -m "fix(analytics): correct automation subscribers, completion rate, status; populate steps"
```

---

## Phase 2: Frontend — Types & API Mapper

### Task 6: Extend mail-types with AutomationStep

**Files:**
- Modify: `frontend/src/features/growth-studio/types/mail-types.ts:110-131`

- [ ] **Step 1: Replace the `EmailAutomation` interface block**

Find lines 110-131 (the Automations Tab section) and replace with:

```typescript
// ---------------------------------------------------------------------------
// Automations Tab
// ---------------------------------------------------------------------------

export type AutomationStepType = 'email' | 'delay' | 'condition';

export interface AutomationStep {
  stepId: string;
  stepNumber: number;
  type: AutomationStepType;
  subject: string | null;
  fromName: string | null;
  emailsSent: number;
  uniqueOpens: number;
  openRate: number;
  uniqueClicks: number;
  clickRate: number;
  unsubscribes: number;
  bounces: number;
  screenshotUrl: string | null;
  previewUrl: string | null;
  delayValue: number | null;
  delayUnit: string | null;
}

export interface EmailAutomation {
  automationId: string;
  name: string;
  automationType: string;
  status: string;
  activeSubscribers: number; // Now: completed + in_queue (ingresados)
  completed: number;
  emailsSent: number;
  openRate: number;
  clickRate: number;
  clickToOpenRate: number;
  completionRate: number;
  unsubscribes: number;
  steps: AutomationStep[];
}

export interface EmailAutomationsData {
  period: string;
  kpis: MetricKpiData[];
  automations: EmailAutomation[];
}
```

- [ ] **Step 2: Run type check**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -40`

Expected: errors in files that consume `EmailAutomation` (missing new fields). That's OK — we'll fix them in Task 7.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/types/mail-types.ts
git commit -m "feat(growth): add AutomationStep type and extend EmailAutomation"
```

---

### Task 7: Update API mapper for new fields

**Files:**
- Modify: `frontend/src/features/growth-studio/api/mail-api.ts:220-245`

- [ ] **Step 1: Add the step mapper and update `mapEmailAutomation`**

Locate the `mapEmailAutomation` function (around line 221) and replace it with:

```typescript
function mapAutomationStep(raw: Record<string, unknown>): AutomationStep {
  return {
    stepId: raw.step_id as string,
    stepNumber: raw.step_number as number,
    type: raw.type as 'email' | 'delay' | 'condition',
    subject: (raw.subject as string | null) ?? null,
    fromName: (raw.from_name as string | null) ?? null,
    emailsSent: (raw.emails_sent as number) ?? 0,
    uniqueOpens: (raw.unique_opens as number) ?? 0,
    openRate: (raw.open_rate as number) ?? 0,
    uniqueClicks: (raw.unique_clicks as number) ?? 0,
    clickRate: (raw.click_rate as number) ?? 0,
    unsubscribes: (raw.unsubscribes as number) ?? 0,
    bounces: (raw.bounces as number) ?? 0,
    screenshotUrl: (raw.screenshot_url as string | null) ?? null,
    previewUrl: (raw.preview_url as string | null) ?? null,
    delayValue: (raw.delay_value as number | null) ?? null,
    delayUnit: (raw.delay_unit as string | null) ?? null,
  };
}

function mapEmailAutomation(raw: Record<string, unknown>): EmailAutomation {
  const steps = (raw.steps as Array<Record<string, unknown>> | undefined) ?? [];
  return {
    automationId: raw.automation_id as string,
    name: raw.name as string,
    automationType: raw.automation_type as string,
    status: raw.status as string,
    activeSubscribers: raw.active_subscribers as number,
    completed: raw.completed as number,
    emailsSent: raw.emails_sent as number,
    openRate: raw.open_rate as number,
    clickRate: raw.click_rate as number,
    clickToOpenRate: (raw.click_to_open_rate as number) ?? 0,
    completionRate: raw.completion_rate as number,
    unsubscribes: (raw.unsubscribes as number) ?? 0,
    steps: steps.map(mapAutomationStep),
  };
}
```

- [ ] **Step 2: Add `AutomationStep` to the type imports at top of the file**

Find the import block (around line 9-29) and add `AutomationStep` to the mail-types imports:

```typescript
import type {
  EmailDashboardData,
  EmailCampaignsData,
  EmailAutomationsData,
  EmailAudienceData,
  EmailHealthData,
  EmailGrowthData,
  EmailHealthScore,
  EmailHealthSubScore,
  EmailCampaignSummary,
  CampaignsVsAutomations,
  EmailCampaign,
  EmailTypePerformance,
  EmailAutomation,
  AutomationStep,
  EmailEngagementSegment,
  SegmentTypeMatrixCell,
  EmailSourcePerformance,
  EngagementDecay,
  ActivityHeatmapCell,
  BounceBreakdown,
} from '../types/mail-types';
```

- [ ] **Step 3: Run type check**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep -E "mail-api|EmailAutomation" | head -20`

Expected: no errors in mail-api.ts (MailAutomatizacionesTab still has errors — fixed in Task 13).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/growth-studio/api/mail-api.ts
git commit -m "feat(growth): map new automation fields (ctor, unsubs, steps) in API response"
```

---

## Phase 3: Frontend — Utilities (TDD)

### Task 8: Create metric-info dictionary

**Files:**
- Create: `frontend/src/features/growth-studio/utils/automation-metric-info.ts`

- [ ] **Step 1: Create the file with the full dictionary**

Write:

```typescript
/**
 * Central dictionary of metric descriptions for info tooltips in the
 * Email Automations UI. Used by table headers, KPIs, pipeline nodes,
 * and sidebar metric boxes.
 */

export interface MetricInfo {
  title: string;
  description: string;
  formula?: string;
  interpret?: {
    good: string;
    mid: string;
    bad: string;
  };
}

export const AUTOMATION_METRIC_INFO: Record<string, MetricInfo> = {
  ingresados: {
    title: 'Ingresados',
    description:
      'Total de suscriptores que entraron a este flujo automatizado (completados + en cola actualmente).',
    formula: 'completados + en_cola',
    interpret: {
      good: 'Más ingresados = mayor alcance automatizado',
      mid: '',
      bad: '',
    },
  },
  completaron: {
    title: 'Completaron',
    description:
      'Suscriptores que recibieron TODOS los emails de la secuencia. El porcentaje muestra la tasa de completación.',
    formula: 'completados / ingresados × 100',
    interpret: {
      good: '>60% excelente retención',
      mid: '30-60% revisar contenido medio',
      bad: '<30% la secuencia pierde gente',
    },
  },
  openRate: {
    title: 'Open Rate',
    description:
      'Porcentaje de emails abiertos sobre el total entregado. Refleja la calidad de tus subject lines.',
    formula: 'emails abiertos / emails entregados × 100',
    interpret: {
      good: '>50% excelente',
      mid: '30-50% aceptable',
      bad: '<30% mejorar subjects',
    },
  },
  clickRate: {
    title: 'Click Rate',
    description:
      'Porcentaje de emails donde al menos un enlace fue clickeado. Mide si tu contenido genera acción.',
    formula: 'emails con click / emails entregados × 100',
    interpret: {
      good: '>5% muy bueno',
      mid: '2-5% promedio',
      bad: '<2% CTA no conecta',
    },
  },
  ctor: {
    title: 'Click-to-Open Rate (CTOR)',
    description:
      'De los que abrieron, ¿cuántos hicieron click? La métrica más pura de engagement — elimina el efecto del subject line.',
    formula: 'clicks únicos / aperturas únicas × 100',
    interpret: {
      good: '>15% contenido muy relevante',
      mid: '8-15% normal',
      bad: '<8% contenido no convence',
    },
  },
  unsubs: {
    title: 'Desuscripciones',
    description:
      'Personas que se desuscribieron durante esta automatización. Un número alto indica que el contenido no cumple la expectativa.',
    interpret: {
      good: '0-1 normal',
      mid: '2-3 monitorear',
      bad: '>3 revisar frecuencia y relevancia',
    },
  },
  salud: {
    title: 'Score de Salud',
    description:
      'Índice compuesto 0-100 que combina apertura, clicks, CTOR, completación y penaliza desuscripciones.',
    formula: '0.3×open + 0.25×click + 0.2×CTOR + 0.15×completion − 0.1×unsub_rate',
    interpret: {
      good: '>70 saludable',
      mid: '40-70 oportunidad de mejora',
      bad: '<40 acción urgente',
    },
  },
  dropoff: {
    title: 'Caída entre pasos',
    description:
      'Porcentaje de suscriptores que dejaron de recibir el siguiente email. Una caída alta indica que el contenido o el timing no funciona.',
    formula: '(1 − siguiente_enviados / actual_enviados) × 100',
    interpret: {
      good: '<10% secuencia saludable',
      mid: '10-30% aceptable',
      bad: '>30% problema serio',
    },
  },
  stepOpen: {
    title: 'Open Rate del email',
    description:
      'Porcentaje que abrió este email específico. Compara con otros pasos para detectar fatiga de secuencia.',
  },
  stepClick: {
    title: 'Click Rate del email',
    description:
      'Porcentaje que hizo click en este email. Click bajo con open alto = el CTA o contenido no convence.',
  },
  enviados: {
    title: 'Enviados',
    description: 'Emails entregados exitosamente a la bandeja del suscriptor.',
  },
  abiertos: {
    title: 'Abiertos',
    description:
      'Aperturas únicas. Cada suscriptor cuenta una sola vez aunque abra múltiples veces.',
  },
  clicks: {
    title: 'Clicks',
    description:
      'Clicks únicos en cualquier enlace del email. Cada suscriptor cuenta una vez.',
  },
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/growth-studio/utils/automation-metric-info.ts
git commit -m "feat(growth): add central metric info dictionary for automation tooltips"
```

---

### Task 9: Health score util — Write failing test

**Files:**
- Create: `frontend/src/features/growth-studio/utils/__tests__/automation-health.test.ts`

- [ ] **Step 1: Create the test file**

Write:

```typescript
import { describe, it, expect } from 'vitest';
import {
  computeHealthScore,
  computeDropoff,
  diagnoseStep,
  findBestStep,
  findAttentionStep,
} from '../automation-health';
import type { EmailAutomation, AutomationStep } from '../../types/mail-types';

function buildAutomation(overrides: Partial<EmailAutomation> = {}): EmailAutomation {
  return {
    automationId: 'a1',
    name: 'Test',
    automationType: 'welcome',
    status: 'active',
    activeSubscribers: 10,
    completed: 5,
    emailsSent: 20,
    openRate: 60,
    clickRate: 10,
    clickToOpenRate: 16.7,
    completionRate: 50,
    unsubscribes: 0,
    steps: [],
    ...overrides,
  };
}

function buildStep(overrides: Partial<AutomationStep> = {}): AutomationStep {
  return {
    stepId: 's1',
    stepNumber: 1,
    type: 'email',
    subject: 'Test email',
    fromName: 'Me',
    emailsSent: 10,
    uniqueOpens: 8,
    openRate: 80,
    uniqueClicks: 4,
    clickRate: 40,
    unsubscribes: 0,
    bounces: 0,
    screenshotUrl: null,
    previewUrl: null,
    delayValue: null,
    delayUnit: null,
    ...overrides,
  };
}

describe('computeHealthScore', () => {
  it('returns 0 when automation has no data', () => {
    const auto = buildAutomation({
      openRate: 0,
      clickRate: 0,
      clickToOpenRate: 0,
      completionRate: 0,
      unsubscribes: 0,
      emailsSent: 0,
    });
    expect(computeHealthScore(auto)).toBe(0);
  });

  it('returns high score (>70) for excellent automation', () => {
    const auto = buildAutomation({
      openRate: 90,
      clickRate: 30,
      clickToOpenRate: 33,
      completionRate: 80,
      unsubscribes: 0,
    });
    expect(computeHealthScore(auto)).toBeGreaterThan(70);
  });

  it('returns low score (<40) for poor automation', () => {
    const auto = buildAutomation({
      openRate: 10,
      clickRate: 0.5,
      clickToOpenRate: 2,
      completionRate: 5,
      unsubscribes: 5,
      emailsSent: 100,
    });
    expect(computeHealthScore(auto)).toBeLessThan(40);
  });

  it('penalizes high unsubscribe rate', () => {
    const baseline = buildAutomation({
      openRate: 60,
      clickRate: 10,
      clickToOpenRate: 16.7,
      completionRate: 50,
      unsubscribes: 0,
      emailsSent: 100,
    });
    const penalized = { ...baseline, unsubscribes: 10 };
    expect(computeHealthScore(penalized)).toBeLessThan(computeHealthScore(baseline));
  });
});

describe('computeDropoff', () => {
  it('returns 0 when both steps have same sent', () => {
    expect(computeDropoff(100, 100)).toBe(0);
  });

  it('returns 50 when half drop off', () => {
    expect(computeDropoff(100, 50)).toBe(50);
  });

  it('returns 0 when previous step had 0 sent (avoid div by zero)', () => {
    expect(computeDropoff(0, 0)).toBe(0);
  });

  it('returns 100 when all drop off', () => {
    expect(computeDropoff(100, 0)).toBe(100);
  });
});

describe('diagnoseStep', () => {
  it('flags high open + low click as weak CTA', () => {
    const step = buildStep({ openRate: 70, clickRate: 1 });
    const insights = diagnoseStep(step);
    expect(insights.some((i) => i.includes('CTA'))).toBe(true);
  });

  it('flags low open rate', () => {
    const step = buildStep({ openRate: 15, clickRate: 2 });
    const insights = diagnoseStep(step);
    expect(insights.some((i) => i.toLowerCase().includes('apertura'))).toBe(true);
  });

  it('flags high unsubscribes', () => {
    const step = buildStep({ unsubscribes: 5, emailsSent: 20 });
    const insights = diagnoseStep(step);
    expect(insights.some((i) => i.toLowerCase().includes('desuscrip'))).toBe(true);
  });

  it('flags steep drop vs previous step', () => {
    const prev = buildStep({ openRate: 90 });
    const current = buildStep({ openRate: 30 });
    const insights = diagnoseStep(current, prev);
    expect(insights.some((i) => i.toLowerCase().includes('caída'))).toBe(true);
  });

  it('returns empty for healthy step', () => {
    const step = buildStep({ openRate: 70, clickRate: 15, unsubscribes: 0 });
    expect(diagnoseStep(step)).toEqual([]);
  });
});

describe('findBestStep', () => {
  it('returns null for empty list', () => {
    expect(findBestStep([])).toBeNull();
  });

  it('picks step with highest open × click product', () => {
    const steps = [
      buildStep({ stepId: 's1', openRate: 80, clickRate: 10 }), // score 800
      buildStep({ stepId: 's2', openRate: 60, clickRate: 20 }), // score 1200
      buildStep({ stepId: 's3', openRate: 70, clickRate: 5 }), // score 350
    ];
    expect(findBestStep(steps)?.stepId).toBe('s2');
  });

  it('ignores non-email steps', () => {
    const steps = [
      buildStep({ stepId: 's1', type: 'delay', openRate: 100, clickRate: 100 }),
      buildStep({ stepId: 's2', type: 'email', openRate: 50, clickRate: 5 }),
    ];
    expect(findBestStep(steps)?.stepId).toBe('s2');
  });
});

describe('findAttentionStep', () => {
  it('returns null when all emails perform OK', () => {
    const steps = [
      buildStep({ openRate: 60, clickRate: 10 }),
      buildStep({ openRate: 55, clickRate: 8 }),
    ];
    expect(findAttentionStep(steps)).toBeNull();
  });

  it('flags step with 0 click rate', () => {
    const steps = [
      buildStep({ stepId: 's1', openRate: 60, clickRate: 10 }),
      buildStep({ stepId: 's2', openRate: 40, clickRate: 0 }),
    ];
    expect(findAttentionStep(steps)?.stepId).toBe('s2');
  });

  it('flags step with very low open rate', () => {
    const steps = [
      buildStep({ stepId: 's1', openRate: 80, clickRate: 15 }),
      buildStep({ stepId: 's2', openRate: 10, clickRate: 2 }),
    ];
    expect(findAttentionStep(steps)?.stepId).toBe('s2');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend && npx vitest run src/features/growth-studio/utils/__tests__/automation-health.test.ts`

Expected: FAIL — `automation-health.ts` doesn't exist yet.

- [ ] **Step 3: Commit the failing test**

```bash
git add frontend/src/features/growth-studio/utils/__tests__/automation-health.test.ts
git commit -m "test(growth): add failing tests for automation health utilities"
```

---

### Task 10: Health score util — Implement

**Files:**
- Create: `frontend/src/features/growth-studio/utils/automation-health.ts`

- [ ] **Step 1: Create the util file**

Write:

```typescript
/**
 * Utilities for automation health scoring, drop-off computation,
 * step diagnosis, and best/attention step detection.
 *
 * Pure functions — no React dependencies. Fully testable in isolation.
 */

import type { EmailAutomation, AutomationStep } from '../types/mail-types';

/**
 * Clamp a value to [0, 100].
 */
function clamp100(value: number): number {
  return Math.max(0, Math.min(100, value));
}

/**
 * Normalize a value to a 0-100 scale given a reference maximum.
 * Values >= refMax map to 100; negatives clamp to 0.
 */
function normalize(value: number, refMax: number): number {
  if (refMax <= 0) return 0;
  return clamp100((value / refMax) * 100);
}

/**
 * Compute composite health score 0-100 for an automation.
 *
 * Weights:
 *   0.30 × open_rate (ref max 100%)
 *   0.25 × click_rate (ref max 30%)
 *   0.20 × CTOR (ref max 50%)
 *   0.15 × completion_rate (ref max 100%)
 *   −0.10 × unsub_rate (ref max 5%)
 *
 * Returns 0 if the automation has no emails sent (no data yet).
 */
export function computeHealthScore(auto: EmailAutomation): number {
  if (auto.emailsSent === 0) return 0;

  const unsubRate = auto.emailsSent > 0 ? (auto.unsubscribes / auto.emailsSent) * 100 : 0;

  const score =
    0.3 * normalize(auto.openRate, 100) +
    0.25 * normalize(auto.clickRate, 30) +
    0.2 * normalize(auto.clickToOpenRate, 50) +
    0.15 * normalize(auto.completionRate, 100) -
    0.1 * normalize(unsubRate, 5);

  return Math.round(clamp100(score));
}

/**
 * Compute drop-off percentage between two consecutive steps.
 */
export function computeDropoff(previousSent: number, currentSent: number): number {
  if (previousSent <= 0) return 0;
  const dropoff = (1 - currentSent / previousSent) * 100;
  return Math.round(clamp100(dropoff));
}

/**
 * Generate actionable insights for an individual email step.
 *
 * Rules (deterministic, no LLM):
 *  - High open + low click → weak CTA
 *  - Low open → subject/timing issue
 *  - High unsub → content mismatch
 *  - Steep drop vs previous → sequence fatigue
 */
export function diagnoseStep(
  step: AutomationStep,
  previousStep?: AutomationStep,
): string[] {
  const insights: string[] = [];
  if (step.type !== 'email') return insights;

  if (step.openRate > 50 && step.clickRate < 2) {
    insights.push(
      'Subject line efectivo pero CTA débil — prueba un botón más visible o copy más directo',
    );
  }

  if (step.openRate < 25 && step.emailsSent > 0) {
    insights.push(
      'Apertura baja — prueba un subject más específico, personalizado o cambia el horario de envío',
    );
  }

  const unsubRate =
    step.emailsSent > 0 ? (step.unsubscribes / step.emailsSent) * 100 : 0;
  if (unsubRate > 5 || step.unsubscribes > 3) {
    insights.push(
      'Desuscripciones altas — el contenido no cumple la expectativa del suscriptor; revisa frecuencia y relevancia',
    );
  }

  if (
    previousStep &&
    previousStep.type === 'email' &&
    previousStep.openRate > 0 &&
    step.openRate < previousStep.openRate * 0.6
  ) {
    const dropPct = Math.round((1 - step.openRate / previousStep.openRate) * 100);
    insights.push(
      `Caída de ${dropPct}% en apertura vs email anterior — posible fatiga de secuencia o timing inadecuado`,
    );
  }

  return insights;
}

/**
 * Score a step for best/worst ranking.
 * Uses open × click product as a proxy for engagement quality.
 */
function scoreStep(step: AutomationStep): number {
  if (step.type !== 'email') return -1;
  return step.openRate * step.clickRate;
}

/**
 * Find the best-performing email step in a sequence.
 * Returns null if the sequence has no email steps.
 */
export function findBestStep(steps: AutomationStep[]): AutomationStep | null {
  const emailSteps = steps.filter((s) => s.type === 'email');
  if (emailSteps.length === 0) return null;

  let best = emailSteps[0];
  let bestScore = scoreStep(best);
  for (const step of emailSteps.slice(1)) {
    const score = scoreStep(step);
    if (score > bestScore) {
      best = step;
      bestScore = score;
    }
  }
  return best;
}

/**
 * Find the email step that needs attention (worst performer).
 * Criteria: 0% click rate OR open rate < 20%. Returns null if all steps
 * are performing acceptably.
 */
export function findAttentionStep(steps: AutomationStep[]): AutomationStep | null {
  const emailSteps = steps.filter((s) => s.type === 'email');
  const problems = emailSteps.filter(
    (s) => s.clickRate === 0 || s.openRate < 20,
  );
  if (problems.length === 0) return null;

  // Pick the worst by open × click score (lowest)
  let worst = problems[0];
  let worstScore = scoreStep(worst);
  for (const step of problems.slice(1)) {
    const score = scoreStep(step);
    if (score < worstScore) {
      worst = step;
      worstScore = score;
    }
  }
  return worst;
}
```

- [ ] **Step 2: Run the health test**

Run: `cd frontend && npx vitest run src/features/growth-studio/utils/__tests__/automation-health.test.ts`

Expected: all tests pass.

- [ ] **Step 3: Run type check**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep automation-health`

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/growth-studio/utils/automation-health.ts
git commit -m "feat(growth): implement automation health score, dropoff, and step diagnosis utils"
```

---

## Phase 4: Frontend — UI Components

### Task 11: Create MetricInfoTooltip component

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/MetricInfoTooltip.tsx`

- [ ] **Step 1: Create the reusable tooltip component**

Write:

```tsx
'use client';

import { Info } from 'lucide-react';

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import type { MetricInfo } from '../../../../../utils/automation-metric-info';

interface MetricInfoTooltipProps {
  info: MetricInfo;
  iconSize?: 'xs' | 'sm';
  side?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
}

/**
 * Reusable info tooltip (ⓘ) showing title, description, formula, and
 * interpretation thresholds (good/mid/bad).
 *
 * Used on every metric in the Automations UI: table headers, KPI cards,
 * pipeline nodes, and sidebar metric boxes.
 */
export function MetricInfoTooltip({
  info,
  iconSize = 'sm',
  side = 'top',
  className,
}: MetricInfoTooltipProps) {
  const iconClass =
    iconSize === 'xs' ? 'h-2.5 w-2.5' : 'h-3 w-3';

  return (
    <TooltipProvider delayDuration={150}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            onClick={(e) => e.stopPropagation()}
            className={cn(
              'inline-flex items-center justify-center rounded-full text-muted-foreground/60 hover:text-primary transition-colors cursor-help align-middle',
              className,
            )}
            aria-label={`Información sobre ${info.title}`}
          >
            <Info className={iconClass} />
          </button>
        </TooltipTrigger>
        <TooltipContent side={side} className="max-w-[260px] p-3">
          <div className="space-y-1.5">
            <p className="font-semibold text-xs">{info.title}</p>
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              {info.description}
            </p>
            {info.formula && (
              <p className="text-[10px] font-mono bg-primary/10 text-primary rounded px-2 py-1">
                {info.formula}
              </p>
            )}
            {info.interpret &&
              (info.interpret.good ||
                info.interpret.mid ||
                info.interpret.bad) && (
                <div className="text-[10px] border-t border-border pt-1.5 space-y-0.5">
                  {info.interpret.good && (
                    <p>
                      <span className="font-semibold text-emerald-500">✓</span>{' '}
                      {info.interpret.good}
                    </p>
                  )}
                  {info.interpret.mid && (
                    <p>
                      <span className="font-semibold text-amber-500">~</span>{' '}
                      {info.interpret.mid}
                    </p>
                  )}
                  {info.interpret.bad && (
                    <p>
                      <span className="font-semibold text-red-500">✗</span>{' '}
                      {info.interpret.bad}
                    </p>
                  )}
                </div>
              )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
```

- [ ] **Step 2: Run type check**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep MetricInfoTooltip`

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/MetricInfoTooltip.tsx
git commit -m "feat(growth): add reusable MetricInfoTooltip component for automation metrics"
```

---

### Task 12: Write test for AutomationPipeline

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/__tests__/AutomationPipeline.test.tsx`

- [ ] **Step 1: Create the test file**

Write:

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import { AutomationPipeline } from '../AutomationPipeline';
import type { AutomationStep } from '../../../../../../types/mail-types';

function buildEmailStep(overrides: Partial<AutomationStep> = {}): AutomationStep {
  return {
    stepId: 's1',
    stepNumber: 1,
    type: 'email',
    subject: 'Bienvenida',
    fromName: 'Equipo',
    emailsSent: 10,
    uniqueOpens: 8,
    openRate: 80,
    uniqueClicks: 4,
    clickRate: 40,
    unsubscribes: 0,
    bounces: 0,
    screenshotUrl: null,
    previewUrl: null,
    delayValue: null,
    delayUnit: null,
    ...overrides,
  };
}

function buildDelayStep(days = 2): AutomationStep {
  return {
    stepId: `delay-${days}`,
    stepNumber: 2,
    type: 'delay',
    subject: null,
    fromName: null,
    emailsSent: 0,
    uniqueOpens: 0,
    openRate: 0,
    uniqueClicks: 0,
    clickRate: 0,
    unsubscribes: 0,
    bounces: 0,
    screenshotUrl: null,
    previewUrl: null,
    delayValue: days,
    delayUnit: 'days',
  };
}

describe('AutomationPipeline', () => {
  it('renders a card for each email step with subject and metrics', () => {
    const steps = [
      buildEmailStep({ stepId: 's1', subject: 'Hola', openRate: 80, clickRate: 40 }),
      buildEmailStep({ stepId: 's2', subject: 'Adiós', openRate: 60, clickRate: 20 }),
    ];
    render(<AutomationPipeline steps={steps} onStepClick={() => {}} />);

    expect(screen.getByText('Hola')).toBeInTheDocument();
    expect(screen.getByText('Adiós')).toBeInTheDocument();
    expect(screen.getByText('80.0%')).toBeInTheDocument();
    expect(screen.getByText('60.0%')).toBeInTheDocument();
  });

  it('shows best performer badge on highest scoring email', () => {
    const steps = [
      buildEmailStep({ stepId: 's1', subject: 'A', openRate: 90, clickRate: 20 }),
      buildEmailStep({ stepId: 's2', subject: 'B', openRate: 50, clickRate: 5 }),
    ];
    render(<AutomationPipeline steps={steps} onStepClick={() => {}} />);

    const badges = screen.getAllByText(/Mejor/i);
    expect(badges.length).toBeGreaterThanOrEqual(1);
  });

  it('shows attention badge on underperforming email', () => {
    const steps = [
      buildEmailStep({ stepId: 's1', subject: 'Good', openRate: 80, clickRate: 25 }),
      buildEmailStep({ stepId: 's2', subject: 'Bad', openRate: 10, clickRate: 0 }),
    ];
    render(<AutomationPipeline steps={steps} onStepClick={() => {}} />);

    expect(screen.getByText(/Atención/i)).toBeInTheDocument();
  });

  it('renders delay steps between emails', () => {
    const steps = [
      buildEmailStep({ stepId: 's1' }),
      buildDelayStep(3),
      buildEmailStep({ stepId: 's2' }),
    ];
    render(<AutomationPipeline steps={steps} onStepClick={() => {}} />);

    expect(screen.getByText(/3 días/i)).toBeInTheDocument();
  });

  it('calls onStepClick with the step when an email card is clicked', () => {
    const handler = vi.fn();
    const step = buildEmailStep({ stepId: 's1', subject: 'Click me' });
    render(<AutomationPipeline steps={[step]} onStepClick={handler} />);

    fireEvent.click(screen.getByText('Click me'));
    expect(handler).toHaveBeenCalledWith(step);
  });

  it('renders AI insight when sequence has drop-off', () => {
    const steps = [
      buildEmailStep({ stepId: 's1', emailsSent: 10, openRate: 80, clickRate: 30 }),
      buildEmailStep({ stepId: 's2', emailsSent: 2, openRate: 20, clickRate: 0 }),
    ];
    render(<AutomationPipeline steps={steps} onStepClick={() => {}} />);

    // Insight container should be present
    expect(screen.getByTestId('automation-ai-insight')).toBeInTheDocument();
  });

  it('renders empty state when there are no email steps', () => {
    render(<AutomationPipeline steps={[]} onStepClick={() => {}} />);
    expect(screen.getByText(/sin pasos/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend && npx vitest run src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/__tests__/AutomationPipeline.test.tsx`

Expected: FAIL — `AutomationPipeline` component doesn't exist.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/__tests__/AutomationPipeline.test.tsx
git commit -m "test(growth): add failing tests for AutomationPipeline component"
```

---

### Task 13: Implement AutomationPipeline

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/AutomationPipeline.tsx`

- [ ] **Step 1: Create the component**

Write:

```tsx
'use client';

import { Clock, Sparkles, AlertTriangle, TrendingDown } from 'lucide-react';

import { cn } from '@/lib/utils';
import {
  computeDropoff,
  diagnoseStep,
  findBestStep,
  findAttentionStep,
} from '../../../../../utils/automation-health';
import { AUTOMATION_METRIC_INFO } from '../../../../../utils/automation-metric-info';
import type { AutomationStep } from '../../../../../types/mail-types';
import { MetricInfoTooltip } from './MetricInfoTooltip';

interface AutomationPipelineProps {
  steps: AutomationStep[];
  onStepClick: (step: AutomationStep) => void;
}

/**
 * Horizontal visual pipeline of an automation's email sequence.
 *
 * Renders each email as a card with key metrics, connectors between steps
 * showing delay and drop-off, best/attention badges, and an AI insight
 * summary computed from the deterministic diagnosis rules.
 */
export function AutomationPipeline({
  steps,
  onStepClick,
}: AutomationPipelineProps) {
  const emailSteps = steps.filter((s) => s.type === 'email');

  if (emailSteps.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border/40 bg-muted/10 py-8 text-center">
        <p className="text-xs text-muted-foreground">
          Sin pasos registrados para esta automatización.
        </p>
      </div>
    );
  }

  const bestStep = findBestStep(emailSteps);
  const attentionStep = findAttentionStep(emailSteps);
  const insights = computeSequenceInsights(emailSteps);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-muted-foreground">
          Secuencia de emails — {emailSteps.length} paso
          {emailSteps.length === 1 ? '' : 's'}
        </h4>
        {insights.headline && (
          <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
            {insights.headlineIcon}
            {insights.headline}
          </span>
        )}
      </div>

      {/* Horizontal pipeline */}
      <div className="flex items-stretch gap-0 overflow-x-auto pb-2">
        {steps.map((step, idx) => {
          if (step.type === 'delay') {
            return <DelayConnector key={step.stepId} step={step} />;
          }

          // Email step
          const prevEmailStep = findPreviousEmail(steps, idx);
          const dropoff = prevEmailStep
            ? computeDropoff(prevEmailStep.emailsSent, step.emailsSent)
            : null;

          return (
            <div
              key={step.stepId}
              className="flex items-stretch"
            >
              {prevEmailStep && !hasDelayBefore(steps, idx) && (
                <StepConnector dropoff={dropoff} delay={null} />
              )}
              <EmailNode
                step={step}
                isBest={bestStep?.stepId === step.stepId}
                isAttention={attentionStep?.stepId === step.stepId}
                onClick={() => onStepClick(step)}
              />
            </div>
          );
        })}
      </div>

      {/* Funnel bar */}
      <FunnelBar steps={emailSteps} />

      {/* AI insight */}
      {insights.messages.length > 0 && (
        <div
          data-testid="automation-ai-insight"
          className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 flex gap-2.5"
        >
          <Sparkles className="h-4 w-4 text-primary mt-0.5 shrink-0" />
          <div className="text-[12px] text-muted-foreground leading-relaxed space-y-1">
            {insights.messages.map((msg, i) => (
              <p key={i}>{msg}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Sub-components ─────────────────────────────────────────────────

interface EmailNodeProps {
  step: AutomationStep;
  isBest: boolean;
  isAttention: boolean;
  onClick: () => void;
}

function EmailNode({ step, isBest, isAttention, onClick }: EmailNodeProps) {
  const openClass =
    step.openRate >= 50
      ? 'text-emerald-500'
      : step.openRate >= 30
        ? 'text-amber-500'
        : 'text-red-500';
  const clickClass =
    step.clickRate >= 5
      ? 'text-emerald-500'
      : step.clickRate >= 2
        ? 'text-amber-500'
        : 'text-red-500';

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'relative w-[190px] shrink-0 rounded-lg border bg-card p-3.5 text-left transition-all cursor-pointer',
        'hover:border-primary hover:shadow-[0_0_0_1px_hsl(var(--primary)),0_4px_20px_rgba(99,102,241,0.15)]',
        isBest && 'border-emerald-500 shadow-[0_0_0_1px_rgba(16,185,129,0.3)]',
        isAttention &&
          !isBest &&
          'border-red-500 shadow-[0_0_0_1px_rgba(239,68,68,0.2)]',
      )}
    >
      {isBest && (
        <span className="absolute -top-2 right-3 rounded-full bg-emerald-500 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-black">
          ★ Mejor
        </span>
      )}
      {isAttention && !isBest && (
        <span className="absolute -top-2 right-3 rounded-full bg-red-500 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-white">
          ⚡ Atención
        </span>
      )}

      <div className="flex items-center justify-between text-[9px] uppercase tracking-wide text-muted-foreground">
        <span>Email {step.stepNumber}</span>
        <span>{step.emailsSent} enviados</span>
      </div>
      <p className="mt-1 truncate text-xs font-medium">
        {step.subject || '(sin asunto)'}
      </p>

      <div className="mt-2.5 grid grid-cols-2 gap-1.5">
        <div className="rounded bg-muted/20 py-1 text-center">
          <p className={cn('text-sm font-bold tabular-nums', openClass)}>
            {step.openRate.toFixed(1)}%
          </p>
          <div className="flex items-center justify-center gap-0.5 text-[9px] uppercase text-muted-foreground">
            Open
            <MetricInfoTooltip
              info={AUTOMATION_METRIC_INFO.stepOpen}
              iconSize="xs"
            />
          </div>
        </div>
        <div className="rounded bg-muted/20 py-1 text-center">
          <p className={cn('text-sm font-bold tabular-nums', clickClass)}>
            {step.clickRate.toFixed(1)}%
          </p>
          <div className="flex items-center justify-center gap-0.5 text-[9px] uppercase text-muted-foreground">
            Click
            <MetricInfoTooltip
              info={AUTOMATION_METRIC_INFO.stepClick}
              iconSize="xs"
            />
          </div>
        </div>
      </div>
    </button>
  );
}

interface StepConnectorProps {
  dropoff: number | null;
  delay: { value: number; unit: string } | null;
}

function StepConnector({ dropoff, delay }: StepConnectorProps) {
  const dropoffClass =
    dropoff === null
      ? 'text-muted-foreground'
      : dropoff < 10
        ? 'text-emerald-500'
        : dropoff < 30
          ? 'text-amber-500'
          : 'text-red-500';

  return (
    <div className="flex min-w-[72px] flex-col items-center justify-center px-2">
      <div className="relative h-0.5 w-full bg-border">
        <span className="absolute -right-1 -top-1 h-0 w-0 border-y-[4px] border-l-[6px] border-y-transparent border-l-border" />
      </div>
      <div className="mt-1.5 text-center space-y-0.5">
        {delay && (
          <p className="flex items-center gap-0.5 text-[10px] text-muted-foreground whitespace-nowrap">
            <Clock className="h-2.5 w-2.5" />
            {delay.value} {delay.unit}
          </p>
        )}
        {dropoff !== null && (
          <p
            className={cn(
              'flex items-center justify-center gap-0.5 text-[10px] font-semibold whitespace-nowrap',
              dropoffClass,
            )}
          >
            −{dropoff}%
            <MetricInfoTooltip info={AUTOMATION_METRIC_INFO.dropoff} iconSize="xs" />
          </p>
        )}
      </div>
    </div>
  );
}

function DelayConnector({ step }: { step: AutomationStep }) {
  return (
    <div className="flex min-w-[72px] flex-col items-center justify-center px-2">
      <div className="relative h-0.5 w-full bg-border">
        <span className="absolute -right-1 -top-1 h-0 w-0 border-y-[4px] border-l-[6px] border-y-transparent border-l-border" />
      </div>
      <p className="mt-1.5 flex items-center gap-1 text-[10px] text-muted-foreground whitespace-nowrap">
        <Clock className="h-2.5 w-2.5" />
        {step.delayValue ?? 0} {step.delayUnit ?? ''}
      </p>
    </div>
  );
}

interface FunnelBarProps {
  steps: AutomationStep[];
}

function FunnelBar({ steps }: FunnelBarProps) {
  if (steps.length === 0) return null;
  const maxSent = Math.max(...steps.map((s) => s.emailsSent), 1);

  return (
    <div>
      <div className="flex h-1.5 overflow-hidden rounded bg-muted/20">
        {steps.map((s) => {
          const width = (s.emailsSent / maxSent) * 100;
          const color =
            s.openRate >= 50
              ? 'bg-emerald-500/70'
              : s.openRate >= 30
                ? 'bg-amber-500/70'
                : 'bg-red-500/70';
          return (
            <div
              key={s.stepId}
              className={cn('h-full transition-all', color)}
              style={{ width: `${width}%` }}
            />
          );
        })}
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-muted-foreground">
        <span>{steps[0].emailsSent} enviaron primer email</span>
        <span>{steps[steps.length - 1].emailsSent} recibieron último</span>
      </div>
    </div>
  );
}

// ─── Helpers ────────────────────────────────────────────────────────

function findPreviousEmail(
  steps: AutomationStep[],
  currentIdx: number,
): AutomationStep | null {
  for (let i = currentIdx - 1; i >= 0; i--) {
    if (steps[i].type === 'email') return steps[i];
  }
  return null;
}

function hasDelayBefore(steps: AutomationStep[], currentIdx: number): boolean {
  if (currentIdx === 0) return false;
  return steps[currentIdx - 1].type === 'delay';
}

interface SequenceInsights {
  headline: string | null;
  headlineIcon: React.ReactNode;
  messages: string[];
}

function computeSequenceInsights(emailSteps: AutomationStep[]): SequenceInsights {
  const messages: string[] = [];
  let headline: string | null = null;
  let headlineIcon: React.ReactNode = null;

  if (emailSteps.length === 0) {
    return { headline: null, headlineIcon: null, messages: [] };
  }

  // Aggregate per-step diagnosis
  for (let i = 0; i < emailSteps.length; i++) {
    const prev = i > 0 ? emailSteps[i - 1] : undefined;
    const stepInsights = diagnoseStep(emailSteps[i], prev);
    for (const insight of stepInsights) {
      const prefix = `Email ${emailSteps[i].stepNumber}:`;
      messages.push(`${prefix} ${insight}`);
    }
  }

  // Compute headline
  const totalEmailSent = emailSteps.reduce((sum, s) => sum + s.emailsSent, 0);
  if (totalEmailSent > 0) {
    const firstSent = emailSteps[0].emailsSent;
    const lastSent = emailSteps[emailSteps.length - 1].emailsSent;
    if (firstSent > 0 && lastSent / firstSent < 0.5 && emailSteps.length > 1) {
      const dropPct = Math.round((1 - lastSent / firstSent) * 100);
      headline = `Engagement cae ${dropPct}% a lo largo de la secuencia`;
      headlineIcon = <TrendingDown className="h-3 w-3 text-red-500" />;
    } else if (messages.length === 0) {
      headline = 'Secuencia saludable — replica este formato';
      headlineIcon = <Sparkles className="h-3 w-3 text-emerald-500" />;
    } else {
      headline = `${messages.length} oportunidad${messages.length === 1 ? '' : 'es'} de mejora`;
      headlineIcon = <AlertTriangle className="h-3 w-3 text-amber-500" />;
    }
  }

  return { headline, headlineIcon, messages };
}
```

- [ ] **Step 2: Run the test**

Run: `cd frontend && npx vitest run src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/__tests__/AutomationPipeline.test.tsx`

Expected: all tests pass.

- [ ] **Step 3: Run type check**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep -E "AutomationPipeline" | head -10`

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/AutomationPipeline.tsx
git commit -m "feat(growth): implement AutomationPipeline with visual email sequence and drop-off"
```

---

### Task 14: Write test for AutomationStepSidebar

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/__tests__/AutomationStepSidebar.test.tsx`

- [ ] **Step 1: Create the test file**

Write:

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

import { AutomationStepSidebar } from '../AutomationStepSidebar';
import type { AutomationStep } from '../../../../../../types/mail-types';

function buildStep(overrides: Partial<AutomationStep> = {}): AutomationStep {
  return {
    stepId: 's1',
    stepNumber: 1,
    type: 'email',
    subject: 'Test Subject',
    fromName: 'Visionarias',
    emailsSent: 10,
    uniqueOpens: 8,
    openRate: 80,
    uniqueClicks: 4,
    clickRate: 40,
    unsubscribes: 1,
    bounces: 0,
    screenshotUrl: null,
    previewUrl: null,
    delayValue: null,
    delayUnit: null,
    ...overrides,
  };
}

describe('AutomationStepSidebar', () => {
  it('does not render content when step is null', () => {
    const { container } = render(
      <AutomationStepSidebar
        step={null}
        automationName="Test automation"
        totalSteps={3}
        previousStep={null}
        onClose={() => {}}
      />,
    );
    // Panel is closed — no visible step data
    expect(container.textContent).not.toContain('Test Subject');
  });

  it('renders step subject and context in header', () => {
    const step = buildStep({ subject: 'Mi email', stepNumber: 2 });
    render(
      <AutomationStepSidebar
        step={step}
        automationName="BIENVENIDA"
        totalSteps={4}
        previousStep={null}
        onClose={() => {}}
      />,
    );
    expect(screen.getByText('Mi email')).toBeInTheDocument();
    expect(screen.getByText(/Email 2 de 4/i)).toBeInTheDocument();
    expect(screen.getByText(/BIENVENIDA/)).toBeInTheDocument();
  });

  it('renders all six metric boxes (enviados, abiertos, clicks, open/click/ctor)', () => {
    const step = buildStep({
      emailsSent: 100,
      uniqueOpens: 80,
      uniqueClicks: 20,
      openRate: 80,
      clickRate: 20,
    });
    render(
      <AutomationStepSidebar
        step={step}
        automationName="Test"
        totalSteps={1}
        previousStep={null}
        onClose={() => {}}
      />,
    );
    expect(screen.getByText('100')).toBeInTheDocument(); // enviados
    expect(screen.getByText('80')).toBeInTheDocument(); // abiertos
    expect(screen.getByText('20')).toBeInTheDocument(); // clicks
    expect(screen.getByText('80.0%')).toBeInTheDocument(); // open rate
    expect(screen.getByText('20.0%')).toBeInTheDocument(); // click rate
    // CTOR = clicks/opens = 20/80 = 25%
    expect(screen.getByText('25.0%')).toBeInTheDocument();
  });

  it('renders "ver email completo" link when previewUrl exists', () => {
    const step = buildStep({ previewUrl: 'https://preview.example' });
    render(
      <AutomationStepSidebar
        step={step}
        automationName="Test"
        totalSteps={1}
        previousStep={null}
        onClose={() => {}}
      />,
    );
    const link = screen.getByRole('link', { name: /email completo/i });
    expect(link).toHaveAttribute('href', 'https://preview.example');
  });

  it('renders AI diagnosis when step has issues', () => {
    const step = buildStep({ openRate: 70, clickRate: 0.5, emailsSent: 100 });
    render(
      <AutomationStepSidebar
        step={step}
        automationName="Test"
        totalSteps={1}
        previousStep={null}
        onClose={() => {}}
      />,
    );
    expect(screen.getByText(/CTA/i)).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const handler = vi.fn();
    const step = buildStep();
    render(
      <AutomationStepSidebar
        step={step}
        automationName="Test"
        totalSteps={1}
        previousStep={null}
        onClose={handler}
      />,
    );
    const closeBtn = screen.getByRole('button', { name: /cerrar/i });
    closeBtn.click();
    expect(handler).toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend && npx vitest run src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/__tests__/AutomationStepSidebar.test.tsx`

Expected: FAIL — component doesn't exist.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/__tests__/AutomationStepSidebar.test.tsx
git commit -m "test(growth): add failing tests for AutomationStepSidebar"
```

---

### Task 15: Implement AutomationStepSidebar

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/AutomationStepSidebar.tsx`

- [ ] **Step 1: Create the sidebar component**

Write:

```tsx
'use client';

import { ExternalLink, Sparkles } from 'lucide-react';

import {
  DetailPanel,
  DetailPanelHeader,
  DetailPanelTitle,
  DetailPanelClose,
} from '@/components/ui/detail-panel';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import { diagnoseStep } from '../../../../../utils/automation-health';
import { AUTOMATION_METRIC_INFO } from '../../../../../utils/automation-metric-info';
import type { AutomationStep } from '../../../../../types/mail-types';
import { MetricInfoTooltip } from './MetricInfoTooltip';

interface AutomationStepSidebarProps {
  step: AutomationStep | null;
  automationName: string;
  totalSteps: number;
  previousStep: AutomationStep | null;
  onClose: () => void;
}

// Industry benchmarks (source: Mailchimp/GetResponse 2025)
const BENCHMARKS = {
  openRate: 21.5,
  clickRate: 2.3,
  ctor: 10.5,
  unsubRate: 0.26,
  bounceRate: 0.58,
};

/**
 * DetailPanel sidebar showing deep-dive metrics for a single email step
 * within an automation. Includes metrics grid, benchmark comparison,
 * preview link, AI diagnosis, and email metadata.
 */
export function AutomationStepSidebar({
  step,
  automationName,
  totalSteps,
  previousStep,
  onClose,
}: AutomationStepSidebarProps) {
  const isOpen = step !== null;

  return (
    <DetailPanel open={isOpen} onClose={onClose} size="md">
      {step && (
        <>
          <DetailPanelHeader>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <DetailPanelTitle className="truncate">
                  {step.subject || '(sin asunto)'}
                </DetailPanelTitle>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Email {step.stepNumber} de {totalSteps} · {automationName}
                </p>
              </div>
              <DetailPanelClose onClose={onClose} />
            </div>
          </DetailPanelHeader>

          <div className="px-6 pb-6">
            <Separator className="my-4" />
            <MetricsSection step={step} />
            <Separator className="my-5" />
            <BenchmarksSection step={step} />
            {step.previewUrl && (
              <>
                <Separator className="my-5" />
                <PreviewSection step={step} />
              </>
            )}
            <Separator className="my-5" />
            <DiagnosisSection step={step} previousStep={previousStep} />
            <Separator className="my-5" />
            <DetailsSection step={step} totalSteps={totalSteps} />
          </div>
        </>
      )}
    </DetailPanel>
  );
}

// ─── Sections ───────────────────────────────────────────────────────

function MetricsSection({ step }: { step: AutomationStep }) {
  const ctor =
    step.uniqueOpens > 0 ? (step.uniqueClicks / step.uniqueOpens) * 100 : 0;

  const openClass = colorForRate(step.openRate, 50, 30);
  const clickClass = colorForRate(step.clickRate, 5, 2);
  const ctorClass = colorForRate(ctor, 15, 8);

  return (
    <section>
      <h4 className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Métricas de este email
      </h4>
      <div className="grid grid-cols-3 gap-2">
        <MetricBox
          value={String(step.emailsSent)}
          label="Enviados"
          info={AUTOMATION_METRIC_INFO.enviados}
        />
        <MetricBox
          value={String(step.uniqueOpens)}
          label="Abiertos"
          info={AUTOMATION_METRIC_INFO.abiertos}
        />
        <MetricBox
          value={String(step.uniqueClicks)}
          label="Clicks"
          info={AUTOMATION_METRIC_INFO.clicks}
        />
        <MetricBox
          value={`${step.openRate.toFixed(1)}%`}
          label="Open Rate"
          valueClass={openClass}
          info={AUTOMATION_METRIC_INFO.openRate}
        />
        <MetricBox
          value={`${step.clickRate.toFixed(1)}%`}
          label="Click Rate"
          valueClass={clickClass}
          info={AUTOMATION_METRIC_INFO.clickRate}
        />
        <MetricBox
          value={`${ctor.toFixed(1)}%`}
          label="CTOR"
          valueClass={ctorClass}
          info={AUTOMATION_METRIC_INFO.ctor}
        />
      </div>
    </section>
  );
}

function BenchmarksSection({ step }: { step: AutomationStep }) {
  const ctor =
    step.uniqueOpens > 0 ? (step.uniqueClicks / step.uniqueOpens) * 100 : 0;
  const unsubRate =
    step.emailsSent > 0 ? (step.unsubscribes / step.emailsSent) * 100 : 0;
  const bounceRate =
    step.emailsSent > 0 ? (step.bounces / step.emailsSent) * 100 : 0;

  const rows = [
    { label: 'Open Rate', value: step.openRate, benchmark: BENCHMARKS.openRate, suffix: '%', higherBetter: true, info: AUTOMATION_METRIC_INFO.openRate },
    { label: 'Click Rate', value: step.clickRate, benchmark: BENCHMARKS.clickRate, suffix: '%', higherBetter: true, info: AUTOMATION_METRIC_INFO.clickRate },
    { label: 'CTOR', value: ctor, benchmark: BENCHMARKS.ctor, suffix: '%', higherBetter: true, info: AUTOMATION_METRIC_INFO.ctor },
    { label: 'Desuscripciones', value: unsubRate, benchmark: BENCHMARKS.unsubRate, suffix: '%', higherBetter: false, info: AUTOMATION_METRIC_INFO.unsubs },
    { label: 'Rebotes', value: bounceRate, benchmark: BENCHMARKS.bounceRate, suffix: '%', higherBetter: false, info: { title: 'Rebotes', description: 'Promedio industria: 0.58%. Rebotes altos = lista desactualizada o emails inválidos. Afecta la reputación del dominio.' } },
  ];

  return (
    <section>
      <h4 className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        vs Benchmarks de la Industria
      </h4>
      <div className="rounded-lg border bg-card p-3.5 space-y-2">
        {rows.map((row) => {
          const isBetter = row.higherBetter
            ? row.value >= row.benchmark
            : row.value <= row.benchmark;
          return (
            <div
              key={row.label}
              className="flex items-center justify-between text-xs border-b border-border/30 pb-2 last:border-0 last:pb-0"
            >
              <span className="flex items-center gap-1 text-muted-foreground">
                {row.label}
                <MetricInfoTooltip info={row.info} iconSize="xs" />
              </span>
              <span
                className={cn(
                  'font-semibold tabular-nums',
                  isBetter ? 'text-emerald-500' : 'text-amber-500',
                )}
              >
                {row.value.toFixed(1)}
                {row.suffix}{' '}
                <span className="text-[10px] font-normal text-muted-foreground">
                  vs {row.benchmark}
                  {row.suffix}
                </span>
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function PreviewSection({ step }: { step: AutomationStep }) {
  return (
    <section>
      <h4 className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Vista previa del email
      </h4>
      <div className="rounded-lg border bg-card overflow-hidden">
        {step.screenshotUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={step.screenshotUrl}
            alt={`Vista previa de ${step.subject ?? 'email'}`}
            className="w-full object-cover max-h-[320px]"
          />
        ) : (
          <div className="flex h-32 items-center justify-center bg-muted/10 text-xs text-muted-foreground">
            Sin vista previa disponible
          </div>
        )}
        <div className="flex items-center justify-between border-t px-3 py-2">
          <a
            href={step.previewUrl ?? '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[11px] text-primary hover:underline"
          >
            <ExternalLink className="h-3 w-3" />
            Ver email completo en MailerLite
          </a>
        </div>
      </div>
    </section>
  );
}

function DiagnosisSection({
  step,
  previousStep,
}: {
  step: AutomationStep;
  previousStep: AutomationStep | null;
}) {
  const insights = diagnoseStep(step, previousStep ?? undefined);
  const hasIssues = insights.length > 0;

  return (
    <section>
      <h4 className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Diagnóstico Inteligente
      </h4>
      <div className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3">
        <h5 className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold text-primary">
          <Sparkles className="h-3 w-3" />
          Análisis de este email
        </h5>
        {hasIssues ? (
          <ul className="space-y-1.5">
            {insights.map((insight, i) => (
              <li
                key={i}
                className="pl-4 text-xs text-muted-foreground leading-relaxed relative"
              >
                <span className="absolute left-0 text-primary">→</span>
                {insight}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground">
            Este email tiene performance saludable. Considera replicar su estructura
            (subject, tono, CTA) en otros emails de la secuencia.
          </p>
        )}
      </div>
    </section>
  );
}

function DetailsSection({
  step,
  totalSteps,
}: {
  step: AutomationStep;
  totalSteps: number;
}) {
  return (
    <section>
      <h4 className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Detalles del email
      </h4>
      <div className="rounded-lg border bg-card p-3.5 space-y-2">
        <DetailRow label="Subject" value={step.subject ?? '—'} />
        <DetailRow label="De" value={step.fromName ?? '—'} />
        <DetailRow label="Posición" value={`${step.stepNumber} de ${totalSteps}`} />
      </div>
    </section>
  );
}

// ─── Reusable bits ──────────────────────────────────────────────────

function MetricBox({
  value,
  label,
  valueClass,
  info,
}: {
  value: string;
  label: string;
  valueClass?: string;
  info: { title: string; description: string; formula?: string; interpret?: { good: string; mid: string; bad: string } };
}) {
  return (
    <div className="rounded-lg border bg-card px-3 py-2.5 text-center">
      <p className={cn('text-lg font-bold tabular-nums', valueClass)}>{value}</p>
      <div className="flex items-center justify-center gap-1 text-[10px] text-muted-foreground">
        {label}
        <MetricInfoTooltip info={info} iconSize="xs" />
      </div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-xs border-b border-border/30 pb-2 last:border-0 last:pb-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium text-foreground truncate max-w-[60%] text-right">
        {value}
      </span>
    </div>
  );
}

function colorForRate(value: number, goodThreshold: number, midThreshold: number) {
  if (value >= goodThreshold) return 'text-emerald-500';
  if (value >= midThreshold) return 'text-amber-500';
  return 'text-red-500';
}
```

- [ ] **Step 2: Verify `Separator` exists in ui**

Run: Glob `frontend/src/components/ui/separator.tsx`

Expected: file exists. If not, add `import { Separator } from '@radix-ui/react-separator'` and replace `<Separator ... />` with a simple `<hr className="my-4 border-border" />`.

- [ ] **Step 3: Run the sidebar test**

Run: `cd frontend && npx vitest run src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/__tests__/AutomationStepSidebar.test.tsx`

Expected: all tests pass.

- [ ] **Step 4: Run type check**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep -E "AutomationStepSidebar" | head -10`

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/components/AutomationStepSidebar.tsx
git commit -m "feat(growth): implement AutomationStepSidebar with metrics, benchmarks and AI diagnosis"
```

---

## Phase 5: Frontend — Tab Rewrite

### Task 16: Update MailTabs test for new columns

**Files:**
- Modify: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/__tests__/MailTabs.test.tsx`

- [ ] **Step 1: Read current test file to find automations test**

Run: Read `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/__tests__/MailTabs.test.tsx` looking for automation tests.

- [ ] **Step 2: Update the automations test block**

Find the test(s) for `MailAutomatizacionesTab` and replace with (add if not present):

```tsx
describe('MailAutomatizacionesTab — redesigned', () => {
  const mockData = {
    period: '30d',
    kpis: [
      {
        metricName: 'automation_emails_sent',
        displayName: 'Emails Automatizados',
        currentValue: 18,
        previousValue: null,
        deltaPct: null,
        deltaAbsolute: null,
        unit: 'count',
        higherIsBetter: true,
        benchmark: null,
      },
    ],
    automations: [
      {
        automationId: 'a1',
        name: 'BIENVENIDA',
        automationType: 'welcome',
        status: 'active',
        activeSubscribers: 9, // Now: completed + in_queue
        completed: 4,
        emailsSent: 18,
        openRate: 100,
        clickRate: 50,
        clickToOpenRate: 50,
        completionRate: 44.4,
        unsubscribes: 0,
        steps: [
          {
            stepId: 's1',
            stepNumber: 1,
            type: 'email' as const,
            subject: 'Bienvenida',
            fromName: 'Team',
            emailsSent: 9,
            uniqueOpens: 9,
            openRate: 100,
            uniqueClicks: 4,
            clickRate: 44.4,
            unsubscribes: 0,
            bounces: 0,
            screenshotUrl: null,
            previewUrl: null,
            delayValue: null,
            delayUnit: null,
          },
        ],
      },
    ],
  };

  it('renders new table columns: Ingresados, CTOR, Unsubs, Salud', async () => {
    vi.mocked(useMailAutomations).mockReturnValue({
      data: mockData,
      isLoading: false,
    } as unknown as ReturnType<typeof useMailAutomations>);

    render(<MailAutomatizacionesTab period="30d" />);

    expect(screen.getByText(/Ingresados/i)).toBeInTheDocument();
    expect(screen.getByText(/CTOR/i)).toBeInTheDocument();
    expect(screen.getByText(/Unsubs/i)).toBeInTheDocument();
    expect(screen.getByText(/Salud/i)).toBeInTheDocument();
  });

  it('renders automation row with ingresados = completed + in_queue (activeSubscribers)', async () => {
    vi.mocked(useMailAutomations).mockReturnValue({
      data: mockData,
      isLoading: false,
    } as unknown as ReturnType<typeof useMailAutomations>);

    render(<MailAutomatizacionesTab period="30d" />);

    // 9 ingresados must appear
    expect(screen.getByText('9')).toBeInTheDocument();
  });

  it('opens accordion when clicking on automation row', async () => {
    vi.mocked(useMailAutomations).mockReturnValue({
      data: mockData,
      isLoading: false,
    } as unknown as ReturnType<typeof useMailAutomations>);

    render(<MailAutomatizacionesTab period="30d" />);

    const row = screen.getByText('BIENVENIDA').closest('tr');
    expect(row).not.toBeNull();
    fireEvent.click(row!);

    // Email subject from the pipeline becomes visible
    expect(await screen.findByText('Bienvenida')).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Ensure imports at top of file include `fireEvent`, `vi`, `useMailAutomations`, `MailAutomatizacionesTab`**

Verify the existing import block includes:

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MailAutomatizacionesTab } from '../tabs/MailAutomatizacionesTab';
import { useMailAutomations } from '../../../../../hooks/useMailDashboard';

vi.mock('../../../../../hooks/useMailDashboard');
```

Add missing pieces as needed. Keep existing tests untouched.

- [ ] **Step 4: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/growth-studio/components/metrics-dashboard/sidebar/mail/__tests__/MailTabs.test.tsx -t "redesigned"`

Expected: FAIL — tab not yet updated.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/__tests__/MailTabs.test.tsx
git commit -m "test(growth): add failing tests for redesigned automations tab columns"
```

---

### Task 17: Rewrite MailAutomatizacionesTab

**Files:**
- Modify: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailAutomatizacionesTab.tsx` (full rewrite)

- [ ] **Step 1: Replace the entire file with the new implementation**

Write:

```tsx
'use client';

import { useState, useMemo } from 'react';
import { Loader2, Bot, ChevronRight } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useMailAutomations } from '../../../../../hooks/useMailDashboard';
import { formatMetricValue } from '../../../../../utils/format-metric-value';
import { computeHealthScore } from '../../../../../utils/automation-health';
import { AUTOMATION_METRIC_INFO } from '../../../../../utils/automation-metric-info';
import { ChartSection } from '../../shared/ChartSection';
import { AutomationPipeline } from '../components/AutomationPipeline';
import { AutomationStepSidebar } from '../components/AutomationStepSidebar';
import { MetricInfoTooltip } from '../components/MetricInfoTooltip';
import type { MetaAdsPeriod, MetricKpiData } from '../../../../../types/metrics';
import type {
  AutomationStep,
  EmailAutomation,
  EmailAutomationsData,
} from '../../../../../types/mail-types';

interface MailAutomatizacionesTabProps {
  period: MetaAdsPeriod;
}

const TYPE_LABELS: Record<string, { label: string; className: string }> = {
  welcome: { label: 'Bienvenida', className: 'bg-blue-500/10 text-blue-500' },
  nurture: { label: 'Nutrición', className: 'bg-purple-500/10 text-purple-500' },
  reengagement: {
    label: 'Re-engagement',
    className: 'bg-amber-500/10 text-amber-500',
  },
  post_compra: {
    label: 'Post-compra',
    className: 'bg-emerald-500/10 text-emerald-500',
  },
  workflow: {
    label: 'Workflow',
    className: 'bg-slate-500/10 text-muted-foreground',
  },
};

const FILTER_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'all', label: 'Todas' },
  { value: 'welcome', label: 'Bienvenida' },
  { value: 'nurture', label: 'Nutrición' },
  { value: 'workflow', label: 'Workflow' },
];

export function MailAutomatizacionesTab({ period }: MailAutomatizacionesTabProps) {
  const { data, isLoading } = useMailAutomations(period);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [selectedStep, setSelectedStep] = useState<AutomationStep | null>(null);
  const [selectedAutomation, setSelectedAutomation] = useState<EmailAutomation | null>(null);

  const filteredAutomations = useMemo(() => {
    if (!data) return [];
    if (activeFilter === 'all') return data.automations;
    return data.automations.filter((a) => a.automationType === activeFilter);
  }, [data, activeFilter]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data || data.automations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-500/10">
          <Bot className="h-8 w-8 text-amber-500" />
        </div>
        <div className="text-center">
          <h3 className="text-lg font-semibold">Sin automatizaciones</h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Las automatizaciones se activarán cuando configures secuencias de email en tu proveedor.
          </p>
        </div>
      </div>
    );
  }

  const handleRowToggle = (automationId: string) => {
    setExpandedId(expandedId === automationId ? null : automationId);
  };

  const handleStepClick = (step: AutomationStep, automation: EmailAutomation) => {
    setSelectedStep(step);
    setSelectedAutomation(automation);
  };

  const handleStepSidebarClose = () => {
    setSelectedStep(null);
    setSelectedAutomation(null);
  };

  const previousStepForSelected =
    selectedStep && selectedAutomation
      ? findPreviousEmailStep(selectedAutomation.steps, selectedStep.stepId)
      : null;

  return (
    <>
      <div className="space-y-6 max-w-[1280px] mx-auto">
        {/* KPI row */}
        <ChartSection slug="kpis-automatizaciones">
          <KpiRow data={data} />
        </ChartSection>

        {/* Table with accordion */}
        <ChartSection slug="tabla-automatizaciones">
          <div className="rounded-lg border bg-card overflow-hidden">
            {/* Header bar */}
            <div className="flex items-center justify-between px-5 py-4 border-b">
              <h3 className="text-sm font-semibold">Detalle por Automatización</h3>
              <div className="flex gap-1.5">
                {FILTER_OPTIONS.map((opt) => (
                  <Button
                    key={opt.value}
                    size="sm"
                    variant={activeFilter === opt.value ? 'default' : 'outline'}
                    onClick={() => setActiveFilter(opt.value)}
                    className="h-7 rounded-full px-3 text-[11px]"
                  >
                    {opt.label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="border-b">
                  <tr className="text-muted-foreground">
                    <th className="w-7 py-3 px-3" />
                    <TableHeader label="Automatización" info={null} />
                    <TableHeader
                      label="Ingresados"
                      info={AUTOMATION_METRIC_INFO.ingresados}
                      center
                    />
                    <TableHeader
                      label="Completaron"
                      info={AUTOMATION_METRIC_INFO.completaron}
                      center
                    />
                    <TableHeader
                      label="Open Rate"
                      info={AUTOMATION_METRIC_INFO.openRate}
                      center
                    />
                    <TableHeader
                      label="Click Rate"
                      info={AUTOMATION_METRIC_INFO.clickRate}
                      center
                    />
                    <TableHeader
                      label="CTOR"
                      info={AUTOMATION_METRIC_INFO.ctor}
                      center
                    />
                    <TableHeader
                      label="Unsubs"
                      info={AUTOMATION_METRIC_INFO.unsubs}
                      center
                    />
                    <TableHeader
                      label="Salud"
                      info={AUTOMATION_METRIC_INFO.salud}
                      center
                    />
                  </tr>
                </thead>
                <tbody>
                  {filteredAutomations.map((auto) => {
                    const isExpanded = expandedId === auto.automationId;
                    const healthScore = computeHealthScore(auto);
                    const typeInfo =
                      TYPE_LABELS[auto.automationType] ?? TYPE_LABELS.workflow;
                    const completionPct = auto.completionRate.toFixed(0);

                    return (
                      <>
                        <tr
                          key={auto.automationId}
                          onClick={() => handleRowToggle(auto.automationId)}
                          className={cn(
                            'border-b border-border/40 cursor-pointer transition-colors hover:bg-primary/[0.03]',
                            isExpanded && 'bg-primary/[0.05]',
                          )}
                        >
                          <td className="py-3 px-3">
                            <ChevronRight
                              className={cn(
                                'h-3.5 w-3.5 text-muted-foreground transition-transform',
                                isExpanded && 'rotate-90',
                              )}
                            />
                          </td>
                          <td className="py-3 px-3">
                            <div className="text-xs font-medium max-w-[260px] truncate">
                              {auto.name}
                            </div>
                            <div className="mt-0.5 flex items-center gap-1.5 text-[10px] text-muted-foreground">
                              <span
                                className={cn(
                                  'rounded-full px-2 py-0.5 font-semibold',
                                  typeInfo.className,
                                )}
                              >
                                {typeInfo.label}
                              </span>
                              <span>·</span>
                              <span>
                                {auto.steps.filter((s) => s.type === 'email').length}{' '}
                                emails
                              </span>
                              <span>·</span>
                              <span
                                className={cn(
                                  'inline-flex items-center gap-1',
                                  auto.status === 'active'
                                    ? 'text-emerald-500'
                                    : 'text-muted-foreground',
                                )}
                              >
                                <span
                                  className={cn(
                                    'h-1.5 w-1.5 rounded-full',
                                    auto.status === 'active'
                                      ? 'bg-emerald-500'
                                      : 'bg-muted-foreground',
                                  )}
                                />
                                {auto.status === 'active' ? 'Activa' : 'Pausada'}
                              </span>
                            </div>
                          </td>
                          <td className="py-3 px-3 text-center tabular-nums">
                            {auto.activeSubscribers}
                          </td>
                          <td className="py-3 px-3 text-center tabular-nums">
                            {auto.completed}{' '}
                            <span className="text-[10px] text-muted-foreground">
                              ({completionPct}%)
                            </span>
                          </td>
                          <td
                            className={cn(
                              'py-3 px-3 text-center font-semibold tabular-nums',
                              rateClass(auto.openRate, 50, 30),
                            )}
                          >
                            {auto.openRate.toFixed(1)}%
                          </td>
                          <td
                            className={cn(
                              'py-3 px-3 text-center font-semibold tabular-nums',
                              rateClass(auto.clickRate, 5, 2),
                            )}
                          >
                            {auto.clickRate.toFixed(1)}%
                          </td>
                          <td
                            className={cn(
                              'py-3 px-3 text-center tabular-nums',
                              rateClass(auto.clickToOpenRate, 15, 8),
                            )}
                          >
                            {auto.clickToOpenRate.toFixed(1)}%
                          </td>
                          <td
                            className={cn(
                              'py-3 px-3 text-center tabular-nums',
                              auto.unsubscribes === 0
                                ? 'text-emerald-500'
                                : auto.unsubscribes <= 3
                                  ? 'text-amber-500'
                                  : 'text-red-500',
                            )}
                          >
                            {auto.unsubscribes}
                          </td>
                          <td className="py-3 px-3">
                            <HealthBar score={healthScore} />
                          </td>
                        </tr>

                        {isExpanded && (
                          <tr className="bg-muted/10">
                            <td colSpan={9} className="px-5 py-5">
                              <AutomationPipeline
                                steps={auto.steps}
                                onStepClick={(step) => handleStepClick(step, auto)}
                              />
                            </td>
                          </tr>
                        )}
                      </>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </ChartSection>
      </div>

      {/* Sidebar */}
      <AutomationStepSidebar
        step={selectedStep}
        automationName={selectedAutomation?.name ?? ''}
        totalSteps={
          selectedAutomation?.steps.filter((s) => s.type === 'email').length ?? 0
        }
        previousStep={previousStepForSelected}
        onClose={handleStepSidebarClose}
      />
    </>
  );
}

// ─── Sub-components ─────────────────────────────────────────────────

function TableHeader({
  label,
  info,
  center = false,
}: {
  label: string;
  info: { title: string; description: string; formula?: string; interpret?: { good: string; mid: string; bad: string } } | null;
  center?: boolean;
}) {
  return (
    <th
      className={cn(
        'py-3 px-3 font-medium text-[10px] uppercase tracking-wide whitespace-nowrap',
        center ? 'text-center' : 'text-left',
      )}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {info && <MetricInfoTooltip info={info} side="bottom" />}
      </span>
    </th>
  );
}

function HealthBar({ score }: { score: number }) {
  const color =
    score >= 70
      ? 'bg-emerald-500'
      : score >= 40
        ? 'bg-amber-500'
        : score > 0
          ? 'bg-red-500'
          : 'bg-muted-foreground';

  const textColor =
    score >= 70
      ? 'text-emerald-500'
      : score >= 40
        ? 'text-amber-500'
        : score > 0
          ? 'text-red-500'
          : 'text-muted-foreground';

  return (
    <div className="flex items-center gap-2 justify-center">
      <div className="h-1.5 w-12 overflow-hidden rounded-full bg-muted/30">
        <div
          className={cn('h-full rounded-full transition-all', color)}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className={cn('text-xs font-bold tabular-nums', textColor)}>
        {score || '—'}
      </span>
    </div>
  );
}

function KpiRow({ data }: { data: EmailAutomationsData }) {
  const totalIngresados = data.automations.reduce(
    (sum, a) => sum + a.activeSubscribers,
    0,
  );
  const totalSent = data.automations.reduce((sum, a) => sum + a.emailsSent, 0);
  const avgOpen =
    totalSent > 0
      ? data.automations.reduce((sum, a) => sum + a.openRate * a.emailsSent, 0) /
        totalSent
      : 0;
  const avgClick =
    totalSent > 0
      ? data.automations.reduce((sum, a) => sum + a.clickRate * a.emailsSent, 0) /
        totalSent
      : 0;
  const avgHealth =
    data.automations.length > 0
      ? data.automations.reduce((sum, a) => sum + computeHealthScore(a), 0) /
        data.automations.length
      : 0;

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <KpiCard
        label="Ingresados Totales"
        value={String(totalIngresados)}
        info={AUTOMATION_METRIC_INFO.ingresados}
      />
      <KpiCard
        label="Open Rate Promedio"
        value={`${avgOpen.toFixed(1)}%`}
        info={AUTOMATION_METRIC_INFO.openRate}
        valueColor={rateClass(avgOpen, 50, 30)}
      />
      <KpiCard
        label="Click Rate Promedio"
        value={`${avgClick.toFixed(1)}%`}
        info={AUTOMATION_METRIC_INFO.clickRate}
        valueColor={rateClass(avgClick, 5, 2)}
      />
      <KpiCard
        label="Salud General"
        value={`${Math.round(avgHealth)}`}
        suffix="/100"
        info={AUTOMATION_METRIC_INFO.salud}
        valueColor={
          avgHealth >= 70
            ? 'text-emerald-500'
            : avgHealth >= 40
              ? 'text-amber-500'
              : 'text-red-500'
        }
      />
    </div>
  );
}

function KpiCard({
  label,
  value,
  suffix,
  info,
  valueColor,
}: {
  label: string;
  value: string;
  suffix?: string;
  info: { title: string; description: string; formula?: string; interpret?: { good: string; mid: string; bad: string } };
  valueColor?: string;
}) {
  return (
    <div className="rounded-lg border bg-card px-4 py-3">
      <div className="flex items-center gap-1 text-[10px] uppercase tracking-wide text-muted-foreground">
        {label}
        <MetricInfoTooltip info={info} iconSize="xs" />
      </div>
      <p className={cn('mt-1 text-xl font-bold tabular-nums', valueColor)}>
        {value}
        {suffix && (
          <span className="text-sm font-normal text-muted-foreground">
            {suffix}
          </span>
        )}
      </p>
    </div>
  );
}

// ─── Helpers ────────────────────────────────────────────────────────

function rateClass(value: number, goodThreshold: number, midThreshold: number) {
  if (value >= goodThreshold) return 'text-emerald-500';
  if (value >= midThreshold) return 'text-amber-500';
  return 'text-red-500';
}

function findPreviousEmailStep(
  steps: AutomationStep[],
  currentStepId: string,
): AutomationStep | null {
  const idx = steps.findIndex((s) => s.stepId === currentStepId);
  if (idx <= 0) return null;
  for (let i = idx - 1; i >= 0; i--) {
    if (steps[i].type === 'email') return steps[i];
  }
  return null;
}
```

- [ ] **Step 2: Run the tab tests**

Run: `cd frontend && npx vitest run src/features/growth-studio/components/metrics-dashboard/sidebar/mail/__tests__/MailTabs.test.tsx`

Expected: all tests pass.

- [ ] **Step 3: Run the full mail test suite**

Run: `cd frontend && npx vitest run src/features/growth-studio/components/metrics-dashboard/sidebar/mail/`

Expected: all tests pass.

- [ ] **Step 4: Run type check**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`

Expected: no errors in any modified file.

- [ ] **Step 5: Run lint**

Run: `cd frontend && npx eslint src/features/growth-studio/components/metrics-dashboard/sidebar/mail/ src/features/growth-studio/utils/ src/features/growth-studio/api/mail-api.ts src/features/growth-studio/types/mail-types.ts`

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailAutomatizacionesTab.tsx
git commit -m "feat(growth): rewrite Automatizaciones tab with health scores, filters and pipeline expansion"
```

---

## Phase 6: Verification

### Task 18: Full CI verification

**Files:** none (validation only)

- [ ] **Step 1: Backend lint**

Run: `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`

Expected: no errors.

- [ ] **Step 2: Backend tests (analytics only)**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/ -x -q --tb=short`

Expected: all tests pass.

- [ ] **Step 3: Architecture tests**

Run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`

Expected: all tests pass.

- [ ] **Step 4: Frontend type check**

Run: `cd frontend && npx tsc --noEmit`

Expected: no errors.

- [ ] **Step 5: Frontend lint**

Run: `cd frontend && npx eslint src/features/growth-studio/`

Expected: no errors.

- [ ] **Step 6: Frontend full test suite**

Run: `cd frontend && npx vitest run src/features/growth-studio/`

Expected: all tests pass.

- [ ] **Step 7: Visual smoke test in dev**

Manual: `docker compose up -d` → open http://localhost:3000/<tenantId>/growth-studio/nutricion-oportunidad/email-nurture?tab=automatizaciones

Verify:
- Table shows Ingresados (not 0), CTOR, Unsubs, Salud
- Click row → accordion expands with email pipeline
- Click email card → sidebar opens with metrics, benchmarks, diagnosis
- Each `ⓘ` shows tooltip with description + formula + interpretation

- [ ] **Step 8: Commit any remaining fixes**

If any verification step revealed issues, fix them and commit separately (`fix(...): ...`). Do not amend previous commits.

---

## Self-Review

**1. Spec coverage:**
- L1 Table redesign → Task 17
- L2 Accordion pipeline → Task 13 (AutomationPipeline) + Task 17 (wired into tab)
- L3 Sidebar detail → Task 15 (AutomationStepSidebar) + Task 17 (wired into tab)
- Bug: subscribers=0 → Task 5
- Bug: completion shows CTOR → Task 5
- Bug: status hardcoded → Task 3 + Task 5
- New metrics (CTOR, unsubs, steps) → Tasks 1, 3, 5, 6, 7
- Info tooltips on every metric → Tasks 8 (dictionary), 11 (component), applied in 13, 15, 17
- Health score → Tasks 9, 10, 17
- Drop-off visualization → Tasks 9, 10, 13
- AI diagnosis → Tasks 9, 10, 13, 15
- Filter pills → Task 17
- Preview link → Task 15
- Benchmarks comparison → Task 15
- Test strategy (backend service + provider + frontend components + tab) → Tasks 2, 4, 9, 12, 14, 16
- Out-of-scope items (revenue attribution, activity endpoint, A/B, historical trends) → correctly excluded

**2. Placeholder scan:** no "TBD", "TODO", "similar to", "add appropriate", or vague handoffs. All code steps contain full implementation.

**3. Type consistency:**
- `AutomationStep` fields match between mail-types.ts, api mapper, DTO, utils, components
- `EmailAutomation.activeSubscribers` semantically = ingresados (documented)
- `clickToOpenRate` used consistently
- `diagnoseStep(step, prev?)` signature matches between util and consumers
- `findBestStep` / `findAttentionStep` used the same way in Pipeline component
- `computeHealthScore(auto)` signature matches in tab KPIs + table rows
- `MetricInfoTooltip` props (`info`, `iconSize`, `side`) consistent across all usages

All consistent. Plan ready for execution.
