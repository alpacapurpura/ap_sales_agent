"""Guided setup — conversation-embedded structured flow.

Replaces the standalone interview engine. State lives inside
``CopilotConversation.procedure_state["guided"]`` so no extra table is needed.
Blocks are generated dynamically from the editable-field catalog (no
hardcoded config files).
"""
