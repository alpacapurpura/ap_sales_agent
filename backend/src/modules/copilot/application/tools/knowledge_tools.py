"""Knowledge tools group — exports the curated marketing KB search tool.

F10 retired the per-tenant ``search_knowledge_base(query, scope)`` tool in
favour of ``knowledge_search`` (tenant-agnostic, domain/methodology filters).
This file is the registry shim — ``ROUTE_TOOL_MAP`` still references the
``"knowledge"`` group via ``KNOWLEDGE_TOOLS`` so we keep the same export
surface and just swap the implementation underneath.

[COPILOT-MARKETING-KB-F10]
"""

from luana_core_copilot.application.tools.knowledge_search import knowledge_search

KNOWLEDGE_TOOLS = [knowledge_search]
