# Phase 3 — Interview Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Interview Engine with voice input (Whisper STT), document attachment, buyer persona interviews, and offer interviews with web research.

**Architecture:** Registry-driven extension of the existing Interview Engine. Each new domain (buyer_persona, offer) registers 4 pieces: InterviewConfig, Persister, ExpertiseTemplate, PreviewComponent. Voice and documents are cross-cutting capabilities added to the copilot module. Split view generalized via PreviewRegistry.

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy 2.0 / OpenAI Whisper API / Tavily API / Next.js 15 / React 18 / TypeScript / Zustand / Shadcn UI

**Spec:** `docs/superpowers/specs/2026-04-12-phase3-interview-engine-design.md`

---

## Execution Phases

```
Phase A (parallel, no deps):     S1-Voice | S2-Documents | S3-Engine-Generalization
Phase B (parallel, after S3):    S4-BuyerPersona | S5-Offer | S6-Frontend-Generalization  
Phase C (parallel, after S4+S6 / S5+S6): S7-BP-Preview | S8-OI-Preview
Phase D (sequential, after all): S9-Entry-Points
```

**IMPORTANT:** Streams S1, S2, S3 can be dispatched to 3 agents simultaneously. Streams within the same phase MUST NOT touch the same files. Cross-stream files are noted in each task.

---

## Stream S1: Voice (STT with Whisper)

**Independent — no dependencies. Can run in parallel with S2 and S3.**

### Task S1.1: Voice Domain Ports

**Files:**
- Create: `backend/src/modules/copilot/domain/voice.py`
- Test: `backend/tests/modules/copilot/test_voice_domain.py`

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/copilot/test_voice_domain.py
from src.modules.copilot.domain.voice import TranscriptionResult


def test_transcription_result_is_immutable():
    result = TranscriptionResult(text="hola mundo", language="es", duration_seconds=2.5)
    assert result.text == "hola mundo"
    assert result.language == "es"
    assert result.duration_seconds == 2.5


def test_transcription_result_frozen():
    result = TranscriptionResult(text="test", language="en", duration_seconds=1.0)
    try:
        result.text = "changed"
        assert False, "Should raise FrozenInstanceError"
    except AttributeError:
        pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_voice_domain.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.modules.copilot.domain.voice'`

- [ ] **Step 3: Implement domain ports**

```python
# backend/src/modules/copilot/domain/voice.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TranscriptionResult:
    """Result of a speech-to-text transcription."""

    text: str
    language: str
    duration_seconds: float


class TranscriptionPort(Protocol):
    """Port for speech-to-text. Implemented by Whisper today, extensible."""

    async def transcribe(self, audio: bytes, mime_type: str) -> TranscriptionResult: ...


class SynthesisPort(Protocol):
    """Port for text-to-speech. Not implemented in Phase 3. Prepared for future TTS."""

    async def synthesize(self, text: str, voice: str) -> bytes: ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_voice_domain.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/copilot/domain/voice.py backend/tests/modules/copilot/test_voice_domain.py
git commit -m "feat(copilot): add voice domain ports (TranscriptionPort, SynthesisPort)"
```

---

### Task S1.2: Whisper Transcriber Infrastructure

**Files:**
- Create: `backend/src/modules/copilot/infrastructure/voice/__init__.py`
- Create: `backend/src/modules/copilot/infrastructure/voice/whisper_transcriber.py`
- Test: `backend/tests/modules/copilot/test_whisper_transcriber.py`

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/copilot/test_whisper_transcriber.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.modules.copilot.infrastructure.voice.whisper_transcriber import WhisperTranscriber


@pytest.mark.asyncio
async def test_transcribe_returns_result():
    mock_response = MagicMock()
    mock_response.text = "hola, soy un test de voz"
    mock_response.language = "es"
    mock_response.duration = 3.2

    with patch(
        "src.modules.copilot.infrastructure.voice.whisper_transcriber.openai_client"
    ) as mock_client:
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        transcriber = WhisperTranscriber()
        result = await transcriber.transcribe(b"fake-audio-bytes", "audio/webm")

        assert result.text == "hola, soy un test de voz"
        assert result.language == "es"
        assert result.duration_seconds == 3.2


@pytest.mark.asyncio
async def test_transcribe_handles_empty_audio():
    with patch(
        "src.modules.copilot.infrastructure.voice.whisper_transcriber.openai_client"
    ) as mock_client:
        mock_client.audio.transcriptions.create = AsyncMock(
            side_effect=Exception("Invalid audio")
        )

        transcriber = WhisperTranscriber()
        with pytest.raises(Exception, match="Invalid audio"):
            await transcriber.transcribe(b"", "audio/webm")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_whisper_transcriber.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement WhisperTranscriber**

```python
# backend/src/modules/copilot/infrastructure/voice/__init__.py
```

```python
# backend/src/modules/copilot/infrastructure/voice/whisper_transcriber.py
from __future__ import annotations

import io
import structlog
from openai import AsyncOpenAI

from src.core.config import settings
from src.modules.copilot.domain.voice import TranscriptionPort, TranscriptionResult

logger = structlog.get_logger()

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

MIME_TO_EXT = {
    "audio/webm": "webm",
    "audio/mp4": "mp4",
    "audio/wav": "wav",
    "audio/mpeg": "mp3",
    "audio/m4a": "m4a",
}


class WhisperTranscriber(TranscriptionPort):
    """Speech-to-text via OpenAI Whisper API."""

    async def transcribe(self, audio: bytes, mime_type: str) -> TranscriptionResult:
        ext = MIME_TO_EXT.get(mime_type, "webm")
        audio_file = io.BytesIO(audio)
        audio_file.name = f"recording.{ext}"

        logger.info("whisper_transcribe_start", size_bytes=len(audio), mime_type=mime_type)

        response = await openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="es",
            response_format="verbose_json",
        )

        result = TranscriptionResult(
            text=response.text,
            language=response.language or "es",
            duration_seconds=response.duration or 0.0,
        )

        logger.info(
            "whisper_transcribe_done",
            text_length=len(result.text),
            language=result.language,
            duration=result.duration_seconds,
        )
        return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_whisper_transcriber.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/copilot/infrastructure/voice/
git add backend/tests/modules/copilot/test_whisper_transcriber.py
git commit -m "feat(copilot): add WhisperTranscriber infrastructure"
```

---

### Task S1.3: Voice API Endpoint

**Files:**
- Create: `backend/src/modules/copilot/api/voice.py`
- Modify: `backend/src/modules/copilot/api/__init__.py` (add voice router)
- Create: `backend/src/modules/copilot/api/voice_dto.py`
- Test: `backend/tests/modules/copilot/test_voice_api.py`

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/copilot/test_voice_api.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.copilot.api.voice import router
from src.core.dependencies import get_tenant_context, get_current_user
from src.core.database import get_db


def _build_client():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot/voice")
    tenant_id = uuid4()
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id
    return TestClient(app), tenant_id


@patch("src.modules.copilot.api.voice.WhisperTranscriber")
def test_transcribe_audio_success(mock_transcriber_cls):
    from src.modules.copilot.domain.voice import TranscriptionResult

    mock_instance = MagicMock()
    mock_instance.transcribe = AsyncMock(
        return_value=TranscriptionResult(
            text="hola mundo", language="es", duration_seconds=2.0
        )
    )
    mock_transcriber_cls.return_value = mock_instance

    client, _ = _build_client()
    response = client.post(
        "/api/v1/copilot/voice/transcribe",
        files={"file": ("recording.webm", b"fake-audio", "audio/webm")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "hola mundo"
    assert data["language"] == "es"
    assert data["duration_seconds"] == 2.0


def test_transcribe_audio_no_file():
    client, _ = _build_client()
    response = client.post("/api/v1/copilot/voice/transcribe")
    assert response.status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_voice_api.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create DTOs**

```python
# backend/src/modules/copilot/api/voice_dto.py
from pydantic import BaseModel


class TranscriptionResponse(BaseModel):
    text: str
    language: str
    duration_seconds: float
```

- [ ] **Step 4: Create voice router**

```python
# backend/src/modules/copilot/api/voice.py
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, UploadFile, Depends
import structlog

from src.core.dependencies import get_tenant_context
from src.modules.copilot.api.voice_dto import TranscriptionResponse
from src.modules.copilot.infrastructure.voice.whisper_transcriber import (
    WhisperTranscriber,
)

logger = structlog.get_logger()
router = APIRouter(tags=["Voice"])


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    tenant_id: UUID = Depends(get_tenant_context),
):
    """Receive audio blob, return transcribed text."""
    audio_bytes = await file.read()
    mime_type = file.content_type or "audio/webm"

    transcriber = WhisperTranscriber()
    result = await transcriber.transcribe(audio_bytes, mime_type)

    return TranscriptionResponse(
        text=result.text,
        language=result.language,
        duration_seconds=result.duration_seconds,
    )
```

- [ ] **Step 5: Register voice router in copilot API**

Read `backend/src/modules/copilot/api/__init__.py` and add:
```python
from src.modules.copilot.api.voice import router as voice_router
# In the router setup:
router.include_router(voice_router, prefix="/voice")
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_voice_api.py -v`
Expected: PASS (2 tests)

- [ ] **Step 7: Lint check**

Run: `cd backend && .venv/bin/ruff check src/modules/copilot/api/voice.py src/modules/copilot/api/voice_dto.py src/modules/copilot/infrastructure/voice/ --no-cache`
Expected: No errors

- [ ] **Step 8: Commit**

```bash
git add backend/src/modules/copilot/api/voice.py backend/src/modules/copilot/api/voice_dto.py
git add backend/src/modules/copilot/api/__init__.py
git add backend/tests/modules/copilot/test_voice_api.py
git commit -m "feat(copilot): add POST /voice/transcribe endpoint"
```

---

### Task S1.4: Frontend — useVoiceRecorder Hook

**Files:**
- Create: `frontend/src/features/copilot/hooks/useVoiceRecorder.ts`
- Create: `frontend/src/features/copilot/api/voice-api.ts`
- Test: `frontend/src/features/copilot/hooks/__tests__/useVoiceRecorder.test.ts`

- [ ] **Step 1: Write the test**

```typescript
// frontend/src/features/copilot/hooks/__tests__/useVoiceRecorder.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useVoiceRecorder } from "../useVoiceRecorder";

// Mock MediaRecorder
const mockMediaRecorder = {
  start: vi.fn(),
  stop: vi.fn(),
  ondataavailable: null as ((e: { data: Blob }) => void) | null,
  onstop: null as (() => void) | null,
  state: "inactive",
};

vi.stubGlobal("MediaRecorder", vi.fn(() => mockMediaRecorder));
vi.stubGlobal("navigator", {
  mediaDevices: {
    getUserMedia: vi.fn().mockResolvedValue(new MediaStream()),
  },
});

vi.mock("../../api/voice-api", () => ({
  transcribeAudio: vi.fn().mockResolvedValue({
    text: "texto transcrito",
    language: "es",
    duration_seconds: 2.5,
  }),
}));

describe("useVoiceRecorder", () => {
  it("starts in idle state", () => {
    const { result } = renderHook(() => useVoiceRecorder());
    expect(result.current.isRecording).toBe(false);
    expect(result.current.isTranscribing).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("sets isRecording to true when startRecording is called", async () => {
    const { result } = renderHook(() => useVoiceRecorder());
    await act(async () => {
      await result.current.startRecording();
    });
    expect(result.current.isRecording).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/copilot/hooks/__tests__/useVoiceRecorder.test.ts`
Expected: FAIL — module not found

- [ ] **Step 3: Create voice API client**

```typescript
// frontend/src/features/copilot/api/voice-api.ts
import { fetchClient } from "@/lib/fetch-client";

interface TranscriptionResponse {
  text: string;
  language: string;
  duration_seconds: number;
}

export async function transcribeAudio(
  audioBlob: Blob,
  token: string,
): Promise<TranscriptionResponse> {
  const formData = new FormData();
  formData.append("file", audioBlob, "recording.webm");

  const response = await fetchClient("/api/v1/copilot/voice/transcribe", {
    method: "POST",
    body: formData,
    token,
  });

  if (!response.ok) {
    throw new Error(`Transcription failed: ${response.status}`);
  }

  return response.json();
}
```

- [ ] **Step 4: Implement useVoiceRecorder hook**

```typescript
// frontend/src/features/copilot/hooks/useVoiceRecorder.ts
"use client";

import { useState, useRef, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { transcribeAudio } from "../api/voice-api";

interface UseVoiceRecorderReturn {
  isRecording: boolean;
  isTranscribing: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<string>;
  cancelRecording: () => void;
  error: string | null;
  duration: number;
}

export function useVoiceRecorder(): UseVoiceRecorderReturn {
  const { getToken } = useAuth();
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duration, setDuration] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const resolveStopRef = useRef<((transcript: string) => void) | null>(null);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });

      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        if (timerRef.current) clearInterval(timerRef.current);

        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size === 0) {
          resolveStopRef.current?.("");
          return;
        }

        setIsTranscribing(true);
        try {
          const token = (await getToken()) ?? "";
          const result = await transcribeAudio(blob, token);
          resolveStopRef.current?.(result.text);
        } catch (err) {
          setError(err instanceof Error ? err.message : "Error al transcribir");
          resolveStopRef.current?.("");
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
      setDuration(0);

      timerRef.current = setInterval(() => {
        setDuration((d) => d + 1);
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo acceder al micrófono");
    }
  }, [getToken]);

  const stopRecording = useCallback((): Promise<string> => {
    return new Promise((resolve) => {
      resolveStopRef.current = resolve;
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    });
  }, []);

  const cancelRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
    chunksRef.current = [];
    resolveStopRef.current?.("");
  }, []);

  return {
    isRecording,
    isTranscribing,
    startRecording,
    stopRecording,
    cancelRecording,
    error,
    duration,
  };
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/copilot/hooks/__tests__/useVoiceRecorder.test.ts`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/copilot/hooks/useVoiceRecorder.ts
git add frontend/src/features/copilot/api/voice-api.ts
git add frontend/src/features/copilot/hooks/__tests__/useVoiceRecorder.test.ts
git commit -m "feat(copilot): add useVoiceRecorder hook + voice API client"
```

---

### Task S1.5: Frontend — InterviewInput Voice Integration

**Files:**
- Modify: `frontend/src/features/copilot/components/interview/interview-input.tsx`
- Test: `frontend/src/features/copilot/components/interview/__tests__/interview-input.test.tsx`

- [ ] **Step 1: Write the test**

```typescript
// frontend/src/features/copilot/components/interview/__tests__/interview-input.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { InterviewInput } from "../interview-input";

vi.mock("../../../hooks/useVoiceRecorder", () => ({
  useVoiceRecorder: () => ({
    isRecording: false,
    isTranscribing: false,
    startRecording: vi.fn(),
    stopRecording: vi.fn().mockResolvedValue("transcribed text"),
    cancelRecording: vi.fn(),
    error: null,
    duration: 0,
  }),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("token") }),
}));

describe("InterviewInput", () => {
  it("renders mic button enabled", () => {
    render(<InterviewInput onSend={vi.fn()} />);
    const micButton = screen.getByRole("button", { name: /micrófono/i });
    expect(micButton).not.toBeDisabled();
  });

  it("renders text input", () => {
    render(<InterviewInput onSend={vi.fn()} />);
    expect(screen.getByPlaceholderText(/escribe/i)).toBeInTheDocument();
  });

  it("calls onSend when submitting text", async () => {
    const onSend = vi.fn();
    render(<InterviewInput onSend={onSend} />);
    const input = screen.getByPlaceholderText(/escribe/i);
    await userEvent.type(input, "test message{Enter}");
    expect(onSend).toHaveBeenCalledWith("test message");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/copilot/components/interview/__tests__/interview-input.test.tsx`
Expected: FAIL (mic button disabled or test structure mismatch)

- [ ] **Step 3: Modify InterviewInput**

Read the current `interview-input.tsx`, then modify it to:
1. Import and use `useVoiceRecorder`
2. Replace the disabled mic button with a toggle that calls `startRecording`/`stopRecording`
3. Add recording state UI (waveform placeholder, timer, stop button)
4. Add `source: "voice"` metadata when sending transcribed text
5. Add `aria-label="Micrófono"` to the mic button

Key changes to the existing component:
- Remove `disabled` from mic button
- Add `onClick` handler: if idle → `startRecording()`, if recording → `stopRecording()` then `onSend(transcript)`
- Conditional rendering: recording state shows duration timer + red pulse + cancel button
- Transcribing state shows spinner "Transcribiendo..."

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/copilot/components/interview/__tests__/interview-input.test.tsx`
Expected: PASS

- [ ] **Step 5: Type check**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: No errors related to interview-input

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/copilot/components/interview/interview-input.tsx
git add frontend/src/features/copilot/components/interview/__tests__/interview-input.test.tsx
git commit -m "feat(copilot): enable voice toggle in InterviewInput"
```

---

## Stream S2: Document Processing

**Independent — no dependencies. Can run in parallel with S1 and S3.**

### Task S2.1: InterviewConfig — Add Document Fields

**Files:**
- Modify: `backend/src/modules/copilot/domain/interview_config.py`
- Modify: `backend/src/modules/copilot/domain/interview_configs/brand_config.py`
- Test: `backend/tests/modules/copilot/test_interview_config.py`

**⚠️ SHARED FILE WARNING:** `interview_config.py` is also modified by S3 (Task S3.1). If running in parallel, S2 adds `document_extraction_template` and `supported_file_types`; S3 adds `initial_research_enabled` and `context_loader`. Merge carefully.

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/copilot/test_interview_config.py
from src.modules.copilot.domain.interview_config import InterviewConfig, InterviewBlock


def test_interview_config_document_fields_defaults():
    config = InterviewConfig(
        domain="test",
        objetivo="test",
        bloques=[InterviewBlock(id="b1", label="B1", campos_objetivo=["f1"], prompt_context="ctx")],
        output_schema_path="test.path",
        datos_previos_fields=[],
        tono="neutral",
        expertise_template="test",
    )
    assert config.document_extraction_template is None
    assert config.supported_file_types == (".pdf", ".docx", ".txt", ".md", ".pptx")


def test_interview_config_with_document_template():
    config = InterviewConfig(
        domain="test",
        objetivo="test",
        bloques=[InterviewBlock(id="b1", label="B1", campos_objetivo=["f1"], prompt_context="ctx")],
        output_schema_path="test.path",
        datos_previos_fields=[],
        tono="neutral",
        expertise_template="test",
        document_extraction_template="brand_doc_extraction",
        supported_file_types=(".pdf", ".docx"),
    )
    assert config.document_extraction_template == "brand_doc_extraction"
    assert config.supported_file_types == (".pdf", ".docx")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_config.py -v`
Expected: FAIL — `TypeError: unexpected keyword argument 'document_extraction_template'`

- [ ] **Step 3: Add fields to InterviewConfig**

Read `backend/src/modules/copilot/domain/interview_config.py` and add these fields to the `InterviewConfig` dataclass:

```python
    document_extraction_template: str | None = None
    supported_file_types: tuple[str, ...] = (".pdf", ".docx", ".txt", ".md", ".pptx")
```

- [ ] **Step 4: Add document_extraction_template to BrandInterviewConfig**

Read `backend/src/modules/copilot/domain/interview_configs/brand_config.py` and add:

```python
    document_extraction_template="brand_doc_extraction",
```
to the `BRAND_INTERVIEW_CONFIG = InterviewConfig(...)` call.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_config.py -v`
Expected: PASS

- [ ] **Step 6: Run existing interview tests to verify no regression**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -v --tb=short`
Expected: All existing tests PASS

- [ ] **Step 7: Commit**

```bash
git add backend/src/modules/copilot/domain/interview_config.py
git add backend/src/modules/copilot/domain/interview_configs/brand_config.py
git add backend/tests/modules/copilot/test_interview_config.py
git commit -m "feat(copilot): add document extraction fields to InterviewConfig"
```

---

### Task S2.2: DocumentProcessor Service

**Files:**
- Create: `backend/src/modules/copilot/application/services/document_processor.py`
- Test: `backend/tests/modules/copilot/test_document_processor.py`

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/copilot/test_document_processor.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.modules.copilot.application.services.document_processor import (
    DocumentProcessor,
    DocumentProcessingResult,
)


@pytest.mark.asyncio
async def test_process_single_document():
    mock_file = MagicMock()
    mock_file.filename = "brief.pdf"
    mock_file.read = AsyncMock(return_value=b"fake pdf content")
    mock_file.content_type = "application/pdf"

    with patch(
        "src.modules.copilot.application.services.document_processor.FileParsingService"
    ) as mock_parser, patch(
        "src.modules.copilot.application.services.document_processor.AIActionService"
    ) as mock_ai:
        mock_parser.parse_file = AsyncMock(return_value="Somos una marca de coaching para emprendedoras")
        mock_ai_instance = MagicMock()
        mock_ai_instance.extract_structured = AsyncMock(
            return_value={"identity.brand_name": "CoachPro", "positioning.uvp": "Transforma tu negocio"}
        )
        mock_ai.return_value = mock_ai_instance

        processor = DocumentProcessor(ai_service=mock_ai_instance)
        result = await processor.process_for_interview(
            files=[mock_file],
            extraction_template="brand_doc_extraction",
            existing_mapa={"identity.brand_name": "OldName"},
            tenant_id=uuid4(),
        )

        assert isinstance(result, DocumentProcessingResult)
        assert result.fields_extracted >= 1
        assert "brief.pdf" in result.source_documents


def test_document_processing_result_structure():
    result = DocumentProcessingResult(
        delta={"field1": "value1"},
        summary="Extracted 1 field from 1 document",
        source_documents=["test.pdf"],
        fields_extracted=1,
        fields_skipped=0,
    )
    assert result.delta == {"field1": "value1"}
    assert result.fields_extracted == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_document_processor.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement DocumentProcessor**

```python
# backend/src/modules/copilot/application/services/document_processor.py
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import structlog
from fastapi import UploadFile

from src.shared.infrastructure.files.file_parsing_service import FileParsingService

logger = structlog.get_logger()


@dataclass
class DocumentProcessingResult:
    delta: dict
    summary: str
    source_documents: list[str]
    fields_extracted: int
    fields_skipped: int


class DocumentProcessor:
    """Domain-agnostic document processing for interview context."""

    def __init__(self, ai_service):
        self.ai_service = ai_service

    async def process_for_interview(
        self,
        files: list[UploadFile],
        extraction_template: str,
        existing_mapa: dict,
        tenant_id: UUID,
    ) -> DocumentProcessingResult:
        """Parse files, extract structured data via LLM, merge into mapa_global."""
        combined_text = ""
        source_docs: list[str] = []

        for file in files:
            parsed = await FileParsingService.parse_file(file)
            if parsed:
                source_docs.append(file.filename or "unknown")
                combined_text += f"\n--- {file.filename} ---\n{parsed}\n"

        if not combined_text.strip():
            return DocumentProcessingResult(
                delta={},
                summary="No se pudo extraer texto de los documentos proporcionados.",
                source_documents=source_docs,
                fields_extracted=0,
                fields_skipped=0,
            )

        logger.info(
            "document_extraction_start",
            template=extraction_template,
            doc_count=len(source_docs),
            text_length=len(combined_text),
        )

        delta = await self.ai_service.extract_structured(
            template=extraction_template,
            text=combined_text,
            existing_data=existing_mapa,
        )

        fields_skipped = sum(1 for k, v in delta.items() if k in existing_mapa and existing_mapa[k])
        fields_extracted = len(delta) - fields_skipped

        # Don't overwrite existing non-empty fields
        filtered_delta = {
            k: v for k, v in delta.items()
            if k not in existing_mapa or not existing_mapa[k]
        }

        summary_parts = [f"Extraídos {fields_extracted} campos de {len(source_docs)} documento(s)."]
        if fields_skipped:
            summary_parts.append(f"{fields_skipped} campos ya tenían valor y no se sobrescribieron.")

        return DocumentProcessingResult(
            delta=filtered_delta,
            summary=" ".join(summary_parts),
            source_documents=source_docs,
            fields_extracted=fields_extracted,
            fields_skipped=fields_skipped,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_document_processor.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/copilot/application/services/document_processor.py
git add backend/tests/modules/copilot/test_document_processor.py
git commit -m "feat(copilot): add DocumentProcessor service for interview documents"
```

---

### Task S2.3: Document Upload API Endpoint

**Files:**
- Modify: `backend/src/modules/copilot/api/interview.py` (add endpoint)
- Create: `backend/src/modules/copilot/api/document_dto.py`
- Test: `backend/tests/modules/copilot/test_document_api.py`

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/copilot/test_document_api.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.copilot.api.interview import router
from src.core.dependencies import get_tenant_context, get_current_user
from src.core.database import get_db


def _build_client():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot/interview")
    tenant_id = uuid4()
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id
    )
    return TestClient(app), tenant_id


@patch("src.modules.copilot.api.interview.DocumentProcessor")
@patch("src.modules.copilot.api.interview.InterviewService")
def test_process_documents_success(mock_service_cls, mock_processor_cls):
    from src.modules.copilot.application.services.document_processor import DocumentProcessingResult

    session_id = uuid4()
    mock_service = MagicMock()
    mock_service.get_session.return_value = MagicMock(
        id=session_id, domain="brand", mapa_global={}, config_snapshot={"document_extraction_template": "brand_doc"}
    )
    mock_service.update_mapa_global = MagicMock()
    mock_service_cls.return_value = mock_service

    mock_processor = MagicMock()
    mock_processor.process_for_interview = AsyncMock(
        return_value=DocumentProcessingResult(
            delta={"identity.brand_name": "TestBrand"},
            summary="Extracted 1 field",
            source_documents=["test.pdf"],
            fields_extracted=1,
            fields_skipped=0,
        )
    )
    mock_processor_cls.return_value = mock_processor

    client, _ = _build_client()
    response = client.post(
        f"/api/v1/copilot/interview/{session_id}/documents",
        files=[("files", ("test.pdf", b"pdf content", "application/pdf"))],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["fields_extracted"] == 1
    assert "test.pdf" in data["source_documents"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_document_api.py -v`
Expected: FAIL

- [ ] **Step 3: Create document DTOs**

```python
# backend/src/modules/copilot/api/document_dto.py
from pydantic import BaseModel


class DocumentProcessingResponse(BaseModel):
    delta: dict
    summary: str
    source_documents: list[str]
    fields_extracted: int
    fields_skipped: int
```

- [ ] **Step 4: Add endpoint to interview router**

Read `backend/src/modules/copilot/api/interview.py` and add:

```python
from fastapi import File, UploadFile
from src.modules.copilot.api.document_dto import DocumentProcessingResponse
from src.modules.copilot.application.services.document_processor import DocumentProcessor

@router.post("/{session_id}/documents", response_model=DocumentProcessingResponse)
async def process_interview_documents(
    session_id: UUID,
    files: list[UploadFile] = File(...),
    tenant_id: UUID = Depends(get_tenant_context),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Process documents and update interview session's mapa_global. Blocking."""
    service = InterviewService(db)
    session = service.get_session(session_id=session_id, tenant_id=tenant_id)

    extraction_template = session.config_snapshot.get("document_extraction_template")
    if not extraction_template:
        raise HTTPException(400, "This interview domain does not support document processing")

    processor = DocumentProcessor(ai_service=AIActionService())
    result = await processor.process_for_interview(
        files=files,
        extraction_template=extraction_template,
        existing_mapa=session.mapa_global,
        tenant_id=tenant_id,
    )

    if result.delta:
        service.update_mapa_global(session_id=session_id, delta=result.delta)

    return DocumentProcessingResponse(
        delta=result.delta,
        summary=result.summary,
        source_documents=result.source_documents,
        fields_extracted=result.fields_extracted,
        fields_skipped=result.fields_skipped,
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_document_api.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/copilot/api/interview.py
git add backend/src/modules/copilot/api/document_dto.py
git add backend/tests/modules/copilot/test_document_api.py
git commit -m "feat(copilot): add POST /interview/{session_id}/documents endpoint"
```

---

### Task S2.4: Frontend — AttachmentButton + DocumentChip Components

**Files:**
- Create: `frontend/src/features/copilot/components/shared/attachment-button.tsx`
- Create: `frontend/src/features/copilot/components/shared/document-chip.tsx`
- Create: `frontend/src/features/copilot/api/document-api.ts`
- Test: `frontend/src/features/copilot/components/shared/__tests__/attachment-button.test.tsx`
- Test: `frontend/src/features/copilot/components/shared/__tests__/document-chip.test.tsx`

- [ ] **Step 1: Write the tests**

```typescript
// frontend/src/features/copilot/components/shared/__tests__/attachment-button.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AttachmentButton } from "../attachment-button";

describe("AttachmentButton", () => {
  it("renders a button with paperclip icon", () => {
    render(<AttachmentButton onFilesSelected={vi.fn()} />);
    expect(screen.getByRole("button", { name: /adjuntar/i })).toBeInTheDocument();
  });

  it("is disabled when disabled prop is true", () => {
    render(<AttachmentButton onFilesSelected={vi.fn()} disabled />);
    expect(screen.getByRole("button", { name: /adjuntar/i })).toBeDisabled();
  });
});
```

```typescript
// frontend/src/features/copilot/components/shared/__tests__/document-chip.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { DocumentChip } from "../document-chip";

describe("DocumentChip", () => {
  const mockFile = new File(["content"], "test.pdf", { type: "application/pdf" });

  it("shows file name", () => {
    render(<DocumentChip file={mockFile} status="pending" />);
    expect(screen.getByText("test.pdf")).toBeInTheDocument();
  });

  it("shows processing spinner when status is processing", () => {
    render(<DocumentChip file={mockFile} status="processing" />);
    expect(screen.getByText(/analizando/i)).toBeInTheDocument();
  });

  it("shows remove button when onRemove provided", () => {
    render(<DocumentChip file={mockFile} status="pending" onRemove={vi.fn()} />);
    expect(screen.getByRole("button", { name: /eliminar/i })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/features/copilot/components/shared/__tests__/`
Expected: FAIL — modules not found

- [ ] **Step 3: Create document API client**

```typescript
// frontend/src/features/copilot/api/document-api.ts
import { fetchClient } from "@/lib/fetch-client";

interface DocumentProcessingResponse {
  delta: Record<string, unknown>;
  summary: string;
  source_documents: string[];
  fields_extracted: number;
  fields_skipped: number;
}

export async function processInterviewDocuments(
  sessionId: string,
  files: File[],
  token: string,
): Promise<DocumentProcessingResponse> {
  const formData = new FormData();
  files.forEach((f) => formData.append("files", f));

  const response = await fetchClient(
    `/api/v1/copilot/interview/${sessionId}/documents`,
    { method: "POST", body: formData, token },
  );

  if (!response.ok) {
    throw new Error(`Document processing failed: ${response.status}`);
  }

  return response.json();
}
```

- [ ] **Step 4: Create AttachmentButton**

```typescript
// frontend/src/features/copilot/components/shared/attachment-button.tsx
"use client";

import { useRef } from "react";
import { Paperclip } from "lucide-react";
import { Button } from "@/components/ui/button";

const ACCEPTED_TYPES = ".pdf,.docx,.txt,.md,.pptx";

interface AttachmentButtonProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
  accept?: string;
}

export function AttachmentButton({
  onFilesSelected,
  disabled = false,
  accept = ACCEPTED_TYPES,
}: AttachmentButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        aria-label="Adjuntar documento"
        className="h-8 w-8 text-muted-foreground hover:text-foreground"
      >
        <Paperclip className="h-4 w-4" />
      </Button>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple
        className="hidden"
        onChange={(e) => {
          const files = Array.from(e.target.files ?? []);
          if (files.length > 0) onFilesSelected(files);
          e.target.value = "";
        }}
      />
    </>
  );
}
```

- [ ] **Step 5: Create DocumentChip**

```typescript
// frontend/src/features/copilot/components/shared/document-chip.tsx
"use client";

import { FileText, Loader2, CheckCircle2, XCircle, X } from "lucide-react";

type ProcessingStatus = "pending" | "processing" | "done" | "error";

interface DocumentChipProps {
  file: File;
  status: ProcessingStatus;
  onRemove?: () => void;
}

const STATUS_CONFIG = {
  pending: { icon: FileText, label: "", className: "bg-muted" },
  processing: { icon: Loader2, label: "Analizando...", className: "bg-primary/10 animate-pulse" },
  done: { icon: CheckCircle2, label: "Listo", className: "bg-green-500/10" },
  error: { icon: XCircle, label: "Error", className: "bg-destructive/10" },
} as const;

export function DocumentChip({ file, status, onRemove }: DocumentChipProps) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs ${config.className}`}
    >
      <Icon
        className={`h-3.5 w-3.5 ${status === "processing" ? "animate-spin" : ""}`}
      />
      <span className="max-w-[120px] truncate">{file.name}</span>
      {config.label && (
        <span className="text-muted-foreground">{config.label}</span>
      )}
      {onRemove && status === "pending" && (
        <button
          type="button"
          onClick={onRemove}
          aria-label="Eliminar documento"
          className="ml-0.5 rounded-full p-0.5 hover:bg-muted-foreground/20"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </div>
  );
}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/features/copilot/components/shared/__tests__/`
Expected: PASS

- [ ] **Step 7: Type check**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: No errors

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/copilot/components/shared/attachment-button.tsx
git add frontend/src/features/copilot/components/shared/document-chip.tsx
git add frontend/src/features/copilot/api/document-api.ts
git add frontend/src/features/copilot/components/shared/__tests__/
git commit -m "feat(copilot): add AttachmentButton + DocumentChip components"
```

---

### Task S2.5: Frontend — InterviewInput Attachment Integration

**Files:**
- Modify: `frontend/src/features/copilot/components/interview/interview-input.tsx`
- Update test: `frontend/src/features/copilot/components/interview/__tests__/interview-input.test.tsx`

**⚠️ SHARED FILE WARNING:** `interview-input.tsx` is also modified by S1 (Task S1.5). If running in parallel, S1 adds voice; S2 adds attachments. Merge carefully — both modify the same component.

- [ ] **Step 1: Add attachment test cases**

Add to the existing test file:

```typescript
it("renders attachment button", () => {
  render(<InterviewInput onSend={vi.fn()} />);
  expect(screen.getByRole("button", { name: /adjuntar/i })).toBeInTheDocument();
});

it("shows document chips when files are attached", async () => {
  render(<InterviewInput onSend={vi.fn()} />);
  // Verify the chip rendering area exists when files are added
  // This tests the integration, not the chip component itself
});
```

- [ ] **Step 2: Modify InterviewInput to include attachments**

Add to the existing `interview-input.tsx`:
1. Import `AttachmentButton` and `DocumentChip`
2. Add `attachedFiles` state (`useState<File[]>([])`)
3. Add `fileStatuses` state for tracking processing status
4. Render `AttachmentButton` next to mic and send buttons
5. Render `DocumentChip` chips above the text input area
6. On send: if files attached, first call `processInterviewDocuments()`, then `onSend(text)`
7. Export `onFilesAttached` callback prop for parent components

- [ ] **Step 3: Run tests**

Run: `cd frontend && npx vitest run src/features/copilot/components/interview/__tests__/`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/copilot/components/interview/interview-input.tsx
git add frontend/src/features/copilot/components/interview/__tests__/interview-input.test.tsx
git commit -m "feat(copilot): integrate document attachment in InterviewInput"
```

---

## Stream S3: Engine Generalization (Backend)

**Independent — no dependencies. Can run in parallel with S1 and S2.**

### Task S3.1: InterviewConfig Registry + Extension Fields

**Files:**
- Modify: `backend/src/modules/copilot/domain/interview_config.py`
- Test: `backend/tests/modules/copilot/test_config_registry.py`

**⚠️ SHARED FILE WARNING:** Also modified by S2 (Task S2.1). S3 adds `initial_research_enabled`, `context_loader`, and registry functions.

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/copilot/test_config_registry.py
import pytest
from src.modules.copilot.domain.interview_config import (
    InterviewConfig,
    InterviewBlock,
    register_interview_config,
    get_interview_config,
    DOMAIN_CONFIGS,
)


def test_register_and_retrieve_config():
    config = InterviewConfig(
        domain="test_domain",
        objetivo="test",
        bloques=[InterviewBlock(id="b1", label="B1", campos_objetivo=["f1"], prompt_context="ctx")],
        output_schema_path="test.path",
        datos_previos_fields=[],
        tono="neutral",
        expertise_template="test",
    )
    register_interview_config("test_domain", config)
    retrieved = get_interview_config("test_domain")
    assert retrieved.domain == "test_domain"
    # Cleanup
    DOMAIN_CONFIGS.pop("test_domain", None)


def test_get_nonexistent_config_raises():
    with pytest.raises(ValueError, match="No interview config"):
        get_interview_config("nonexistent_domain_xyz")


def test_config_research_fields_defaults():
    config = InterviewConfig(
        domain="test",
        objetivo="test",
        bloques=[InterviewBlock(id="b1", label="B1", campos_objetivo=["f1"], prompt_context="ctx")],
        output_schema_path="test.path",
        datos_previos_fields=[],
        tono="neutral",
        expertise_template="test",
    )
    assert config.initial_research_enabled is False
    assert config.context_loader is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_config_registry.py -v`
Expected: FAIL — `cannot import name 'register_interview_config'`

- [ ] **Step 3: Implement registry + new fields**

Read `backend/src/modules/copilot/domain/interview_config.py` and add:

```python
# Add to InterviewConfig dataclass:
    initial_research_enabled: bool = False
    context_loader: str | None = None

# Add registry at module level (after dataclass):
DOMAIN_CONFIGS: dict[str, InterviewConfig] = {}


def register_interview_config(domain: str, config: InterviewConfig) -> None:
    """Register an interview config for a domain."""
    DOMAIN_CONFIGS[domain] = config


def get_interview_config(domain: str) -> InterviewConfig:
    """Retrieve interview config by domain. Raises ValueError if not found."""
    if domain not in DOMAIN_CONFIGS:
        raise ValueError(f"No interview config registered for domain: {domain}")
    return DOMAIN_CONFIGS[domain]
```

- [ ] **Step 4: Register brand config**

Read `backend/src/modules/copilot/domain/interview_configs/brand_config.py` and add at the bottom:

```python
from src.modules.copilot.domain.interview_config import register_interview_config

register_interview_config("brand", BRAND_INTERVIEW_CONFIG)
```

- [ ] **Step 5: Update InterviewService to use registry**

Read `backend/src/modules/copilot/application/services/interview_service.py` and replace the hardcoded `DOMAIN_CONFIGS` dict (if any) with `get_interview_config(domain)` import.

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_config_registry.py -v`
Expected: PASS

- [ ] **Step 7: Run all copilot tests for regression**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -v --tb=short`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add backend/src/modules/copilot/domain/interview_config.py
git add backend/src/modules/copilot/domain/interview_configs/brand_config.py
git add backend/src/modules/copilot/application/services/interview_service.py
git add backend/tests/modules/copilot/test_config_registry.py
git commit -m "feat(copilot): add InterviewConfig registry + research/context fields"
```

---

### Task S3.2: Tavily Web Search Service

**Files:**
- Create: `backend/src/modules/copilot/infrastructure/web/__init__.py`
- Create: `backend/src/modules/copilot/infrastructure/web/tavily_search.py`
- Test: `backend/tests/modules/copilot/test_tavily_search.py`

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/copilot/test_tavily_search.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.modules.copilot.infrastructure.web.tavily_search import (
    TavilySearchService,
    SearchResult,
)


@pytest.mark.asyncio
async def test_search_returns_results():
    mock_response = {
        "results": [
            {
                "title": "Coaching pricing 2026",
                "url": "https://example.com/pricing",
                "content": "Average coaching program costs $500-$2000",
                "score": 0.95,
            }
        ]
    }
    with patch(
        "src.modules.copilot.infrastructure.web.tavily_search.httpx.AsyncClient"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(
            return_value=MagicMock(json=lambda: mock_response, status_code=200)
        )
        mock_client_cls.return_value = mock_client

        service = TavilySearchService(api_key="test-key")
        results = await service.search("coaching pricing benchmark")

        assert len(results) == 1
        assert results[0].title == "Coaching pricing 2026"
        assert results[0].relevance_score == 0.95


def test_search_result_dataclass():
    result = SearchResult(
        title="Test",
        url="https://example.com",
        content_snippet="Test content",
        relevance_score=0.8,
    )
    assert result.title == "Test"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_tavily_search.py -v`
Expected: FAIL

- [ ] **Step 3: Implement TavilySearchService**

```python
# backend/src/modules/copilot/infrastructure/web/__init__.py
```

```python
# backend/src/modules/copilot/infrastructure/web/tavily_search.py
from __future__ import annotations

from dataclasses import dataclass

import httpx
import structlog

from src.core.config import settings

logger = structlog.get_logger()

TAVILY_API_URL = "https://api.tavily.com/search"


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    content_snippet: str
    relevance_score: float


class TavilySearchService:
    """Web search via Tavily API — purpose-built for AI agents."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or getattr(settings, "TAVILY_API_KEY", "")

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
    ) -> list[SearchResult]:
        """Search the web and return structured results."""
        logger.info("tavily_search_start", query=query, max_results=max_results)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                TAVILY_API_URL,
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": search_depth,
                    "include_answer": False,
                },
            )
            response.raise_for_status()
            data = response.json()

        results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content_snippet=r.get("content", ""),
                relevance_score=r.get("score", 0.0),
            )
            for r in data.get("results", [])
        ]

        logger.info("tavily_search_done", query=query, results_count=len(results))
        return results
```

- [ ] **Step 4: Add TAVILY_API_KEY to settings**

Read `backend/src/core/config.py` and add:

```python
    TAVILY_API_KEY: str = ""
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_tavily_search.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/copilot/infrastructure/web/
git add backend/tests/modules/copilot/test_tavily_search.py
git add backend/src/core/config.py
git commit -m "feat(copilot): add TavilySearchService for web research"
```

---

### Task S3.3: Web Research Interview Tool

**Files:**
- Create: `backend/src/modules/copilot/application/tools/interview/web_research.py`
- Modify: `backend/src/modules/copilot/application/tools/registry.py` (add to interview group)
- Test: `backend/tests/modules/copilot/test_web_research_tool.py`

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/copilot/test_web_research_tool.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from src.modules.copilot.application.tools.interview.web_research import web_research


@pytest.mark.asyncio
async def test_web_research_returns_results():
    from src.modules.copilot.infrastructure.web.tavily_search import SearchResult

    mock_results = [
        SearchResult(
            title="Coaching pricing 2026",
            url="https://example.com",
            content_snippet="Programs range $500-$2000",
            relevance_score=0.9,
        )
    ]

    with patch(
        "src.modules.copilot.application.tools.interview.web_research.TavilySearchService"
    ) as mock_cls:
        mock_service = MagicMock()
        mock_service.search = AsyncMock(return_value=mock_results)
        mock_cls.return_value = mock_service

        result = await web_research.ainvoke({"query": "coaching pricing", "max_results": 3})
        parsed = json.loads(result)

        assert "results" in parsed
        assert len(parsed["results"]) == 1
        assert parsed["results"][0]["title"] == "Coaching pricing 2026"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_web_research_tool.py -v`
Expected: FAIL

- [ ] **Step 3: Implement web_research tool**

```python
# backend/src/modules/copilot/application/tools/interview/web_research.py
from __future__ import annotations

import json
from langchain_core.tools import tool

from src.modules.copilot.infrastructure.web.tavily_search import TavilySearchService


@tool
async def web_research(query: str, max_results: int = 5) -> str:
    """Search the web for competitor analysis, pricing benchmarks, and niche insights.

    Use this tool to research the user's market: competitor offers, pricing,
    best practices, and industry trends. Returns structured search results.

    Args:
        query: Search query describing what to research
        max_results: Maximum number of results to return (default 5)
    """
    service = TavilySearchService()
    results = await service.search(query=query, max_results=max_results)

    return json.dumps(
        {
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.content_snippet,
                    "relevance": r.relevance_score,
                }
                for r in results
            ]
        },
        ensure_ascii=False,
    )
```

- [ ] **Step 4: Register in tool registry**

Read `backend/src/modules/copilot/application/tools/registry.py`. Add `web_research` to the `INTERVIEW_TOOLS` list:

```python
from src.modules.copilot.application.tools.interview.web_research import web_research
# Add to INTERVIEW_TOOLS list:
INTERVIEW_TOOLS = [...existing_tools..., web_research]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_web_research_tool.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/copilot/application/tools/interview/web_research.py
git add backend/src/modules/copilot/application/tools/registry.py
git add backend/tests/modules/copilot/test_web_research_tool.py
git commit -m "feat(copilot): add web_research interview tool with Tavily"
```

---

### Task S3.4: Context Loader Registry

**Files:**
- Create: `backend/src/modules/copilot/infrastructure/context/__init__.py`
- Create: `backend/src/modules/copilot/infrastructure/context/context_loader_registry.py`
- Create: `backend/src/modules/copilot/infrastructure/context/offer_context_loader.py`
- Test: `backend/tests/modules/copilot/test_context_loaders.py`

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/copilot/test_context_loaders.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4

from src.modules.copilot.infrastructure.context.context_loader_registry import (
    get_context_loader,
)
from src.modules.copilot.infrastructure.context.offer_context_loader import (
    OfferContextLoader,
)


def test_get_context_loader_offer():
    db = MagicMock()
    loader = get_context_loader("offer_context", db)
    assert isinstance(loader, OfferContextLoader)


def test_get_context_loader_unknown_raises():
    with pytest.raises(ValueError, match="No context loader"):
        get_context_loader("nonexistent", MagicMock())


@pytest.mark.asyncio
async def test_offer_context_loader_with_no_offers():
    mock_db = MagicMock()
    mock_db.execute = AsyncMock(return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: [])))

    loader = OfferContextLoader(mock_db)
    result = await loader.load(tenant_id=uuid4(), entity_id=uuid4())

    assert isinstance(result, str)
    assert "No hay otros offers" in result or result == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_context_loaders.py -v`
Expected: FAIL

- [ ] **Step 3: Implement context loader registry**

```python
# backend/src/modules/copilot/infrastructure/context/__init__.py
```

```python
# backend/src/modules/copilot/infrastructure/context/context_loader_registry.py
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.copilot.infrastructure.context.offer_context_loader import (
    OfferContextLoader,
)

CONTEXT_LOADERS = {
    "offer_context": OfferContextLoader,
}


def get_context_loader(key: str, db: AsyncSession):
    """Get context loader by key. Raises ValueError if not found."""
    loader_cls = CONTEXT_LOADERS.get(key)
    if not loader_cls:
        raise ValueError(f"No context loader registered for key: {key}")
    return loader_cls(db)
```

```python
# backend/src/modules/copilot/infrastructure/context/offer_context_loader.py
from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.offer.infrastructure.models.offer_model import OfferModel

logger = structlog.get_logger()

VALUE_LEVEL_ORDER = [
    "LEAD_MAGNET", "ACTIVACION", "TRANSFORMACION", "MAXIMIZACION", "CORPORATIVO",
]


class OfferContextLoader:
    """Loads other offers from the tenant for interview context."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def load(self, tenant_id: UUID, entity_id: UUID | None = None) -> str:
        """Load all offers for tenant, build ladder context string."""
        stmt = (
            select(OfferModel)
            .where(OfferModel.tenant_id == tenant_id)
            .where(OfferModel.deleted_at.is_(None))
        )
        if entity_id:
            stmt = stmt.where(OfferModel.id != entity_id)

        result = await self.db.execute(stmt)
        offers = result.scalars().all()

        if not offers:
            return "No hay otros offers en el negocio. Este es el primero."

        lines = ["Otros offers del negocio:"]
        for offer in sorted(offers, key=lambda o: VALUE_LEVEL_ORDER.index(o.value_level) if o.value_level in VALUE_LEVEL_ORDER else 99):
            price = offer.price_pay_in_full or "sin precio"
            lines.append(
                f"- {offer.public_name} ({offer.archetype}, {offer.value_level}): {offer.currency or ''} {price} — {offer.status}"
            )

        # Identify ladder gaps
        existing_levels = {o.value_level for o in offers}
        gaps = [level for level in VALUE_LEVEL_ORDER if level not in existing_levels]
        if gaps:
            lines.append(f"\nGaps en el ladder: {', '.join(gaps)}")

        return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_context_loaders.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/copilot/infrastructure/context/
git add backend/tests/modules/copilot/test_context_loaders.py
git commit -m "feat(copilot): add context loader registry + OfferContextLoader"
```

---

### Task S3.5: InterviewService — Support entity_id, context, and research

**Files:**
- Modify: `backend/src/modules/copilot/application/services/interview_service.py`
- Modify: `backend/src/modules/copilot/domain/interview_session.py` (add entity_id field)
- Test: `backend/tests/modules/copilot/test_interview_service_extensions.py`

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/copilot/test_interview_service_extensions.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4


def test_interview_session_accepts_entity_id():
    from src.modules.copilot.domain.interview_session import InterviewSession, InterviewStatus
    from src.modules.copilot.domain.interview_config import InterviewConfig, InterviewBlock

    config = InterviewConfig(
        domain="offer",
        objetivo="test",
        bloques=[InterviewBlock(id="b1", label="B1", campos_objetivo=["f1"], prompt_context="ctx")],
        output_schema_path="test",
        datos_previos_fields=[],
        tono="test",
        expertise_template="test",
    )

    session = InterviewSession.create(
        tenant_id=uuid4(),
        domain="offer",
        config=config,
        conversation_id=uuid4(),
        entity_id=uuid4(),
        initial_mapa={"public_name": "Test Offer"},
    )

    assert session.entity_id is not None
    assert session.mapa_global == {"public_name": "Test Offer"}
    assert session.status == InterviewStatus.ACTIVE
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_service_extensions.py -v`
Expected: FAIL — `TypeError: unexpected keyword argument 'entity_id'`

- [ ] **Step 3: Extend InterviewSession.create()**

Read `backend/src/modules/copilot/domain/interview_session.py` and modify:

1. Add `entity_id: UUID | None = None` to `__init__`
2. Add `entity_id` and `initial_mapa` params to `create()`:

```python
    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        domain: str,
        config: InterviewConfig,
        conversation_id: UUID,
        entity_id: UUID | None = None,
        initial_mapa: dict | None = None,
    ) -> InterviewSession:
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            domain=domain,
            config_snapshot=asdict(config),
            conversation_id=conversation_id,
            mapa_global=initial_mapa or {},
            bloque_actual=config.bloques[0].id,
            bloques_completados=[],
            status=InterviewStatus.ACTIVE,
            messages_count=0,
            entity_id=entity_id,
        )
```

- [ ] **Step 4: Add entity_id to InterviewSessionModel**

Read `backend/src/modules/copilot/infrastructure/models/interview_session_model.py` and add:

```python
    entity_id = Column(UUID(as_uuid=True), nullable=True)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_service_extensions.py -v`
Expected: PASS

- [ ] **Step 6: Run all copilot tests for regression**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -v --tb=short`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add backend/src/modules/copilot/domain/interview_session.py
git add backend/src/modules/copilot/infrastructure/models/interview_session_model.py
git add backend/src/modules/copilot/application/services/interview_service.py
git add backend/tests/modules/copilot/test_interview_service_extensions.py
git commit -m "feat(copilot): extend InterviewSession with entity_id + initial_mapa"
```

---

## Stream S4: Buyer Persona (Backend)

**Depends on S3 (registry). Run in Phase B.**

### Task S4.1: BuyerPersona Domain Entity

**Files:**
- Create: `backend/src/modules/brand/domain/buyer_persona.py`
- Test: `backend/tests/modules/brand/test_buyer_persona_entity.py`

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/brand/test_buyer_persona_entity.py
from uuid import uuid4
from src.modules.brand.domain.buyer_persona import BuyerPersona


def test_create_buyer_persona():
    persona = BuyerPersona(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        name="María",
        tagline="Quiere escalar sin perder autenticidad",
    )
    assert persona.name == "María"
    assert persona.scope == "GLOBAL"
    assert persona.is_primary is False
    assert persona.demographics == {}
    assert persona.pain_points == []
    assert persona.completeness_score == 0.0


def test_buyer_persona_with_full_profile():
    persona = BuyerPersona(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        name="Carlos",
        demographics={"age_range": "30-40", "location": "LATAM"},
        pain_points=[{"description": "No puede escalar", "intensity": "high"}],
        desires=[{"description": "Automatizar ventas", "priority": "high"}],
        completeness_score=45.0,
    )
    assert persona.demographics["age_range"] == "30-40"
    assert len(persona.pain_points) == 1
    assert persona.completeness_score == 45.0


def test_buyer_persona_offer_scope():
    offer_id = uuid4()
    persona = BuyerPersona(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        name="Offer Persona",
        scope="OFFER",
        offer_id=offer_id,
    )
    assert persona.scope == "OFFER"
    assert persona.offer_id == offer_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/brand/test_buyer_persona_entity.py -v`
Expected: FAIL

- [ ] **Step 3: Implement BuyerPersona entity**

```python
# backend/src/modules/brand/domain/buyer_persona.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from src.shared.domain.base_entity import BaseEntity


class BuyerPersona(BaseEntity):
    """Rich buyer persona entity — replaces the lightweight Avatar."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    name: str
    tagline: str | None = None
    scope: str = "GLOBAL"
    offer_id: UUID | None = None
    is_primary: bool = False

    # Profile (JSONB — flexible, evolves with interview)
    demographics: dict = {}
    psychographics: dict = {}
    pain_points: list[dict] = []
    desires: list[dict] = []
    objections: list[dict] = []
    preferred_channels: list[dict] = []
    buyer_journey: dict = {}
    purchase_triggers: list[str] = []
    anti_patterns: list[str] = []

    # Metadata
    completeness_score: float = 0.0
    interview_session_id: UUID | None = None

    # Soft delete
    is_active: bool = True
    deleted_at: datetime | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/brand/test_buyer_persona_entity.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/brand/domain/buyer_persona.py
git add backend/tests/modules/brand/test_buyer_persona_entity.py
git commit -m "feat(brand): add BuyerPersona domain entity"
```

---

### Task S4.2: BuyerPersona SQLAlchemy Model + Migration

**Files:**
- Create: `backend/src/modules/brand/infrastructure/models/buyer_persona_model.py`
- Create: `backend/alembic/versions/xxxx_add_buyer_personas.py` (via alembic)
- Test: `backend/tests/modules/brand/test_buyer_persona_model.py`

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/brand/test_buyer_persona_model.py
from src.modules.brand.infrastructure.models.buyer_persona_model import BuyerPersonaModel


def test_buyer_persona_model_tablename():
    assert BuyerPersonaModel.__tablename__ == "buyer_personas"


def test_buyer_persona_model_has_required_columns():
    columns = {c.name for c in BuyerPersonaModel.__table__.columns}
    expected = {
        "id", "tenant_id", "user_id", "name", "tagline", "scope",
        "offer_id", "is_primary", "demographics", "psychographics",
        "pain_points", "desires", "objections", "preferred_channels",
        "buyer_journey", "purchase_triggers", "anti_patterns",
        "completeness_score", "interview_session_id",
        "is_active", "deleted_at", "created_at", "updated_at",
    }
    assert expected.issubset(columns)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/brand/test_buyer_persona_model.py -v`
Expected: FAIL

- [ ] **Step 3: Create SQLAlchemy model**

```python
# backend/src/modules/brand/infrastructure/models/buyer_persona_model.py
from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index,
    String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.shared.domain.base_entity import Base


class BuyerPersonaModel(Base):
    __tablename__ = "buyer_personas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False)
    tagline = Column(Text, nullable=True)
    scope = Column(String(20), nullable=False, default="GLOBAL")
    offer_id = Column(UUID(as_uuid=True), ForeignKey("offers.id", ondelete="SET NULL"), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)

    demographics = Column(JSONB, nullable=False, default=dict)
    psychographics = Column(JSONB, nullable=False, default=dict)
    pain_points = Column(JSONB, nullable=False, default=list)
    desires = Column(JSONB, nullable=False, default=list)
    objections = Column(JSONB, nullable=False, default=list)
    preferred_channels = Column(JSONB, nullable=False, default=list)
    buyer_journey = Column(JSONB, nullable=False, default=dict)
    purchase_triggers = Column(JSONB, nullable=False, default=list)
    anti_patterns = Column(JSONB, nullable=False, default=list)

    completeness_score = Column(Float, nullable=False, default=0.0)
    interview_session_id = Column(UUID(as_uuid=True), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_buyer_personas_tenant_scope", "tenant_id", "scope"),
    )
```

- [ ] **Step 4: Register model in model registry**

Read `backend/src/shared/infrastructure/model_registry.py` (or wherever models are imported for Alembic) and add the import:

```python
from src.modules.brand.infrastructure.models.buyer_persona_model import BuyerPersonaModel  # noqa: F401
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/brand/test_buyer_persona_model.py -v`
Expected: PASS

- [ ] **Step 6: Create idempotent migration**

Create migration file using alembic, then replace content with idempotent raw SQL:

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && alembic revision --autogenerate -m 'add_buyer_personas'"
```

Then edit the generated file to use idempotent SQL as per project rules (IF NOT EXISTS for table, columns, indexes).

- [ ] **Step 7: Apply migration**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"
```

- [ ] **Step 8: Commit**

```bash
git add backend/src/modules/brand/infrastructure/models/buyer_persona_model.py
git add backend/src/shared/infrastructure/model_registry.py
git add backend/alembic/versions/*buyer_personas*
git add backend/tests/modules/brand/test_buyer_persona_model.py
git commit -m "feat(brand): add BuyerPersona SQLAlchemy model + migration"
```

---

### Task S4.3: BuyerPersona Repository

**Files:**
- Create: `backend/src/modules/brand/infrastructure/repositories/buyer_persona_repository.py`
- Test: `backend/tests/modules/brand/test_buyer_persona_repository.py`

- [ ] **Step 1-5: TDD cycle**

Follow the same repository pattern as `avatar_repository.py`. Implement:
- `create(tenant_id, persona: BuyerPersona) → BuyerPersona`
- `get_by_id(tenant_id, persona_id) → BuyerPersona | None`
- `list_by_tenant(tenant_id, scope?) → list[BuyerPersona]`
- `update(tenant_id, persona_id, updates: dict) → BuyerPersona`
- `soft_delete(tenant_id, persona_id) → None`

All methods MUST filter by `tenant_id`. Use SA 2.0 syntax (`select().where()`).

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/brand/infrastructure/repositories/buyer_persona_repository.py
git add backend/tests/modules/brand/test_buyer_persona_repository.py
git commit -m "feat(brand): add BuyerPersona repository with tenant isolation"
```

---

### Task S4.4: BuyerPersona Interview Config + Expertise Template

**Files:**
- Create: `backend/src/modules/copilot/domain/interview_configs/buyer_persona_config.py`
- Create: `backend/src/modules/copilot/infrastructure/prompts/templates/interview/buyer_persona_expertise.j2`
- Create: `backend/src/modules/copilot/infrastructure/prompts/templates/interview/buyer_persona_doc_extraction.j2`
- Test: `backend/tests/modules/copilot/test_buyer_persona_config.py`

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/copilot/test_buyer_persona_config.py
from src.modules.copilot.domain.interview_configs.buyer_persona_config import (
    BUYER_PERSONA_INTERVIEW_CONFIG,
)
from src.modules.copilot.domain.interview_config import get_interview_config


def test_buyer_persona_config_registered():
    config = get_interview_config("buyer_persona")
    assert config.domain == "buyer_persona"


def test_buyer_persona_has_5_blocks():
    config = BUYER_PERSONA_INTERVIEW_CONFIG
    assert len(config.bloques) == 5


def test_buyer_persona_block_ids():
    config = BUYER_PERSONA_INTERVIEW_CONFIG
    block_ids = [b.id for b in config.bloques]
    assert block_ids == ["demographics", "psychographics", "pain_desire", "objections", "channels_journey"]


def test_buyer_persona_has_document_template():
    config = BUYER_PERSONA_INTERVIEW_CONFIG
    assert config.document_extraction_template == "buyer_persona_doc_extraction"


def test_buyer_persona_all_blocks_have_campos():
    config = BUYER_PERSONA_INTERVIEW_CONFIG
    for block in config.bloques:
        assert len(block.campos_objetivo) > 0, f"Block {block.id} has no campos_objetivo"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_buyer_persona_config.py -v`
Expected: FAIL

- [ ] **Step 3: Create buyer_persona_config.py**

Use the exact config from the spec (Section 5.4) — 5 InterviewBlocks with all campos_objetivo as specified. Register via `register_interview_config("buyer_persona", ...)`.

- [ ] **Step 4: Create expertise template**

```jinja2
{# buyer_persona_expertise.j2 #}
{# Frameworks: Jobs-to-be-Done, Empathy Map, Buyer Persona Canvas #}
{# Content from spec Section 5.5 #}
```

- [ ] **Step 5: Create document extraction template**

```jinja2
{# buyer_persona_doc_extraction.j2 #}
Analiza el siguiente documento y extrae información sobre el buyer persona.
Extrae campos en formato JSON plano con dot-notation.
...
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_buyer_persona_config.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/src/modules/copilot/domain/interview_configs/buyer_persona_config.py
git add backend/src/modules/copilot/infrastructure/prompts/templates/interview/buyer_persona_expertise.j2
git add backend/src/modules/copilot/infrastructure/prompts/templates/interview/buyer_persona_doc_extraction.j2
git add backend/tests/modules/copilot/test_buyer_persona_config.py
git commit -m "feat(copilot): add BuyerPersona interview config + expertise template"
```

---

### Task S4.5: BuyerPersonaPersister

**Files:**
- Create: `backend/src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py`
- Modify: `backend/src/modules/copilot/infrastructure/persisters/persister_registry.py`
- Test: `backend/tests/modules/copilot/test_buyer_persona_persister.py`

- [ ] **Step 1-5: TDD cycle**

Pattern: same as BrandPersister but writes to BuyerPersona entity via BuyerPersonaRepository.

Key logic:
- Dot-notation paths: `"demographics.age_range"` → `persona.demographics["age_range"]`
- List fields: `"pain_points"` → `persona.pain_points` (replace full list)
- Calculate `completeness_score` after persist
- Add `"buyer_persona": BuyerPersonaPersister` to `persister_registry.py`
- Also implement `load_existing(tenant_id, entity_id) → dict` for pre-filling mapa_global

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py
git add backend/src/modules/copilot/infrastructure/persisters/persister_registry.py
git add backend/tests/modules/copilot/test_buyer_persona_persister.py
git commit -m "feat(copilot): add BuyerPersonaPersister + register in registry"
```

---

## Stream S5: Offer Interview (Backend)

**Depends on S3 (registry + web research). Run in Phase B.**

### Task S5.1: Offer Interview Config + Expertise Template

**Files:**
- Create: `backend/src/modules/copilot/domain/interview_configs/offer_config.py`
- Create: `backend/src/modules/copilot/infrastructure/prompts/templates/interview/offer_expertise.j2`
- Create: `backend/src/modules/copilot/infrastructure/prompts/templates/interview/offer_doc_extraction.j2`
- Test: `backend/tests/modules/copilot/test_offer_config.py`

- [ ] **Step 1: Write the test**

```python
# backend/tests/modules/copilot/test_offer_config.py
from src.modules.copilot.domain.interview_configs.offer_config import (
    OFFER_INTERVIEW_CONFIG,
)
from src.modules.copilot.domain.interview_config import get_interview_config


def test_offer_config_registered():
    config = get_interview_config("offer")
    assert config.domain == "offer"


def test_offer_has_6_blocks():
    config = OFFER_INTERVIEW_CONFIG
    assert len(config.bloques) == 6


def test_offer_block_ids():
    config = OFFER_INTERVIEW_CONFIG
    block_ids = [b.id for b in config.bloques]
    assert block_ids == [
        "identity_strategy", "promise", "psychology",
        "pricing", "value_stack", "closing",
    ]


def test_offer_has_research_enabled():
    config = OFFER_INTERVIEW_CONFIG
    assert config.initial_research_enabled is True


def test_offer_has_context_loader():
    config = OFFER_INTERVIEW_CONFIG
    assert config.context_loader == "offer_context"


def test_offer_has_document_template():
    config = OFFER_INTERVIEW_CONFIG
    assert config.document_extraction_template == "offer_doc_extraction"
```

- [ ] **Step 2-6: TDD cycle**

Create `offer_config.py` with 6 blocks from spec Section 6.2. Register via `register_interview_config("offer", ...)`.
Create `offer_expertise.j2` with Value Stacking, Pricing Psychology, Guarantee Framework, Objection Mapping from spec Section 6.7.
Create `offer_doc_extraction.j2` for document extraction.

- [ ] **Step 7: Commit**

```bash
git add backend/src/modules/copilot/domain/interview_configs/offer_config.py
git add backend/src/modules/copilot/infrastructure/prompts/templates/interview/offer_expertise.j2
git add backend/src/modules/copilot/infrastructure/prompts/templates/interview/offer_doc_extraction.j2
git add backend/tests/modules/copilot/test_offer_config.py
git commit -m "feat(copilot): add Offer interview config + expertise template"
```

---

### Task S5.2: OfferPersister

**Files:**
- Create: `backend/src/modules/copilot/infrastructure/persisters/offer_persister.py`
- Modify: `backend/src/modules/copilot/infrastructure/persisters/persister_registry.py`
- Test: `backend/tests/modules/copilot/test_offer_persister.py`

- [ ] **Step 1-5: TDD cycle**

Key logic:
- Writes to existing Offer entity (requires entity_id)
- Complex type mapping: `"objections"` → `list[ObjectionItem]`, `"pricing_options"` → `list[PricingStructure]`
- Load existing offer data for pre-filling
- Add `"offer": OfferPersister` to registry
- Implement `load_existing(tenant_id, entity_id) → dict`

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/copilot/infrastructure/persisters/offer_persister.py
git add backend/src/modules/copilot/infrastructure/persisters/persister_registry.py
git add backend/tests/modules/copilot/test_offer_persister.py
git commit -m "feat(copilot): add OfferPersister + register in registry"
```

---

## Stream S6: Frontend Generalization

**Depends on S3 (architecture patterns). Run in Phase B.**

### Task S6.1: Preview Registry

**Files:**
- Create: `frontend/src/features/copilot/config/interview-preview-registry.ts`
- Test: `frontend/src/features/copilot/config/__tests__/interview-preview-registry.test.ts`

- [ ] **Step 1: Write the test**

```typescript
// frontend/src/features/copilot/config/__tests__/interview-preview-registry.test.ts
import { describe, it, expect } from "vitest";
import {
  registerPreview,
  getPreview,
  type PreviewConfig,
} from "../interview-preview-registry";

const mockConfig: PreviewConfig = {
  summaryComponent: () => null,
  sectionsComponent: () => null,
  emptyStateMessage: "No data yet",
};

describe("interview-preview-registry", () => {
  it("registers and retrieves a preview config", () => {
    registerPreview("test_domain", mockConfig);
    const result = getPreview("test_domain");
    expect(result).toBe(mockConfig);
  });

  it("throws for unregistered domain", () => {
    expect(() => getPreview("nonexistent_xyz")).toThrow("No preview registered");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/copilot/config/__tests__/interview-preview-registry.test.ts`
Expected: FAIL

- [ ] **Step 3: Implement PreviewRegistry**

Use the exact interfaces from spec Section 4.4.

- [ ] **Step 4: Run test, verify pass, commit**

```bash
git add frontend/src/features/copilot/config/interview-preview-registry.ts
git add frontend/src/features/copilot/config/__tests__/
git commit -m "feat(copilot): add interview PreviewRegistry"
```

---

### Task S6.2: Generalize InterviewSplitView

**Files:**
- Move: `frontend/src/features/brand/components/interview/interview-split-view.tsx` → `frontend/src/features/copilot/components/interview/interview-split-view.tsx`
- Create: `frontend/src/features/brand/components/interview/brand-preview-summary.tsx`
- Create: `frontend/src/features/brand/components/interview/brand-preview-sections.tsx`
- Modify: `frontend/src/app/(main)/brand-studio/interview/page.tsx` (update import)
- Test: `frontend/src/features/copilot/components/interview/__tests__/interview-split-view.test.tsx`

- [ ] **Step 1: Write the test for generic split view**

```typescript
// frontend/src/features/copilot/components/interview/__tests__/interview-split-view.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("../../../config/interview-preview-registry", () => ({
  getPreview: vi.fn().mockReturnValue({
    summaryComponent: () => <div data-testid="mock-summary">Summary</div>,
    sectionsComponent: () => <div data-testid="mock-sections">Sections</div>,
    emptyStateMessage: "No data",
  }),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("token") }),
}));

// Mock the chat panel
vi.mock("../interview-chat-panel", () => ({
  InterviewChatPanel: () => <div data-testid="chat-panel">Chat</div>,
}));

import { InterviewSplitView } from "../interview-split-view";

describe("InterviewSplitView (generic)", () => {
  it("renders preview from registry and chat panel", () => {
    render(<InterviewSplitView domain="test" />);
    expect(screen.getByTestId("mock-summary")).toBeInTheDocument();
    expect(screen.getByTestId("mock-sections")).toBeInTheDocument();
    expect(screen.getByTestId("chat-panel")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2-5: Refactor**

1. Extract brand-specific preview logic into `brand-preview-summary.tsx` and `brand-preview-sections.tsx`
2. Register them in the PreviewRegistry as `"brand"`
3. Rewrite `interview-split-view.tsx` to be generic (accept `domain` prop, load from registry)
4. Move file to `copilot/components/interview/`
5. Update brand interview page import
6. Verify old brand interview still works

- [ ] **Step 6: Run tests, commit**

```bash
git add frontend/src/features/copilot/components/interview/interview-split-view.tsx
git add frontend/src/features/brand/components/interview/brand-preview-summary.tsx
git add frontend/src/features/brand/components/interview/brand-preview-sections.tsx
git add frontend/src/app/\(main\)/brand-studio/interview/page.tsx
git add frontend/src/features/copilot/components/interview/__tests__/
git commit -m "refactor(copilot): generalize InterviewSplitView with PreviewRegistry"
```

---

## Stream S7: Buyer Persona Preview (Frontend)

**Depends on S4 + S6. Run in Phase C.**

### Task S7.1: Persona Preview Components + Registry Entry

**Files:**
- Create: `frontend/src/features/brand/components/interview/previews/persona-preview-summary.tsx`
- Create: `frontend/src/features/brand/components/interview/previews/persona-preview-sections.tsx`
- Create: `frontend/src/features/brand/components/interview/previews/index.ts` (register)
- Test: `frontend/src/features/brand/components/interview/previews/__tests__/persona-preview.test.tsx`

- [ ] **Step 1-5: TDD cycle**

Build the hybrid preview (ficha resumen + sections) as specified in the mockups:
- Summary: avatar circle + name + tagline + % completado
- Sections: Demographics, Psychographics, Pain Points (red border), Desires (green border), Objections, Channels, Journey
- Register in PreviewRegistry as `"buyer_persona"`

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/brand/components/interview/previews/
git commit -m "feat(brand): add BuyerPersona interview preview components"
```

---

## Stream S8: Offer Preview (Frontend)

**Depends on S5 + S6. Run in Phase C.**

### Task S8.1: Offer Preview Components + Registry Entry

**Files:**
- Create: `frontend/src/features/offer-studio/components/interview/previews/offer-preview-summary.tsx`
- Create: `frontend/src/features/offer-studio/components/interview/previews/offer-preview-sections.tsx`
- Create: `frontend/src/features/offer-studio/components/interview/previews/index.ts` (register)
- Test: `frontend/src/features/offer-studio/components/interview/previews/__tests__/offer-preview.test.tsx`

- [ ] **Step 1-5: TDD cycle**

Build the complete view preview (7 sections) as specified:
- Summary: archetype icon + name + tags + price + % completado
- 7 Sections: Identity, Strategy, Promise, Psychology (pains/desires/objections), Pricing, Value Stack, Closing
- Each section shows progress and live data
- Register in PreviewRegistry as `"offer"`

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/offer-studio/components/interview/previews/
git commit -m "feat(offer): add Offer interview preview components"
```

---

## Stream S9: Entry Points + Routing

**Depends on all other streams. Run in Phase D.**

### Task S9.1: Interview Mode Button + Section Chat Trigger

**Files:**
- Create: `frontend/src/features/copilot/components/shared/interview-mode-button.tsx`
- Create: `frontend/src/features/copilot/components/shared/section-chat-trigger.tsx`
- Test both components

- [ ] **Step 1-5: TDD cycle for both components**

`InterviewModeButton`:
- Props: `{ domain: string; entityId?: string; label?: string }`
- Renders button with chat icon + label (default: "Modo Entrevista")
- On click: navigates to interview route with correct params

`SectionChatTrigger`:
- Props: `{ sectionId: string; sectionLabel: string }`
- Renders small icon button next to section title
- On click: opens copilot panel with section context pre-loaded

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/copilot/components/shared/interview-mode-button.tsx
git add frontend/src/features/copilot/components/shared/section-chat-trigger.tsx
git commit -m "feat(copilot): add InterviewModeButton + SectionChatTrigger"
```

---

### Task S9.2: Buyer Persona Interview Route

**Files:**
- Create: `frontend/src/app/(main)/brand-studio/interview/buyer-persona/page.tsx`
- Modify: `backend/src/modules/copilot/application/tools/registry.py` (add route mapping)

- [ ] **Step 1-3: Create route + register tool mapping**

Page: thin Server Component that renders `<InterviewSplitView domain="buyer_persona" />`
Backend: add `"brand-studio/interview/buyer-persona": ["interview", "knowledge"]` to `ROUTE_TOOL_MAP`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/\(main\)/brand-studio/interview/buyer-persona/page.tsx
git add backend/src/modules/copilot/application/tools/registry.py
git commit -m "feat(brand): add buyer persona interview route"
```

---

### Task S9.3: Offer Interview Route

**Files:**
- Create: `frontend/src/app/(main)/offer-studio/interview/page.tsx`
- Modify: `backend/src/modules/copilot/application/tools/registry.py` (add route mapping)

- [ ] **Step 1-3: Create route + register tool mapping**

Page: reads `offerId` from searchParams, renders `<InterviewSplitView domain="offer" offerId={offerId} />`
Backend: add `"offer-studio/interview": ["interview", "knowledge"]` to `ROUTE_TOOL_MAP`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/\(main\)/offer-studio/interview/page.tsx
git add backend/src/modules/copilot/application/tools/registry.py
git commit -m "feat(offer): add offer interview route"
```

---

### Task S9.4: Add Interview Mode Buttons to Studios

**Files:**
- Modify: Brand Studio header (add InterviewModeButton for brand + buyer_persona)
- Modify: Offer Studio header/card (add InterviewModeButton for offer)
- Add InterviewModeButton to Offer cards for individual offer interview

- [ ] **Step 1-3: Wire up buttons**

Read existing studio headers, add `<InterviewModeButton>` in appropriate locations.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: add Modo Entrevista buttons to Brand + Offer studios"
```

---

### Task S9.5: Migration for entity_id in interview_sessions

**Files:**
- Create: `backend/alembic/versions/xxxx_add_entity_id_to_interview_sessions.py`

- [ ] **Step 1: Create idempotent migration**

```sql
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS entity_id UUID;
```

- [ ] **Step 2: Apply and verify**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"
```

- [ ] **Step 3: Commit**

```bash
git add backend/alembic/versions/*entity_id*
git commit -m "feat(copilot): add entity_id column to interview_sessions"
```

---

### Task S9.6: Full Integration Test + Lint

- [ ] **Step 1: Run full backend tests**

Run: `cd backend && .venv/bin/pytest -x -q --tb=short`
Expected: All PASS

- [ ] **Step 2: Run backend lint**

Run: `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`
Expected: No errors

- [ ] **Step 3: Run frontend tests**

Run: `cd frontend && npx vitest run`
Expected: All PASS

- [ ] **Step 4: Run frontend type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 5: Run architecture tests**

Run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
Expected: All PASS

- [ ] **Step 6: Final commit if any fixes needed**

```bash
git commit -m "fix: resolve integration issues from Phase 3 streams"
```
