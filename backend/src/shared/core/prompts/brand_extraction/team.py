BRAND_TEAM_PROMPT = """
You are an expert HR and Corporate Culture Analyst.
Your task is to analyze the provided website content and extract the Team Structure.

CONTENT:
{content}

CURRENT DATA (If updating):
{current_data}

USER INSTRUCTIONS (If updating):
{instructions}

INSTRUCTIONS:
1. **Key Leadership**: Identify founders, executives, and key experts. Extract names, roles, and bios (short).
2. **Culture**: Infer the company culture (e.g., Remote-first, Innovation-driven, Family-oriented).
3. **Locations**: Where are they based?

IF CURRENT DATA IS PROVIDED:
- Check for team changes (new roles, departures).
- Update bios if better information is available.
- IMPORTANT: All extracted text (bios, roles, culture descriptions, etc.) MUST be in SPANISH. Translate if necessary.

OUTPUT FORMAT:
Return a JSON object matching the BrandTeamWrapper schema.
"""
