import re
import json
from src.core.enums import ModelRole
from src.modules.copilot.application.agents.style_analyzer.state import OnboardingState
from src.modules.copilot.application.agents.style_analyzer.prompts import JANITOR_PROMPT, PSYCHOLOGIST_PROMPT, ARCHITECT_PROMPT, SIMULATOR_PROMPT
from src.shared.infrastructure.llm.factory import LLMFactory
from src.modules.sales_agent.infrastructure.monitoring.tracing import trace_node

def clean_text_regex(text: str) -> str:
    """
    Advanced Regex cleaning to save tokens before LLM.
    Removes common WhatsApp/Telegram export artifacts and noise.
    """
    # 1. Remove timestamps (e.g., [10/12/24, 15:30:22], 12/10/2024 10:30 a. m.)
    text = re.sub(r'\[?\d{1,2}[/-]\d{1,2}[/-]\d{2,4},? \d{1,2}:\d{2}(:\d{2})?( [AP]M|[ap]\.?\s?m\.?)?\]?', '', text)
    text = re.sub(r'\d{1,2}:\d{2}( [AP]M)? - ', '', text) # Short format "10:30 AM - "
    
    # 2. Remove " - Name:" prefix pattern often found in exports
    text = re.sub(r' - .*?: ', ': ', text)
    
    # 3. Remove "Media omitted" / System messages
    text = re.sub(r'<Media omitted>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'image omitted', '', text, flags=re.IGNORECASE)
    text = re.sub(r'audio omitted', '', text, flags=re.IGNORECASE)
    text = re.sub(r'sticker omitted', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Messages and calls are end-to-end encrypted.*', '', text, flags=re.IGNORECASE)
    
    # 4. Remove URLs (Optional: sometimes style is in the link sharing, but usually noise for text style)
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[LINK]', text)

    return text.strip()

@trace_node("janitor")
def node_janitor(state: OnboardingState):
    """
    Step 1: Clean the raw input using Regex + Smart Sampling.
    Optimization: Avoids sending huge context to LLM if not necessary.
    """
    raw_input = state["raw_input"]
    
    # 1. Pre-cleaning (Regex)
    pre_cleaned = clean_text_regex(raw_input)
    
    # 2. Smart Sampling for Token Savings
    # We don't need 100k tokens to analyze style. 4000-6000 chars is usually enough for a strong pattern.
    # We take a slice from the middle-end (usually more representative than the very beginning)
    max_chars = 6000
    if len(pre_cleaned) > max_chars:
        # Take the last N chars as they represent the most current style
        sampled_text = "... " + pre_cleaned[-max_chars:]
    else:
        sampled_text = pre_cleaned

    # 3. LLM Cleaning (Semantic Filtering) - Optional
    # We use the sampled text to save tokens.
    try:
        cleaned_text = LLMFactory.get_service().generate_response(
            messages=[{"role": "user", "content": sampled_text}],
            system_prompt=JANITOR_PROMPT.format(raw_input=sampled_text), 
            model_type=ModelRole.FAST,
            temperature=0.0, # Deterministic
            max_output_tokens=2000
        )
    except Exception as e:
        print(f"Janitor Error: {e}")
        # Fallback to regex output
        cleaned_text = sampled_text
        
    return {"cleaned_input": cleaned_text}

@trace_node("psychologist")
def node_psychologist(state: OnboardingState):
    """
    Step 2: Analyze the style using Metaprompting (Smart Model).
    """
    cleaned_input = state.get("cleaned_input", "")
    
    if not cleaned_input:
        return {"error": "No cleaned input available for analysis."}
        
    try:
        # Use "smart" model (GPT-4o) for deep analysis
        analysis_json = LLMFactory.get_service().generate_response(
            messages=[{"role": "user", "content": cleaned_input}],
            system_prompt=PSYCHOLOGIST_PROMPT.format(cleaned_input=cleaned_input),
            model_type=ModelRole.REASONING,
            temperature=0.2,
            max_output_tokens=1000
        )
        
        # Parse JSON
        # Clean markdown if present
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
        return {"error": f"Failed to analyze style: {str(e)}"}

@trace_node("architect")
def node_architect(state: OnboardingState):
    """
    Step 3: Generate the System Instruction (Smart Model).
    """
    style_profile = state.get("style_profile")
    
    if not style_profile:
        return {"error": "No style profile available."}
        
    try:
        # Format profile as string for the prompt
        profile_str = json.dumps(style_profile, indent=2, ensure_ascii=False)
        
        instruction = LLMFactory.get_service().generate_response(
            messages=[],
            system_prompt=ARCHITECT_PROMPT.format(style_profile=profile_str),
            model_type=ModelRole.REASONING,
            temperature=0.7, # Slightly creative for better writing
            max_output_tokens=1000
        )
        
        return {"system_instruction": instruction.strip()}
        
    except Exception as e:
        print(f"Architect Error: {e}")
        return {"error": f"Failed to generate instruction: {str(e)}"}

@trace_node("simulator")
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
            max_output_tokens=800
        )
        
        # Parse JSON List
        json_str = examples_json.replace("```json", "").replace("```", "").strip()
        examples = json.loads(json_str)
        
        return {"simulation_examples": examples}
        
    except Exception as e:
        print(f"Simulator Error: {e}")
        # Return empty list rather than fail
        return {"simulation_examples": []}
