# TP6 — Channel Formatter Registry (F7)

**F# que valida:** F7 (`OutputChannelFormat` registry + `format_for_channel` tool + `synthesizer.py::_CHANNEL_HINTS`).
**Tiempo estimado:** 2 hs.
**Pre-req hard:** TP0 + TP2 (brand_summary aporta voice_tone que el formatter respeta).

---

## Misión

Confirmar que:

1. Pedir output "para WhatsApp" / "para email" / "para SMS" produce texto formateado correctamente para cada canal.
2. Markdown NO sale roto en canales que no lo soportan (WhatsApp: bullet con `•` o lineas, NO `*` ni `**`).
3. Voice/tono respeta brand mientras adapta al canal (formal email vs casual WA).
4. Caracteres especiales (emoji, unicode, ¿¡) se preservan.
5. Length limits del canal se respetan (SMS ≤160 chars).

---

## Research mandate

Queries:

- `"whatsapp business api message formatting markdown 2026"` — confirmar specs actuales (asterisks → bold? underscore → italic?).
- `"sms 160 character limit segmentation 2026"` — confirmar GSM-7 vs Unicode.
- `"email html plain text dual format LLM generation 2026"` — patrón dual.

---

## Scenarios

Matrix 4 canales × 4 tipos de contenido = 16 escenarios:

| Canal | Headline | Email | Story | CTA |
|---|---|---|---|---|
| chat | S6.1 | S6.2 | S6.3 | S6.4 |
| whatsapp | S6.5 | S6.6 | S6.7 | S6.8 |
| email | S6.9 | S6.10 | S6.11 | S6.12 |
| sms | S6.13 | S6.14 | S6.15 | S6.16 |

### Patrón S6.X — input/expected

```
prompt: "armame un {tipo} para {canal}, sobre {tema}"
expected_output_canal:
  chat: markdown rich permitido
  whatsapp: solo plain + emoji + line breaks; NO **bold** ni *italic*
  email: HTML allowed pero plain-text fallback friendly
  sms: ≤160 chars, plain, sin emoji opcional
```

DeepEval check per scenario:

```python
metric = GEval(
    name="channel_format_correctness",
    evaluation_steps=[
        f"Output respects {canal} formatting rules",
        f"No markdown noise (no ** or * for {'whatsapp' if canal=='whatsapp' else 'all'})",
        "Brand voice preserved (cálido y directo if tenant_voice='cálido y directo')",
        f"Length limit respected ({160 if canal=='sms' else 'no hard limit'})",
    ],
    evaluation_params=["actual_output"],
)
```

### S6.17 — Spanish neutro LatAm verificación

Para todos los outputs, validar voseo regex:
```python
VOSEO_RE = re.compile(r'\b(vos|tenés|querés|podés|sabés|hacés|venís|decís|mirá|dejá|poné|usá)\b')
assert not VOSEO_RE.search(output), f"Voseo found: {output}"
```

**Pass:** 0 voseo en 16 outputs.

### S6.18 — Length SMS hard

10 prompts pidiendo SMS sobre temas variados. Verificar `len(text) <= 160`.

**Pass:** 10/10 ≤160 chars.

### S6.19 — Markdown WhatsApp clean

10 prompts pidiendo WhatsApp. Regex check:
```python
MD_NOISE_RE = re.compile(r'\*\*|`{3,}|\[.+?\]\(.+?\)')
```

**Pass:** 0 matches en los 10.

---

## Tools / queries

- DeepEval: `tests/quality/deepeval/test_tp6_channel_format.py`.
- Regex validators inline.
- CopilotJudge dim `tone` para canal-específico.

---

## Targets

| Métrica | Target | Hard fail |
|---|---|---|
| Channel format correctness avg | ≥4.0 (judge) | <3.5 |
| WA sin markdown noise | 100% (10/10) | <90% |
| SMS ≤160 chars | 100% | <100% |
| Voseo neutro | 0 instances | ≥1 |
| Brand voice preserved | judge ≥4.0 | <3.5 |
| Emoji preserved | OK | mojibake |

---

## Failure playbook

| Síntoma | Investigar | Root cause | Fix |
|---|---|---|---|
| WA con `**bold**` | synthesizer hint débil | `application/tools/ask_tenant_data/synthesizer.py::_CHANNEL_HINTS['whatsapp']` | refinar prompt format hint |
| SMS >160 | length cap no enforced | `format_for_channel` post-process | agregar truncate + warning |
| Voseo en output | LLM ignoró regla 11 | system prompt o per-tenant brand voice | bumpear instruction strength |
| Mojibake | encoding chain | check char encoding entre BE → SSE → FE | UTF-8 enforce |
| Email HTML mal formado | sanitizer | `output_sanitizer.py` | tighten regex |

---

## Lo que necesito de Chris

- [ ] Tenant test con voice_tone explícito (ej: "cálido y directo") para S6 brand voice check.
- [ ] (Opcional) confirmar si tenés un endpoint que envíe el output a WA real (Manychat) para validación humana post-DeepEval.
