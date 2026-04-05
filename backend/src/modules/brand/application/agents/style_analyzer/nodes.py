import json
import re

from src.core.enums import ModelRole
from src.modules.brand.application.agents.style_analyzer.prompts import (
    ARCHITECT_PROMPT,
    JANITOR_PROMPT,
    PSYCHOLOGIST_PROMPT,
    SIMULATOR_PROMPT,
)
from src.modules.brand.application.agents.style_analyzer.state import OnboardingState
from src.shared.infrastructure.llm.factory import LLMFactory


def clean_text_regex(text: str) -> str:
    """
    Advanced Regex cleaning to save tokens before LLM.
    Removes common WhatsApp/Telegram export artifacts and noise.
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
        r"Messages and calls are end-to-end encrypted.*", "", text, flags=re.IGNORECASE
    )

    # 4. Remove URLs (Optional: sometimes style is in the link sharing, but usually noise for text style)
    text = re.sub(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        "[LINK]",
        text,
    )

    return text.strip()


def node_janitor(state: OnboardingState):
    """
    Step 1: Clean the raw input using Regex + Smart Sampling.
    Optimization: Avoids sending huge context to LLM if not necessary.
    """
    raw_input = state["raw_input"]

    # 1. Pre-cleaning (Regex)
    pre_cleaned = clean_text_regex(raw_input)

    # 2. Smart Sampling for Token Savings
    max_chars = 6000
    if len(pre_cleaned) > max_chars:
        # Take the last N chars as they represent the most current style
        sampled_text = "... " + pre_cleaned[-max_chars:]
    else:
        sampled_text = pre_cleaned

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
        print(f"Janitor Error: {e}")
        cleaned_text = sampled_text

    return {"cleaned_input": cleaned_text}


def node_psychologist(state: OnboardingState):
    """
    Step 2: Analyze the style using Metaprompting (Smart Model).
    """
    cleaned_input = state.get("cleaned_input", "")

    if not cleaned_input:
        return {"error": "No cleaned input available for analysis."}

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
        except json.JSONDecodeError as e:
            print(f"Psychologist JSON Parse Error. Raw output:\n{analysis_json}")
            raise e

        return {"style_profile": style_profile}

    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"Psychologist Error Type: {type(e)}")
        print(f"Psychologist Error: {e}")
        return {"error": f"Failed to analyze style: {e!s}"}


def node_architect(state: OnboardingState):
    """
    Step 3: Generate the System Instruction (Smart Model).
    """
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
        print(f"Architect Error: {e}")
        return {"error": f"Failed to generate instruction: {e!s}"}


def node_simulator(state: OnboardingState):
    """
    Step 4: Generate examples (Fast Model).
    """
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

        return {"simulation_examples": examples}

    except Exception as e:
        print(f"Simulator Error: {e}")
        return {"simulation_examples": []}
