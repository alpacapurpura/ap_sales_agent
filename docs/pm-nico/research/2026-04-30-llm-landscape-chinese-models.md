# LLM Landscape 2026-04-30 — Chinese Models Cost/Quality Benchmark

## Meta
- Fecha: 2026-04-30
- Owner: /pm
- Trigger: PI-2-copilot-improvement S2 — evaluar migración stack copilot Nicolify
- Métrica decisional Chris: (1) escalabilidad 1000+ tenants, (2) latencia p99 <200ms hot paths, (3) costo LLM optimizado ponderado vs calidad. Si chino bate incumbente >2 dimensiones → migrar. Si falla eval gate vs incumbente → mantener.

## Resumen ejecutivo
- **DeepSeek V4-Pro (lanzado 2026-04-24)** = candidato #1 reemplazo Claude Sonnet/Opus en specialist tasks: 80.6% SWE-bench Verified vs Opus 4.7 87.6% (gap −7pts), pricing $1.74 input / $3.48 output vs Opus 4.7 $5/$25 → **~7x cheaper output, ~3x cheaper input**. 1M context default. Open weights MIT.
- **DeepSeek V4-Flash** = ganador absoluto cost/perf para classifier/routing layer: $0.14 input / $0.28 output, 1M context, 81.9 t/s, MoE 284B params. Reemplaza Kimi K2.5/GPT-4o-mini sin contest.
- **Kimi K2.6 (2026-04-20)** = mantener para summarizer / multi-agent orchestration: 256K context, $0.95/$4.00, 86.4 MMLU, 92 HumanEval, 80.2 SWE-bench. Especializado long-horizon coding + multi-agent. Pricing 5x más caro que DeepSeek V4-Flash → migrar summarizer a V4-Flash si calidad pasa eval gate.
- **GLM-5.1 / GLM-5 (Z.ai, 2026-04-07)** = wildcard #1 calidad open-source: 91.7 MMLU base / 96 reasoning, 99 HumanEval, 98 MATH-500, 58.4 SWE-Bench Pro (batió GPT-5.4 y Opus 4.6 en su release). Pricing $1.00 input. Coding-first. Considerar para tareas extraction/auto-fill complejas.
- **Qwen 3.5 Plus (Alibaba)** = wildcard #2 cost/perf masivo: $0.26 input / $1.56 output, 397B-A17B MoE. Multilingual fuerte (LatAm Spanish OK). Embeddings Qwen3-Embedding-8B = #1 MTEB multilingual (70.58) > BGE-M3 (63.0).
- **MiniMax M2.7 (2026-03-18)** = mejor Intelligence Index/$ del mercado: 50 IndexAA @ $0.30/$1.20, 205K context, self-evolving agent design. 17-21x cheaper que Opus 4.6. Output speed sub-par (46.8 t/s) → no apto hot paths latencia crítica.
- **Claude Opus 4.7** mantiene corona en benchmarks agentic complejos (SWE-bench 87.6, MCP-Atlas 77.3) pero gap costo es 25-50x vs chinos top. Justifica solo en hot path "razonamiento crítico cliente-facing".
- **GPT-5.5 (2026-04-23)** $5/$30 → no competitive vs Claude ni vs chinos. Ningún caso uso defensible Nicolify.
- **Embeddings**: migrar/confirmar Qwen3-Embedding-8B (MTEB ML 70.58, 100+ idiomas, fits RAG) sobre BGE-M3 si stack actual usa BGE.
- **Veredicto migración global: PARCIAL AGRESIVO**. 3 swaps recomendados: (1) classifier/router → DeepSeek V4-Flash, (2) specialist extraction/auto-fill → DeepSeek V4-Pro o GLM-5.1 (eval gate decide), (3) summarizer → DeepSeek V4-Flash. Mantener Claude Opus 4.7 solo cliente-facing crítico (alta variabilidad output, brand voice). Embeddings: migrar a Qwen3-Embedding-8B si actual ≠ Qwen.

## Tabla comparativa — frontier models 2026-Q2

| Model | Provider | Context | $/1M in | $/1M out | MMLU | HumanEval | MATH | SWE-bench Verified | Output t/s | TTFT (s) | Release | API |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Claude Opus 4.7 | Anthropic | 200K | $5.00 | $25.00 | n/d | n/d | n/d | 87.6 | n/d | n/d | 2026-04-16 | ✅ |
| Claude Sonnet 4.6 | Anthropic | 200K | $3.00 | $15.00 | n/d | n/d | n/d | n/d | n/d | n/d | 2026-Q1 | ✅ |
| Claude Haiku 4.5 | Anthropic | 200K | $1.00 | $5.00 | n/d | n/d | n/d | n/d | 80–120 | n/d | 2026-Q1 | ✅ |
| GPT-5.5 | OpenAI | 256K | $5.00 | $30.00 | n/d | n/d | n/d | ~84 (est) | n/d | n/d | 2026-04-23 | ✅ |
| GPT-5.5-pro | OpenAI | 256K | $30.00 | $80.00 | n/d | n/d | n/d | n/d | n/d | n/d | 2026-04-23 | ✅ |
| **DeepSeek V4-Pro** | DeepSeek | 1M | $1.74 ($0.435 promo→05-05) | $3.48 ($0.87 promo) | n/d | n/d | n/d | 80.6 | 34.4 | 0.99 (Together.ai) | 2026-04-24 | ✅ open |
| **DeepSeek V4-Flash** | DeepSeek | 1M | $0.14 | $0.28 | n/d | n/d | n/d | ~73 (est) | 81.9 | 1.03 | 2026-04-24 | ✅ open |
| **Kimi K2.6** | Moonshot | 256K | $0.95 ($0.16 cache-hit) | $4.00 | 86.4 | 92 | n/d (K2 base 70.22) | 80.2 | n/d | n/d | 2026-04-20 | ✅ open |
| **GLM-5** (base) | Z.ai | n/d | $1.00 ($0.573 cheapest) | $2.08 | 91.7 | 99 | 98 (MATH-500) | n/d | n/d | n/d | 2026-Q1 | ✅ open |
| **GLM-5 Reasoning** | Z.ai | n/d | $1.00 | $2.08 | 96 | n/d | 98 (AIME), 95 (HMMT) | n/d | n/d | n/d | 2026-Q1 | ✅ open |
| **GLM-5.1** | Z.ai | n/d | n/d | n/d | n/d | n/d | n/d | 58.4 SWE-Pro | n/d | n/d | 2026-04-07 | ✅ open |
| **Qwen 3.5 397B-A17B** | Alibaba | n/d | $0.39 | $2.34 | n/d | n/d | n/d | n/d | n/d | n/d | 2026-Q1 | ✅ open |
| **Qwen 3.5 Plus** | Alibaba | n/d | $0.26 | $1.56 | n/d | n/d | n/d | n/d | n/d | n/d | 2026-Q1 | ✅ |
| **Qwen3-32B-Base** | Alibaba | 128K+ | n/d | n/d | 65.54 (MMLU-Pro) | n/d | n/d | n/d | n/d | n/d | 2025-05 (stale 12mo) | ✅ open |
| **MiniMax M2.7** | MiniMax | 205K | $0.30 | $1.20 | n/d | n/d | n/d | 56.2 SWE-Pro, 57.0 Terminal Bench 2 | 46.8 | n/d | 2026-03-18 | ✅ open |
| **MiniMax M2** | MiniMax | 197K | $0.255 | $1.00 | n/d | n/d | n/d | n/d | n/d | n/d | 2025-10-23 | ✅ open |

Notas:
- "n/d" = no devuelto por websearch en cifra exacta; cita parcial o ausente.
- DeepSeek V4-Pro 75% off promo expira 2026-05-05 — pricing post-promo es número primario evaluación.
- Claude Opus 4.7 tokenizer nuevo emite hasta 35% más tokens mismo input → costo efectivo +35% vs nominal.
- SWE-bench Pro y SWE-bench Verified son benchmarks distintos; comparar dentro misma columna.

## Recomendación per-uso copilot Nicolify

| Uso copilot | Modelo actual (asumido) | Modelo recomendado 2026-Q2 | Justificación cuantitativa | Trade-off |
|---|---|---|---|---|
| **Classifier (router)** | Kimi K2.5 / GPT-4o-mini | **DeepSeek V4-Flash** | $0.14/$0.28 vs Kimi K2.5 ~$0.60/$2.50 → 4x cheaper input, 9x cheaper output. 81.9 t/s, TTFT 1.03s suficiente router. 1M context. | Latencia TTFT 1.03s puede no cumplir hot path <200ms — testear paralelo + cache prefix agresivo. Si falla, fallback Claude Haiku 4.5 (80–120 t/s). |
| **Specialist (extraction/auto-fill)** | Claude Sonnet 4.6 / Kimi K2.5 | **DeepSeek V4-Pro** (default) o **GLM-5 Reasoning** (calidad-first) | DeepSeek V4-Pro $1.74/$3.48 vs Sonnet $3/$15 → ~4x cheaper output, calidad SWE-Verified 80.6 vs Opus 87.6 (gap −7pts aceptable extraction). GLM-5 R: 96 MMLU, 99 HumanEval, 98 MATH → batería completa academic top. | DeepSeek output 34.4 t/s = lento para flows largos. GLM-5 1.3x más caro vs DeepSeek pero superior reasoning. **Eval gate obligatorio**: 50 goldens extraction Nicolify, threshold ≥95% pass DeepSeek/GLM vs Sonnet baseline. |
| **Summarizer (compression > N msgs)** | Claude Haiku 4.5 / Kimi K2.5 | **DeepSeek V4-Flash** | Compression task tolera latencia. $0.14/$0.28 vs Haiku $1/$5 → 7x cheaper input, 18x cheaper output. 1M context = comprimir threads largos sin chunking. | 1M context overhead memoria infra. Si Kimi K2.6 cache-hit $0.16 + flow caché-friendly → revaluar Kimi. |
| **Embeddings (semantic)** | BGE-M3 (asumido open-source) | **Qwen3-Embedding-8B** | MTEB multilingual 70.58 vs BGE-M3 63.0 → +7.58 pts, 100+ idiomas (LatAm Spanish ✓), dim flexible 32–4096, MTEB Code 80.68. | Migración requiere re-index Qdrant entero (cost compute one-time + downtime ventana). Stale source de Qwen3-Embedding (jun 2025) — confirmar no hay v2 más reciente antes commit. |
| **Cliente-facing crítico (sales_agent voice)** | Claude Sonnet 4.6 / 4.7 | **MANTENER Claude Sonnet 4.7** (no migrar) | Brand voice sales_agent = SSoT crítico (rule `sales-agent-brand-voice.md`). Anthropic instruction-following + voz consistente = competitive moat hoy. Costo justificado por valor cliente final. | Costo 10-25x vs DeepSeek. Acepta. Re-evaluar Q3 2026 cuando voice fidelity grader pueda validar Chinese model output ≥95% match brand voice. |

## Cambios sugeridos vs stack actual Nicolify

1. **Migrar classifier/router → DeepSeek V4-Flash**. Ahorro estimado: 4–9x. Ventana migración: 1 sprint. Eval gate: latencia p99 <300ms (relax vs <200ms hot path por TTFT 1.03s — clasificación tolera). Fallback Claude Haiku 4.5 si falla SLO.
2. **Migrar specialist extraction → DeepSeek V4-Pro o GLM-5 Reasoning** (decidir post-eval gate Nicolify goldens). Ahorro estimado: 4–7x output. PR-2 PI-2 candidato.
3. **Migrar summarizer → DeepSeek V4-Flash**. Ahorro estimado: 7–18x. Implementación trivial (drop-in OpenAI-compatible API). Beneficio adicional: 1M context elimina chunking lógica actual.
4. **Migrar embeddings → Qwen3-Embedding-8B** (si actual = BGE-M3 o anterior). Ganancia +7 pts MTEB ML. Re-index Qdrant requiere ventana mantenimiento (planear sprint dedicado + rollback plan).
5. **Mantener Claude Opus/Sonnet 4.7 solo en sales_agent voice** + cliente-facing crítico. Documentar criterio decisional explícito en `sales-agent-expert` skill.
6. **Descartar GPT-5.5 / GPT-5.5-pro de cualquier consideración** — sin caso uso defensible vs Anthropic + chinos.
7. **Setup observability migración**: `copilot_llm_call` table debe rastrear modelo + costo per-turn pre/post migración. Métricas ganancia validan o roll-back automático.
8. **Eval gate obligatorio antes cada migración**: 50–100 goldens per uso, threshold ≥95% calidad vs incumbente, latencia p99 medida en infra prod (no benchmark vendor).

## Trade-offs cuantitativos por modelo chino candidato

### DeepSeek V4 (Pro + Flash, 2026-04-24)
- **Pro**: 80.6 SWE-Verified (vs Opus 4.7 87.6, gap −7), 1.6T params MoE, 1M context, $1.74/$3.48 (post-promo).
- **Flash**: 284B params MoE, 1M context, $0.14/$0.28, 81.9 t/s.
- **Pros**: open MIT, mejor cost/performance ratio actual mercado para tier "near-frontier", 1M context default elimina chunking, OpenAI-compatible API.
- **Cons**: Output speed Pro 34.4 t/s = no apto streaming responsivo. TTFT 0.99–1.03s. Calidad agentic gap −7 pts SWE vs Opus 4.7. Dependencia provider (DeepSeek directo o Together/Fireworks/SiliconFlow). Censura LLM origen china potencial — no relevante uso interno Nicolify pero documentar.
- **Veredicto**: ✅ DEFAULT migración classifier + summarizer. ⚠️ EVAL-GATE specialist extraction.

### Kimi K2.6 (Moonshot, 2026-04-20)
- 256K context, $0.95/$4.00 ($0.16 cache-hit input), 86.4 MMLU, 92 HumanEval, 80.2 SWE-bench, 1T MoE.
- Multimodal (text + image + video), thinking/non-thinking modes, multi-agent orchestration design, OpenAI-compatible.
- **Pros**: Cache-hit $0.16 = brutal cost optimization si flow stack permite cache reuse alto. Multi-agent orchestration ≈ feature competitive deepagents. Calidad coding alta.
- **Cons**: 5x más caro que DeepSeek V4-Flash sin ventaja calidad clara para classifier. Context 256K < DeepSeek 1M. Sin precio cache-miss claramente competitive.
- **Veredicto**: ⚠️ MANTENER en stack actual mientras se valida cache hit rate >70%. Si cache hit <70% → reemplazar por DeepSeek V4-Flash sin pérdida.

### Qwen 3.5 (Plus + 397B-A17B, Alibaba, 2026-Q1)
- Plus: $0.26/$1.56. 397B-A17B: $0.39/$2.34. MoE 397B total / 22B activos.
- Qwen3-32B-Base: 65.54 MMLU-Pro, +Qwen3.5-9B beats GPT-OSS-120B en MMLU-Pro (82.5 vs 80.8).
- Multilingual nativo fuerte (Apache 2.0).
- **Pros**: Pricing más bajo entre opciones calidad-frontier. Multilingual = +Spanish LatAm sólido. Embeddings Qwen3-Embedding-8B #1 MTEB ML.
- **Cons**: SWE-bench scores específicos no publicados claramente (n/d). Dependencia Alibaba Cloud (puede ser geopolítica blocker para clientes US — relevante futuro Nicolify).
- **Veredicto**: ✅ EMBEDDINGS migrar a Qwen3-Embedding-8B. ⚠️ LLM Qwen3.5 evaluar como tercera opción si DeepSeek + GLM fallan eval gate.

### GLM-5 / GLM-5.1 (Z.ai, 2026-04-07 GLM-5.1)
- GLM-5: 745B params MoE, 44B activos, $1.00/$2.08, 91.7 MMLU base / 96 reasoning, 99 HumanEval, 98 MATH-500.
- GLM-5.1: 58.4 SWE-Bench Pro (batió GPT-5.4 57.7 y Opus 4.6 57.3 en release).
- Z.ai = Tsinghua spinoff, IPO HK ~$558M.
- **Pros**: Mejor open-source calidad academic actual. Coding-first. SWE-Pro lidera open-source.
- **Cons**: 30% más caro que GLM-4.7 (no es el más barato). Latencia / TTFT no medidos públicos. Pricing $1.00 input vs DeepSeek V4-Flash $0.14 → 7x cost differential.
- **Veredicto**: ⚠️ CANDIDATO PRIMARIO specialist extraction si calidad-first prioritario sobre costo. Eval gate decide DeepSeek V4-Pro vs GLM-5 R.

### MiniMax M2.7 (2026-03-18)
- $0.30/$1.20, 205K context, 50 Intelligence Index AA (vs median open-weight 28), 56.2 SWE-Pro, 57.0 Terminal Bench 2, 46.8 t/s.
- Self-evolving agent design.
- **Pros**: Mejor IndexAA/$ del mercado (frontier intelligence at $0.30 input). 17–21x cheaper Opus.
- **Cons**: Output speed 46.8 t/s = sub-median (53.4) → mal candidato hot paths streaming. Mercado adoption lower que DeepSeek/Kimi/Qwen → ecosystem support weaker.
- **Veredicto**: ⚠️ DEFER. Re-evaluar Q3 si achievement Index AA sube + tokens/s mejora.

## Modelos chinos descartados (con razón)

| Modelo | Razón descarte |
|---|---|
| Qwen3-32B-Base (2025-05, stale 12 meses) | Cifras MMLU-Pro 65.54 muy below frontier 2026-Q2. Reemplazado por Qwen 3.5 397B-A17B / Plus. |
| MiniMax M2 (2025-10) | Reemplazado por M2.7 mismo provider. M2.7 mejor en todos los ejes. |
| GLM-4.7 / GLM previas | Reemplazado por GLM-5 / GLM-5.1 mismo provider. GLM-5 supera todos benchmarks. |
| Kimi K2 / K2.5 | Reemplazado por K2.6 mismo provider (release 2026-04-20). Stack actual Nicolify usa K2.5 → upgrade K2.6 obligatorio si se mantiene Kimi. |
| MiMo V2 Pro (Xiaomi) | "Frontier-adjacent" según fuentes, 1M context, low cost — pero precio exacto y benchmarks no publicados claramente. n/d data. Re-evaluar Q3 cuando publique. |
| DeepSeek V3.2 / V3.x | Reemplazado por V4-Pro / V4-Flash (release 2026-04-24). V4 1M context default + 27% FLOPs / 10% KV cache vs V3.2 → upgrade obligatorio. |

## Sources
- [DeepSeek V4 Pro — Artificial Analysis](https://artificialanalysis.ai/models/deepseek-v4-pro)
- [DeepSeek V4 release coverage — VentureBeat](https://venturebeat.com/technology/deepseek-v4-arrives-with-near-state-of-the-art-intelligence-at-1-6th-the-cost-of-opus-4-7-gpt-5-5)
- [DeepSeek V4 release April 2026 — Fello AI](https://felloai.com/deepseek-v4/)
- [DeepSeek V4 — DataCamp](https://www.datacamp.com/blog/deepseek-v4)
- [DeepSeek V4 Flash performance metrics — BSWEN](https://docs.bswen.com/blog/2026-04-26-deepseek-v4-flash-performance-metrics/)
- [DeepSeek-V4 million-token context — Hugging Face](https://huggingface.co/blog/deepseekv4)
- [DeepSeek vs GPT-5.5 pricing — South China Morning Post](https://www.scmp.com/tech/tech-trends/article/3351595/chinas-deepseek-prices-new-v4-ai-model-97-below-openais-gpt-55)
- [DeepSeek V4 vs GPT-5.5 — DataCamp](https://www.datacamp.com/blog/deepseek-v4-vs-gpt-5-5)
- [Kimi K2.6 OpenRouter](https://openrouter.ai/moonshotai/kimi-k2.6)
- [Kimi K2.6 review — ProgressiveRobot](https://www.progressiverobot.com/2026/04/21/kimi-k2-6/)
- [Kimi K2.6 stats — llm-stats.com](https://llm-stats.com/models/kimi-k2.6)
- [Kimi 2.6 benchmarks — BenchLM.ai](https://benchlm.ai/models/kimi-2-6)
- [GLM-5 stats — llm-stats.com](https://llm-stats.com/models/glm-5)
- [GLM-5 Hugging Face](https://huggingface.co/zai-org/GLM-5)
- [GLM-5.1 SWE-Bench Pro — Modemguides](https://www.modemguides.com/blogs/ai-news/glm-5-1-open-source-benchmarks-local-ai)
- [Zhipu GLM-5.1 vs Claude Opus 4.6 — DigitalApplied](https://www.digitalapplied.com/blog/zhipu-glm-5-1-coding-benchmark-claude-opus-comparison)
- [Qwen API Pricing 2026 — pricepertoken](https://pricepertoken.com/pricing-page/provider/qwen)
- [Qwen 3.5 397B-A17B — OpenRouter](https://openrouter.ai/qwen/qwen3.5-397b-a17b)
- [Qwen3 Embedding leaderboard — Qwen blog](https://qwenlm.github.io/blog/qwen3-embedding/)
- [Qwen3-Embedding GitHub](https://github.com/QwenLM/Qwen3-Embedding)
- [Embedding models benchmark 2026 — Cheney Zhang](https://zc277584121.github.io/rag/2026/03/20/embedding-models-benchmark-2026.html)
- [MiniMax M2.7 — Artificial Analysis](https://artificialanalysis.ai/models/minimax-m2-7)
- [MiniMax M2.7 review — ComputerTech](https://computertech.co/minimax-m2-7-review/)
- [MiniMax M2.7 — WaveSpeedAI](https://wavespeed.ai/blog/posts/minimax-m2-7-self-evolving-agent-model-features-benchmarks-2026/)
- [Best Chinese LLMs 2026 ranking — BenchLM.ai](https://benchlm.ai/blog/posts/best-chinese-llm)
- [Top 5 Chinese Open-Source LLMs — Second Talent](https://www.secondtalent.com/resources/chinese-open-source-llms-ai-leaders/)
- [Open-Source LLM Revolution 2026 — Alphamatch](https://www.alphamatch.ai/blog/open-source-llm-comparison-blog-2026)
- [Claude Opus 4.7 benchmarks — Vellum](https://www.vellum.ai/blog/claude-opus-4-7-benchmarks-explained)
- [Claude Opus 4.7 pricing — Finout](https://www.finout.io/blog/claude-opus-4.7-pricing-the-real-cost-story-behind-the-unchanged-price-tag)
- [Claude API pricing — BenchLM.ai](https://benchlm.ai/blog/posts/claude-api-pricing)
- [Claude Opus 4.7 vs Qwen 3.6 — Maxim](https://www.getmaxim.ai/articles/claude-opus-4-7-vs-qwen-3-6-closed-frontier-meets-open-weight-reasoning/)
- [Open-Weight vs Closed-Source Q2 2026 — DigitalApplied](https://www.digitalapplied.com/blog/open-weight-vs-closed-source-ai-models-q2-2026)
- [LLM API Pricing 2026 — TLDL](https://www.tldl.io/resources/llm-api-pricing-2026)
- [LLM Benchmarks 2026 — Iternal](https://iternal.ai/llm-selection-guide)
- [LLM Benchmark Scores 2026 — TokenCalculator](https://tokencalculator.com/llm-benchmarks)
