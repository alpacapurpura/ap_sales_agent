"""Style analyzer agent node functions."""

import json
import re

import structlog
from luana_core_brand_studio.application.agents.style_analyzer.prompts import (
    ARCHITECT_PROMPT,
    JANITOR_PROMPT,
    PERSONALITY_PSYCHOLOGIST_PROMPT,
    PSYCHOLOGIST_PROMPT,
    SIMULATOR_PROMPT,
)
from luana_core_brand_studio.application.agents.style_analyzer.state import OnboardingState
from luana_core_llm.factory import LLMFactory
from luana_core_platform.core.enums import ModelRole

logger = structlog.get_logger()


def clean_text_regex(text: str) -> str:
    """Clean text with advanced regex to save tokens before LLM.

    Remove common WhatsApp/Telegram export artifacts and noise.
    """
    # 1. Remove timestamps (e.g., [10/12/24, 15:30:22], 12/10/2024 10:30 a. m.)
    text = re.sub(
        r"\[?\d{1,2}[/-]\d{1,2}[/-]\d{2,4},? \d{1,2}:\d{2}(:\d{2})?( [AP]M|[ap]\.?\s?m\.?)?\]?",
        "",
        text,
    )
    text = re.sub(r"\d{1,2}:\d{2}( [AP]M)? - ", "", text)  # Short format "10:30 AM - "

    # 2. Remove " - Name:" prefix pattern often found in exports
    text = re.sub(r" - .*?: ", ": ", text)

    # 3. Remove "Media omitted" / System messages
    text = re.sub(r"<Media omitted>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"image omitted", "", text, flags=re.IGNORECASE)
    text = re.sub(r"audio omitted", "", text, flags=re.IGNORECASE)
    text = re.sub(r"sticker omitted", "", text, flags=re.IGNORECASE)
    text = re.sub(
        r"Messages and calls are end-to-end encrypted.*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # 4. Remove URLs (Optional: sometimes style is in the link sharing, but usually noise for text style)
    text = re.sub(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        "[LINK]",
        text,
    )

    return text.strip()


_JANITOR_MAX_CHARS = 6000

# B3: Stratified sampling buckets — when raw material exceeds the LLM budget,
# we sample EVENLY across these contexts so the psychologist node sees the
# full conversational range (greetings + objections + closes), not just the
# last-N chars (which biased the LLM toward whatever happened most recently).
_JANITOR_CONTEXT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "greeting": ("hola", "buenas", "buen día", "qué tal", "saludos", "hey"),
    "price": ("cuánto", "precio", "costo", "vale", "cuesta", "tarifa", "$"),
    "objection": (
        "caro",
        "no puedo",
        "no tengo",
        "lo pienso",
        "lo voy a pensar",
        "más adelante",
        "no es para mí",
        "no estoy seguro",
        "no sé",
        "duda",
        "complicado",
    ),
    "closing": (
        "quiero entrar",
        "lo tomo",
        "vamos",
        "dale",
        "perfecto",
        "comprar",
        "pagar",
        "link",
        "agendar",
        "agenda",
    ),
    "follow_up": (
        "sigues",
        "cómo vas",
        "te quedaste",
        "retomamos",
        "recordatorio",
        "vuelvo a escribir",
    ),
    "neutral": (),  # catches everything that didn't match the above
}


def _stratified_sample(text: str, max_chars: int) -> str:
    """Build a context-balanced sample fitting within ``max_chars``.

    Splits ``text`` into lines, buckets each by keyword match, then takes a
    proportional slice from each bucket so all contexts are represented even
    when the raw input is much longer than the LLM budget. Falls back to
    last-N chars if bucketing produces nothing useful.
    """
    if len(text) <= max_chars:
        return text

    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return text[-max_chars:]

    buckets: dict[str, list[str]] = {ctx: [] for ctx in _JANITOR_CONTEXT_KEYWORDS}
    for ln in lines:
        lower = ln.lower()
        matched = False
        for ctx, kws in _JANITOR_CONTEXT_KEYWORDS.items():
            if ctx == "neutral":
                continue
            if any(kw in lower for kw in kws):
                buckets[ctx].append(ln)
                matched = True
                break
        if not matched:
            buckets["neutral"].append(ln)

    non_empty = [ctx for ctx, items in buckets.items() if items]
    if not non_empty:
        return text[-max_chars:]

    per_bucket = max_chars // len(non_empty)
    parts: list[str] = []
    for ctx in non_empty:
        joined = "\n".join(buckets[ctx])
        parts.append(f"[{ctx}]\n{joined[:per_bucket]}")
    sample = "\n\n".join(parts)
    return sample[:max_chars]


def node_janitor(state: OnboardingState) -> dict[str, str]:
    """Clean the raw input using regex + stratified sampling.

    B3: replaces "last 6000 chars" sampling with context-balanced sampling so
    the psychologist node sees greetings + objections + closes proportionally,
    even when the export is much larger than the LLM budget.
    """
    raw_input = state["raw_input"]

    # 1. Pre-cleaning (Regex)
    pre_cleaned = clean_text_regex(raw_input)

    # 2. Stratified sampling for token savings + context coverage (B3)
    sampled_text = _stratified_sample(pre_cleaned, _JANITOR_MAX_CHARS)

    # 3. LLM Cleaning (Semantic Filtering)
    try:
        cleaned_text = LLMFactory.get_service().generate_response(
            messages=[{"role": "user", "content": sampled_text}],
            system_prompt=JANITOR_PROMPT.format(raw_input=sampled_text),
            model_type=ModelRole.FAST,
            temperature=0.0,
            max_output_tokens=2000,
        )
    except Exception as e:
        logger.exception("janitor_llm_cleaning_failed", error=str(e))
        cleaned_text = sampled_text

    return {"cleaned_input": cleaned_text}


def node_psychologist(state: OnboardingState) -> dict[str, str | dict[str, str]]:
    """Step 2: Analyze the style using Metaprompting (Smart Model).

    If the state contains ``parsed_messages`` (6-node pipeline), uses the new
    PERSONALITY_PSYCHOLOGIST_PROMPT and populates the ``personality_*`` fields.
    Otherwise falls back to the legacy PSYCHOLOGIST_PROMPT + ``style_profile``.
    """
    cleaned_input = state.get("cleaned_input", "")

    if not cleaned_input:
        return {"error": "No cleaned input available for analysis."}

    # ---------------------------------------------------------------
    # 6-node path: parsed_messages present → extract personality profile
    # ---------------------------------------------------------------
    if state.get("parsed_messages"):
        try:
            analysis_json = LLMFactory.get_service().generate_response(
                messages=[{"role": "user", "content": cleaned_input}],
                system_prompt=PERSONALITY_PSYCHOLOGIST_PROMPT.format(cleaned_input=cleaned_input),
                model_type=ModelRole.REASONING,
                temperature=0.2,
                max_output_tokens=2000,
            )

            json_str = analysis_json.replace("```json", "").replace("```", "").strip()
            try:
                profile_data = json.loads(json_str)
            except json.JSONDecodeError:
                logger.exception("personality_psychologist_json_parse_error", raw_output=analysis_json)
                raise

        except Exception as e:
            logger.exception(
                "personality_psychologist_failed",
                error_type=type(e).__name__,
                error=str(e),
            )
            return {"error": f"Failed to extract personality profile: {e!s}"}

        return {
            "personality_dimensions": profile_data.get("dimensions", {}),
            "personality_linguistic_patterns": profile_data.get("linguistic_patterns", {}),
            "personality_sample_exchanges": profile_data.get("sample_exchanges", []),
            "personality_confidence": float(profile_data.get("confidence", 0.0)),
        }

    # ---------------------------------------------------------------
    # Legacy 4-node path: use old PSYCHOLOGIST_PROMPT → style_profile
    # ---------------------------------------------------------------
    try:
        analysis_json = LLMFactory.get_service().generate_response(
            messages=[{"role": "user", "content": cleaned_input}],
            system_prompt=PSYCHOLOGIST_PROMPT.format(cleaned_input=cleaned_input),
            model_type=ModelRole.REASONING,
            temperature=0.2,
            max_output_tokens=1000,
        )

        json_str = analysis_json.replace("```json", "").replace("```", "").strip()
        try:
            style_profile = json.loads(json_str)
        except json.JSONDecodeError:
            logger.exception("psychologist_json_parse_error", raw_output=analysis_json)
            raise

    except Exception as e:
        logger.exception(
            "psychologist_analysis_failed",
            error_type=type(e).__name__,
            error=str(e),
        )
        return {"error": f"Failed to analyze style: {e!s}"}

    else:
        return {"style_profile": style_profile}


def node_architect(state: OnboardingState) -> dict[str, str]:
    """Step 3: Generate the System Instruction (Smart Model).

    If the state contains ``personality_dimensions`` (6-node pipeline), uses
    PersonalityCompiler to build the 5-block instruction deterministically.
    Otherwise falls back to the legacy LLM-based ARCHITECT_PROMPT approach.
    """
    # ---------------------------------------------------------------
    # 6-node path: personality_dimensions present → use PersonalityCompiler
    # ---------------------------------------------------------------
    if state.get("personality_dimensions"):
        try:
            from luana_core_brand_studio.domain.personality import (
                LinguisticPatterns,
                PersonalityCompiler,
                PersonalityDimensions,
                SampleExchange,
            )

            dims_data = state["personality_dimensions"]
            patterns_data = state.get("personality_linguistic_patterns", {})
            exchanges_data = state.get("personality_sample_exchanges", [])

            # Build value objects — use sensible defaults for missing patterns fields
            dims = PersonalityDimensions(
                energy=float(dims_data.get("energy", 0.5)),
                warmth=float(dims_data.get("warmth", 0.5)),
                humor=float(dims_data.get("humor", 0.5)),
                expressiveness=float(dims_data.get("expressiveness", 0.5)),
                narrative=float(dims_data.get("narrative", 0.5)),
                verbosity=float(dims_data.get("verbosity", 0.5)),
            )
            patterns = LinguisticPatterns(
                emoji_style=patterns_data.get("emoji_style", "moderate"),
                favorite_emojis=patterns_data.get("favorite_emojis", []),
                greeting=patterns_data.get("greeting", "Hola"),
                farewell=patterns_data.get("farewell", "Hasta pronto"),
                filler_phrases=patterns_data.get("filler_phrases", []),
                avg_message_length=patterns_data.get("avg_message_length", "medium"),
                punctuation_style=patterns_data.get("punctuation_style", "standard"),
                humor_type=patterns_data.get("humor_type", "none"),
                unique_vocabulary=patterns_data.get("unique_vocabulary", []),
            )
            exchanges = [SampleExchange(**e) for e in exchanges_data]

            instruction = PersonalityCompiler.compile(dims, patterns, exchanges)
            return {"system_instruction": instruction}

        except Exception as e:
            logger.exception("architect_personality_compile_failed", error=str(e))
            return {"error": f"Failed to compile personality instruction: {e!s}"}

    # ---------------------------------------------------------------
    # Legacy 4-node path: LLM-based architect
    # ---------------------------------------------------------------
    style_profile = state.get("style_profile")

    if not style_profile:
        return {"error": "No style profile available."}

    try:
        profile_str = json.dumps(style_profile, indent=2, ensure_ascii=False)

        instruction = LLMFactory.get_service().generate_response(
            messages=[],
            system_prompt=ARCHITECT_PROMPT.format(style_profile=profile_str),
            model_type=ModelRole.REASONING,
            temperature=0.7,
            max_output_tokens=1000,
        )

        return {"system_instruction": instruction.strip()}

    except Exception as e:
        logger.exception("architect_instruction_generation_failed", error=str(e))
        return {"error": f"Failed to generate instruction: {e!s}"}


def node_simulator(state: OnboardingState) -> dict[str, list[str]]:
    """Step 4: Generate examples (Fast Model)."""
    instruction = state.get("system_instruction")

    if not instruction:
        return {"error": "No system instruction available."}

    try:
        examples_json = LLMFactory.get_service().generate_response(
            messages=[],
            system_prompt=SIMULATOR_PROMPT.format(system_instruction=instruction),
            model_type=ModelRole.FAST,
            temperature=0.7,
            max_output_tokens=800,
        )

        json_str = examples_json.replace("```json", "").replace("```", "").strip()
        examples = json.loads(json_str)

    except Exception as e:
        logger.exception("simulator_example_generation_failed", error=str(e))
        return {"simulation_examples": []}
    else:
        return {"simulation_examples": examples}


# ---------------------------------------------------------------------------
# NEW NODES — Personality Engine (6-node pipeline)
# ---------------------------------------------------------------------------


def node_parser(state: OnboardingState) -> dict:
    """Node 0 (6-node pipeline): Parse raw chat export into structured messages.

    Uses the auto-detecting ``detect_and_parse`` function from the parsers module.
    Handles WhatsApp .txt, Instagram DM JSON, and Telegram JSON formats.

    On success: sets ``parsed_messages`` (list[dict]) and ``cleaned_input``
    (plain-text join of message texts, for the downstream janitor/psychologist).

    On parse failure: falls back to treating raw_input as plain text so the
    pipeline can degrade gracefully.
    """
    raw_input = state.get("raw_input", "")

    try:
        from luana_core_brand_studio.infrastructure.parsers.base import detect_and_parse

        messages = detect_and_parse(raw_input)
        parsed_dicts = [
            {
                "text": m.text,
                "sender": m.sender,
                "has_emoji": m.has_emoji,
                "word_count": m.word_count,
            }
            for m in messages
        ]
        # Join parsed texts for downstream nodes that expect plain cleaned_input
        cleaned_text = "\n".join(m.text for m in messages if m.text.strip())

        logger.info(
            "node_parser.success",
            message_count=len(messages),
            cleaned_chars=len(cleaned_text),
        )
        return {
            "parsed_messages": parsed_dicts,
            "cleaned_input": cleaned_text,
        }

    except ValueError as e:
        # Unsupported format — fall back to raw text so the pipeline continues
        logger.warning("node_parser.unsupported_format", error=str(e))
        return {
            "parsed_messages": [],
            "cleaned_input": raw_input,
        }
    except Exception as e:
        logger.exception("node_parser.failed", error=str(e))
        return {
            "parsed_messages": [],
            "cleaned_input": raw_input,
        }


async def node_embedder(state: OnboardingState) -> dict:
    """Node 5 (6-node pipeline): Embed sample_exchanges as Qdrant style anchors.

    Requires that ``state`` contains a ``_style_store`` key with a
    ``StyleAnchorStore`` instance, ``personality_profile_id``, and
    ``personality_sample_exchanges``.  If Qdrant is unavailable or not wired,
    this node degrades gracefully: sets ``anchor_count=0`` and logs a warning.

    Note: In production the style_store is injected by the graph orchestrator
    (e.g. via state initialisation or dependency injection). In tests and the
    legacy flow where Qdrant is not configured, the node is a no-op.
    """
    style_store = state.get("_style_store")  # type: ignore[misc]  # _style_store is an injected infra dependency, intentionally absent from OnboardingState TypedDict
    profile_id_str = state.get("personality_profile_id")
    exchanges = state.get("personality_sample_exchanges", [])
    user_id = state.get("user_id", "")

    if not style_store or not profile_id_str or not exchanges:
        logger.warning(
            "node_embedder.skipped",
            has_store=bool(style_store),
            has_profile_id=bool(profile_id_str),
            exchange_count=len(exchanges),
        )
        return {"anchor_count": 0}

    try:
        import uuid as _uuid

        tenant_id = _uuid.UUID(user_id) if user_id else _uuid.uuid4()
        profile_id = _uuid.UUID(profile_id_str)

        count = await style_store.upsert_anchors(tenant_id, profile_id, exchanges)
        logger.info("node_embedder.success", anchor_count=count, profile_id=profile_id_str)
        return {"anchor_count": count}

    except Exception as e:  # noqa: BLE001 — graceful degradation: Qdrant unavailability must not break pipeline
        logger.warning("node_embedder.qdrant_unavailable", error=str(e))
        return {"anchor_count": 0}
