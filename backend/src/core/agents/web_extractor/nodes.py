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
        self.css_variables = {}

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
        # 1. Existing hex extraction (Enhanced regex for numbers in properties)
        rules = re.findall(r'([a-zA-Z0-9-]+)\s*:[^;]*(#(?:[0-9a-fA-F]{3}){1,2})', css_text)
        
        for prop, color in rules:
            prop = prop.lower().strip()
            color = color.lower()
            # Normalize 3-digit hex to 6-digit
            if len(color) == 4:
                color = '#' + ''.join([c*2 for c in color[1:]])
            
            # Boost variable definitions significantly
            weight = self.property_weights.get(prop, 1.0)
            if prop.startswith('--'):
                weight = 3.0 # Treat variable definition as important as background

            score_dict[color] += (weight * global_boost)
            
            # Track context if unique
            if color not in context_dict:
                context_dict[color] = []
            if len(context_dict[color]) < 5: # Limit context examples
                context_dict[color].append(f"{current_context} ({prop})")

        # 2. Variable Usage Resolution: property: var(--name)
        # Capture: property: ... var(--name) ...
        # Simplified regex to catch most common usages
        var_usages = re.findall(r'([a-zA-Z0-9-]+)\s*:[^;]*var\((--[a-zA-Z0-9-]+)\)', css_text)
        
        for prop, var_name in var_usages:
            prop = prop.lower().strip()
            if var_name in self.css_variables:
                color = self.css_variables[var_name]
                weight = self.property_weights.get(prop, 1.0)
                # Apply the boost to the RESOLVED color
                score_dict[color] += (weight * global_boost)
                
                if color not in context_dict:
                    context_dict[color] = []
                if len(context_dict[color]) < 5:
                    context_dict[color].append(f"{current_context} ({prop}->{var_name})")

    def extract_candidates(self, html_content: str, external_css_contents: List[str]) -> List[Tuple[str, float, List[str]]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        color_scores = defaultdict(float)
        color_contexts = {} # color -> list of contexts
        self.css_variables = {}

        # 1. First pass: Collect variables from all sources
        all_css_sources = []
        for style in soup.find_all('style'):
            if style.string: all_css_sources.append(style.string)
        for i, css in enumerate(external_css_contents):
            all_css_sources.append(css)
        
        # Simple regex to capture variable definitions: --name: #hex
        # This ignores scope, assuming global uniqueness which is common enough
        for css in all_css_sources:
            var_defs = re.findall(r'(--[a-zA-Z0-9-]+)\s*:\s*(#(?:[0-9a-fA-F]{3}){1,2})', css)
            for name, color in var_defs:
                if len(color) == 4:
                    color = '#' + ''.join([c*2 for c in color[1:]])
                self.css_variables[name] = color.lower()

        # 2. Analyze <style> blocks
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

class BrandFontExtractor:
    def __init__(self):
        self.font_weights = {
            'font-family': 1.0,
        }
        self.system_fonts = {
            'sans-serif', 'serif', 'monospace', 'inherit', 'initial', 'arial', 'helvetica', 'times new roman', 'inter'
        }
        self.css_variables = {}

    def _extract_variables(self, css_text):
        vars = re.findall(r'(--[a-zA-Z0-9-]+)\s*:\s*([^;]+)', css_text)
        for name, value in vars:
            self.css_variables[name] = value.strip()

    def _resolve_var(self, value):
        if 'var(' not in value:
            return value
        
        match = re.search(r'var\((--[a-zA-Z0-9-]+)\)', value)
        if match:
            var_name = match.group(1)
            if var_name in self.css_variables:
                resolved = self.css_variables[var_name]
                return self._resolve_var(resolved)
        return value

    def extract_fonts(self, html_content: str, external_css_contents: list) -> List[Tuple[str, float, List[str]]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        font_scores = defaultdict(float)
        font_contexts = defaultdict(list)
        
        # 0. Extract Variables
        all_css_sources = []
        for style in soup.find_all('style'):
            if style.string: all_css_sources.append(style.string)
        all_css_sources.extend(external_css_contents)
        
        for css in all_css_sources:
            self._extract_variables(css)

        # 1. Google Fonts Extraction
        google_fonts = []
        for link in soup.find_all("link", href=True):
            href = link['href']
            if "fonts.googleapis.com" in href:
                matches = re.findall(r'family=([^:&]+)', href)
                for match in matches:
                    font_name = match.replace('+', ' ')
                    google_fonts.append(font_name)
                    font_scores[font_name] += 10.0
                    font_contexts[font_name].append("Google Fonts Import")

        # 2. CSS Analysis
        for css_text in all_css_sources:
             rules = re.findall(r'font-family\s*:\s*([^;}]+)', css_text, re.IGNORECASE)
             for rule in rules:
                rule = rule.strip()
                resolved_rule = self._resolve_var(rule)
                
                fonts = [f.strip().strip('"\'') for f in resolved_rule.split(',')]
                if not fonts: continue
                
                primary_font = fonts[0]
                primary_font = re.sub(r'\s+', ' ', primary_font).strip()
                
                if primary_font.lower() not in self.system_fonts and len(primary_font) > 2:
                    font_scores[primary_font] += 1.0
                    if len(font_contexts[primary_font]) < 3:
                        font_contexts[primary_font].append(f"CSS Rule ({rule})")

        # Rank
        ranked_fonts = []
        for font, score in font_scores.items():
            if font in google_fonts: score *= 2.0
            ranked_fonts.append((font, score, font_contexts[font]))

        ranked_fonts.sort(key=lambda x: x[1], reverse=True)
        return ranked_fonts[:5]

# --- Helper Functions ---

def extract_internal_links(base_url: str, current_url: str, html: str, max_links: int = 5) -> List[str]:
    """
    Extracts internal links from HTML, prioritizing relevant pages.
    """
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    base_domain = urllib.parse.urlparse(base_url).netloc
    
    # Keywords to prioritize for brand/strategy/team
    priority_keywords = ["about", "team", "mission", "vision", "strategy", "services", "product", "story", "history", "founders", "nosotros", "equipo", "historia"]
    
    found_links = []
    
    for a in soup.find_all("a", href=True):
        href = a['href']
        # Normalize
        full_url = urllib.parse.urljoin(current_url, href)
        parsed = urllib.parse.urlparse(full_url)
        
        # Check domain (internal only)
        if parsed.netloc != base_domain:
            continue
            
        # Skip files, anchors, etc.
        if any(full_url.endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.css', '.js', '.zip']):
            continue
        if '#' in href and len(href) > 1 and href.startswith('#'): # Skip pure anchors
            continue
            
        # Score relevance
        score = 0
        path = parsed.path.lower()
        for kw in priority_keywords:
            if kw in path:
                score += 10 # High boost for keywords
        
        # Avoid duplicate URLs
        if full_url not in links:
            found_links.append((score, full_url))
            links.add(full_url)
            
    # Sort by score descending
    found_links.sort(key=lambda x: x[1], reverse=True)
    
    # Return top N
    return [x[1] for x in found_links[:max_links]]

# --- LangGraph Nodes ---

def fetch_html(state: WebExtractorState) -> Dict[str, Any]:
    """
    Fetches HTML + External CSS, extracts color candidates, and cleans text.
    Handles Deep Crawling (multi-step).
    """
    # Initialize aggregated_content if not present
    aggregated_content = state.get("aggregated_content", [])
    
    # Get URL to process
    url = state.get("current_url")
    if not url:
        url = state.get("base_url")
    
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AIResearchBot/1.0; +http://visionarias.ai)"}
    
    print(f"Crawling: {url} (Depth: {state.get('depth', 0)})")
    
    try:
        # 1. Fetch Main HTML
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html_content = response.text
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        # --- Visual Extraction (Only on Root/Depth 0) ---
        candidates_str = ""
        font_candidates_str = ""
        
        if state.get("depth", 0) == 0:
            # 2. Fetch External CSS (Top 3 non-generic)
            css_links = []
            for link in soup.find_all("link", rel="stylesheet"):
                href = link.get("href")
                if href:
                    full_url = urllib.parse.urljoin(url, href)
                    if not any(x in full_url for x in ["bootstrap", "font-awesome", "swiper", "animate"]):
                        css_links.append(full_url)
            
            external_css_contents = []
            for css_url in css_links[:3]:
                try:
                    css_res = requests.get(css_url, headers=headers, timeout=5)
                    if css_res.status_code == 200:
                        external_css_contents.append(css_res.text)
                except Exception:
                    continue 
                    
            # 3. Run Intelligent Color Extraction
            extractor = BrandColorExtractor()
            candidates = extractor.extract_candidates(html_content, external_css_contents)
            
            # 3.1 Run Font Extraction
            font_extractor = BrandFontExtractor()
            font_candidates = font_extractor.extract_fonts(html_content, external_css_contents)
            
            candidates_str = "\n".join([f"{c[0]} (Score: {c[1]:.1f}) - Found in: {', '.join(c[2])}" for c in candidates])
            font_candidates_str = "\n".join([f"{f[0]} (Score: {f[1]:.1f}) - Found in: {', '.join(f[2])}" for f in font_candidates])

        # 4. Clean HTML for Text Content
        for script in soup(["script", "style", "nav", "footer", "svg", "path", "iframe", "noscript"]):
            script.decompose()
        
        text = soup.get_text(separator="\n")
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Format Content Chunk
        page_content = f"\n\n=== CONTENT FROM URL: {url} ===\n{clean_text[:15000]}"
        
        if state.get("depth", 0) == 0:
            if candidates_str:
                page_content += f"\n\n[SYSTEM DETECTED VISUAL ASSETS]:\n{candidates_str}"
            if font_candidates_str:
                 page_content += f"\n\n[SYSTEM DETECTED FONT ASSETS]:\n{font_candidates_str}"
        
        aggregated_content.append(page_content)
        
        # --- Link Discovery (if depth < max_depth) ---
        queue = state.get("queue", [])
        visited = state.get("visited", [])
        
        # Mark current as visited if not already (it should be)
        if url not in visited:
            visited.append(url)
        
        if state.get("depth", 0) < state.get("max_depth", 0):
            new_links = extract_internal_links(state["base_url"], url, html_content)
            for link in new_links:
                if link not in visited and link not in queue:
                    queue.append(link)
        
        return {
            "aggregated_content": aggregated_content,
            "queue": queue,
            "visited": visited,
            "error": None
        }
        
    except Exception as e:
        print(f"Failed to fetch {url}: {str(e)}")
        # If root fails, it's a critical error
        if url == state["base_url"]:
            return {"error": f"Failed to fetch {url}: {str(e)}", "aggregated_content": []}
        return {"error": None} # Ignore sub-page error

def extract_structured(state: WebExtractorState) -> Dict[str, Any]:
    """
    Extracts structured data using LLM and the provided schema.
    Uses aggregated content from all visited pages.
    """
    if state.get("error"):
        return {}
        
    aggregated_content = state.get("aggregated_content", [])
    if not aggregated_content:
        return {"error": "Missing content for extraction"}
    
    # Combine content
    full_content = "\n".join(aggregated_content)
    
    # Check for crawl_only mode
    if state.get("mode") == "crawl_only":
        return {"extracted_data": {"content": full_content}}
    
    schema = state.get("target_schema")
    prompt_template = state.get("prompt_template")
    
    if not schema:
        return {"error": "Missing schema for extraction"}
        
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(schema)
    
    try:
        # Determine System Prompt
        if prompt_template:
            # If a specific prompt is provided (e.g. Brand Identity, Team, etc.)
            system_msg = prompt_template
        else:
            # Fallback/Default Prompt
            system_msg = "You are an expert Data Extractor. Extract the requested information from the provided website content."
            
        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=f"Website Content (Crawled Pages):\n\n{full_content[:50000]}") # Token limit safety
        ]
        
        result = structured_llm.invoke(messages)
        return {"extracted_data": result}
    except Exception as e:
        return {"error": f"Extraction failed: {str(e)}"}
