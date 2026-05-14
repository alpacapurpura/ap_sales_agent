# T-voice-2 RESULT — Voice samples ingestion

**State**: done · **Verdict**: tests-passing
**Validators**: V-F-17 + V-AE-28 GREEN

## Files

Source (3 files):
- `comunify/backend/src/modules/comunify/brand/voice_cloning/samples_parser.py`
- `comunify/backend/src/modules/comunify/application/tasks/__init__.py`
- `comunify/backend/src/modules/comunify/application/tasks/voice_samples_ingest_worker.py`

Tests (2 files, 25 tests):
- `comunify/backend/tests/agentic_evals/voice_cloning/test_voice_samples_pii_sanitized.py` (22 tests)
- `comunify/backend/tests/architecture/test_comunify_no_pii_in_voice_samples_persistence.py` (3 arch fitness tests)

## Acceptance summary

| Aspect | Verified by | Result |
|---|---|---|
| PII strip from chat lines (email/phone/DNI/RFC/RUT/CURP/CUIT) | 8 parser tests | ✅ |
| Voseo NOT clobbered (legit brand voice survives) | 1 parser test | ✅ |
| Voice note hint lines excluded from chat_lines | 1 parser test | ✅ |
| Voice notes counted + paths collected | 1 parser test | ✅ |
| Corrupt ZIP / missing _chat.txt graceful | 2 parser tests | ✅ |
| Whisper timeout → empty + warning (graceful-degradation) | 1 transcriber test | ✅ |
| Whisper exception → empty + warning | 1 transcriber test | ✅ |
| Transcription output PII-stripped | 1 transcriber test | ✅ |
| Worker persists COUNTS ONLY (D15 invariant) | 1 worker test + 1 arch fitness | ✅ |
| Worker deletes original upload (D15) | 1 worker test | ✅ |
| Worker handles fetch / persist failures gracefully | 2 worker tests | ✅ |
| Worker auto-kicks distillation at threshold | 1 worker test | ✅ |
| Arch fitness: `upload_history_entry` allowlist | 1 arch test | ✅ |
| Arch fitness: ORM model has no raw-content fields | 1 arch test | ✅ |

## Gate output

```
$ cd /home/chris/luana-platform/comunify/backend && \
    .venv/bin/pytest tests/agentic_evals/voice_cloning/test_voice_samples_pii_sanitized.py \
    tests/architecture/test_comunify_no_pii_in_voice_samples_persistence.py -q --tb=short
.........................                                                [100%]
25 passed in 0.6s
```

## Footer

done -> docs/product/stories/luana-comunify-bootstrap/T-voice-2-result.md
