---
alwaysApply: false
description: "Stack tecnológico backend: FastAPI, LangGraph, PostgreSQL y Qdrant. Usar para referencia de librerías y herramientas aprobadas."
---
# Backend Technology Stack

Frameworks & Core:
- Framework: FastAPI (Python 3.11+)
- Agent Engine: LangGraph (Stateful, Multi-turn workflows)
- Admin UI for internal test: Streamlit (Internal tools only)

Data & Persistence:
- Database: PostgreSQL (via SQLAlchemy ORM)
- Vector Store: Qdrant (for RAG)

AI & LLM:
- Providers: OpenAI, Google Gemini
- Integration: Adapter Pattern (to switch providers easily)
