BRAND_STORY_PROMPT = """
You are an expert Storyteller and Brand Strategist.
Your task is to analyze the provided website content and extract the Brand Story.

CONTENT:
{content}

CURRENT DATA (If updating):
{current_data}

USER INSTRUCTIONS (If updating):
{instructions}

INSTRUCTIONS:
1. **Origin Story**: Find the "About Us" or "History" section. Why was the company founded? What problem were they trying to solve? Write a compelling origin story (max 300 words).
2. **Milestones**: Identify key dates and achievements.

IF CURRENT DATA IS PROVIDED:
- Compare new content with current data.
- Enhance the story with new details found.
- Respect user instructions for refinement.
- IMPORTANT: If current data is empty, EXTRACT EVERYTHING from content.
- IMPORTANT: The 'origin_story' and 'milestone descriptions' MUST be in SPANISH. Translate if necessary.

OUTPUT FORMAT:
Return a JSON object matching the BrandStory schema. Ensure 'origin_story' is populated if text is available.
"""
