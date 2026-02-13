import requests
import re
import colorsys
import urllib.parse
from collections import defaultdict
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.core.agents.web_extractor.state import WebExtractorState

# --- Brand Color Extractor Logic ---

class BrandColorExtractor:
    def __init__(self):
        self.hex_pattern = re.compile(r'#(?:[0-9a-fA-F]{3}){1,2}\b')
        self.property_weights = {
            'background-color': 3.0, 
            'background': 2.5,
            'fill': 2.0,             
            'color': 1.0,            
            'border': 0.5,
            'border-color': 0.5
        }
        self.selector_boosts = {
            'btn': 4.0, 'button': 4.0, 'cta': 5.0, 'primary': 5.0,
            'header': 3.0, 'nav': 3.0, 'logo': 4.0, 'menu': 2.0,
            'hero': 3.0, 'footer': 1.5, 'accent': 3.0
        }

    def _hex_to_hsl(self, hex_code: str) -> Tuple[float, float, float]:
        hex_code = hex_code.lstrip('#')
        if len(hex_code) == 3:
            hex_code = ''.join([c*2 for c in hex_code])
        try:
            r, g, b = int(hex_code[0:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16)
            return colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
        except (ValueError, IndexError):
            return (0, 0, 0)

    def _is_neutral(self, hsl: Tuple[float, float, float]) -> bool:
        h, lightness, s = hsl
        # Very dark (black) or very light (white)
        if lightness < 0.10 or lightness > 0.95: return True
        # Very desaturated (gray)
        if s < 0.10: return True
        return False

    def _analyze_css_text(self, css_text: str, score_dict: Dict[str, float], context_dict: Dict[str, List[str]], global_boost: float = 1.0, current_context: str = "css"):
        # Regex to capture property: value pairs containing hex codes
        rules = re.findall(r'([a-zA-Z-]+)\s*:[^;]*(#(?:[0-9a-fA-F]{3}){1,2})', css_text)
        
        for prop, color in rules:
            prop = prop.lower().strip()
            color = color.lower()
            # Normalize 3-digit hex to 6-digit
            if len(color) == 4:
                color = '#' + ''.join([c*2 for c in color[1:]])
            
            weight = self.property_weights.get(prop, 1.0)
            score_dict[color] += (weight * global_boost)
            
            # Track context if unique
            if color not in context_dict:
                context_dict[color] = []
            if len(context_dict[color]) < 5: # Limit context examples
                context_dict[color].append(f"{current_context} ({prop})")

    def extract_candidates(self, html_content: str, external_css_contents: List[str]) -> List[Tuple[str, float, List[str]]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        color_scores = defaultdict(float)
        color_contexts = {} # color -> list of contexts

        # 1. Analyze <style> blocks
        for style in soup.find_all('style'):
            if style.string:
                self._analyze_css_text(style.string, color_scores, color_contexts, current_context="internal <style>")

        # 2. Analyze inline styles
        for tag in soup.find_all(attrs={"style": True}):
            style_attr = tag['style']
            context_boost = 1.0
            element_meta = f"{tag.name}.{'.'.join(tag.get('class', []))}" if tag.get('class') else tag.name
            
            # Apply boost based on class/id names
            full_meta = f"{tag.get('id', '')} {str(tag.get('class', ''))}".lower()
            for keyword, boost in self.selector_boosts.items():
                if keyword in full_meta:
                    context_boost = max(context_boost, boost)
            
            self._analyze_css_text(style_attr, color_scores, color_contexts, context_boost, current_context=f"inline {element_meta}")

        # 3. Analyze External CSS
        for i, css_content in enumerate(external_css_contents):
            # We can't know selectors easily without parsing CSS structure properly (too heavy for regex), 
            # so we treat it as generic but prioritize background-color
            self._analyze_css_text(css_content, color_scores, color_contexts, global_boost=1.0, current_context=f"external_css_{i}")

        # 4. Filter and Rank
        ranked_colors = []
        for color, score in color_scores.items():
            hsl = self._hex_to_hsl(color)
            
            # Heuristic: Penalize neutrals for the "primary" ranking, but keep them for palette analysis
            neutral_penalty = 1.0
            if self._is_neutral(hsl):
                neutral_penalty = 0.05 
            
            # Heuristic: Boost vibrant colors
            vibrancy_boost = 1.0
            if hsl[2] > 0.4: # Saturation > 40%
                vibrancy_boost = 1.5

            final_score = score * neutral_penalty * vibrancy_boost
            contexts = color_contexts.get(color, [])
            ranked_colors.append((color, final_score, contexts))

        ranked_colors.sort(key=lambda x: x[1], reverse=True)
        return ranked_colors[:15] # Return top 15 candidates to capture neutrals too

# --- LangGraph Nodes ---

def fetch_html(state: WebExtractorState) -> Dict[str, Any]:
    """
    Fetches HTML + External CSS, extracts color candidates, and cleans text.
    """
    url = state["url"]
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AIResearchBot/1.0; +http://visionarias.ai)"}
    
    try:
        # 1. Fetch Main HTML
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html_content = response.text
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 2. Fetch External CSS (Top 3 non-generic)
        css_links = []
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if href:
                # Resolve relative URLs
                full_url = urllib.parse.urljoin(url, href)
                # Skip common generic libraries to save time/noise
                if not any(x in full_url for x in ["bootstrap", "font-awesome", "swiper", "animate"]):
                    css_links.append(full_url)
        
        external_css_contents = []
        # Limit to top 3 CSS files to avoid timeouts
        for css_url in css_links[:3]:
            try:
                css_res = requests.get(css_url, headers=headers, timeout=5)
                if css_res.status_code == 200:
                    external_css_contents.append(css_res.text)
            except Exception:
                continue # Skip if fail
                
        # 3. Run Intelligent Color Extraction
        extractor = BrandColorExtractor()
        candidates = extractor.extract_candidates(html_content, external_css_contents)
        
        # Format candidates for LLM with Context
        candidates_str = "\n".join([f"{c[0]} (Score: {c[1]:.1f}) - Found in: {', '.join(c[2])}" for c in candidates])
        
        # 4. Clean HTML for Text Content
        for script in soup(["script", "style", "nav", "footer", "svg", "path"]):
            script.decompose()
        
        text = soup.get_text(separator="\n")
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        final_context = clean_text[:20000]
        if candidates:
            final_context += f"\n\n[SYSTEM DETECTED VISUAL ASSETS]:\n{candidates_str}"
        
        return {"raw_content": final_context, "error": None}
        
    except Exception as e:
        return {"error": f"Failed to fetch {url}: {str(e)}", "raw_content": None}

def extract_structured(state: WebExtractorState) -> Dict[str, Any]:
    """
    Extracts structured data using LLM and the provided schema.
    """
    if state.get("error"):
        return {}
        
    content = state.get("raw_content", "")
    schema = state.get("target_schema")
    
    if not content or not schema:
        return {"error": "Missing content or schema for extraction"}
        
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(schema)
    
    try:
        messages = [
            SystemMessage(content="You are an expert UI/UX Designer and Brand Strategist. Your goal is to reverse-engineer a Design System from the provided website content.\n\nCRITICAL FOR COLOR EXTRACTION:\n- Analyze the '[SYSTEM DETECTED VISUAL ASSETS]' section.\n- It lists colors sorted by importance and WHERE they were found (e.g., 'btn', 'nav', 'footer').\n- Use this context to determine the Extended Palette: Backgrounds, Text Colors, and Usage Guidelines.\n- 'primary_color': High score, found in buttons/headers, non-neutral.\n- 'background_color': Found in body/sections, usually light/neutral.\n- 'text_primary_color': Found in text/paragraphs, usually dark/neutral.\n- 'design_style': Infer from the color choices (e.g., High contrast = Bold; Pastels = Soft; Dark backgrounds = Modern/Tech).\n- 'usage_guidelines': Generate actionable rules like 'Use primary color for CTA buttons', 'Use dark background for footer'."),
            HumanMessage(content=f"Text to extract from:\n\n{content}")
        ]
        result = structured_llm.invoke(messages)
        return {"extracted_data": result}
    except Exception as e:
        return {"error": f"Extraction failed: {str(e)}"}
