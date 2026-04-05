"""
CopilotOrchestrator — Manages conversation state and streams responses via SSE.
"""

import json
import uuid
from collections.abc import AsyncGenerator
from uuid import UUID

import structlog
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from sqlalchemy.orm import Session

from src.core.database import redis_client
from src.modules.copilot.api.dto import ClientContextDTO, SSEEvent
from src.modules.copilot.application.orchestrator.graph import copilot_graph
from src.modules.copilot.application.orchestrator.state import (
    create_initial_copilot_state,
)
from src.modules.copilot.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
)

logger = structlog.get_logger()

# Redis key prefix for active conversation context (TTL 1h)
REDIS_CONV_PREFIX = "copilot:conv:"
REDIS_CONV_TTL = 3600


class CopilotOrchestrator:
    """
    Orchestrates the Copilot agent: manages conversation state,
    persists history, and streams SSE events to the frontend.
    """

    def __init__(self, db: Session):
        self.db = db
        self.conv_repo = ConversationRepository(db)

    async def stream_chat(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        message: str,
        conversation_id: str | None = None,
        context: ClientContextDTO | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Process a user message and yield SSE events.
        """
        # 1. Resolve or create conversation
        conv_id = conversation_id or str(uuid.uuid4())
        conv_uuid = UUID(conv_id)

        # Try to load existing conversation from DB
        existing_conv = self.conv_repo.get_by_id(conv_uuid, tenant_id)
        if not existing_conv:
            existing_conv = self.conv_repo.create(
                conversation_id=conv_uuid,
                tenant_id=tenant_id,
                user_id=user_id,
            )
            self.db.commit()

        # 2. Build state
        client_ctx = {
            "current_route": context.current_route if context else None,
            "selected_fields": [
                f.model_dump() if hasattr(f, "model_dump") else f
                for f in (context.selected_fields if context else [])
            ],
            "form_data": context.form_data if context else {},
            "locale": context.locale if context else "es",
        }

        state = create_initial_copilot_state(
            user_id=user_id,
            tenant_id=tenant_id,
            conversation_id=conv_id,
            client_context=client_ctx,
        )

        # 3. Load conversation history from Redis (fast) or DB (fallback)
        history_messages = self._load_history(conv_id, tenant_id, existing_conv)
        state["messages"] = [*history_messages, HumanMessage(content=message)]

        # 4. Emit status: thinking
        yield SSEEvent(event="status", data={"state": "thinking"}).to_sse()

        # 5. Stream the graph execution
        full_response = ""
        accumulated_messages: list = []  # Collect LangChain messages for persistence
        last_tool_call_ids: dict[str, str] = {}  # tool_name -> tool_call_id
        try:
            yield SSEEvent(event="status", data={"state": "streaming"}).to_sse()

            # Use astream_events for granular streaming
            async for event in copilot_graph.astream_events(state, version="v2"):
                kind = event.get("event")

                # Stream text chunks from the LLM
                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        full_response += chunk.content
                        yield SSEEvent(
                            event="text_chunk",
                            data={"content": chunk.content},
                        ).to_sse()

                # Capture complete AIMessages (with tool_calls)
                elif kind == "on_chat_model_end":
                    output = event.get("data", {}).get("output")
                    if isinstance(output, AIMessage):
                        accumulated_messages.append(output)
                        if output.tool_calls:
                            for tc in output.tool_calls:
                                last_tool_call_ids[tc["name"]] = tc["id"]

                # Tool execution events
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    tool_input = event.get("data", {}).get("input", {})
                    yield SSEEvent(
                        event="tool_start",
                        data={"tool": tool_name, "args": tool_input},
                    ).to_sse()

                elif kind == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    tool_output = event.get("data", {}).get("output", "")

                    # Capture ToolMessage for persistence
                    if isinstance(tool_output, ToolMessage):
                        accumulated_messages.append(tool_output)
                    elif isinstance(tool_output, str):
                        tool_call_id = last_tool_call_ids.pop(tool_name, "")
                        accumulated_messages.append(
                            ToolMessage(
                                content=tool_output,
                                name=tool_name,
                                tool_call_id=tool_call_id,
                            )
                        )

                    yield SSEEvent(
                        event="tool_result",
                        data={
                            "tool": tool_name,
                            "result": str(tool_output)[:500],
                        },
                    ).to_sse()

                    # If tool result contains a ui_action, emit it
                    parsed = tool_output if isinstance(tool_output, dict) else None
                    if not parsed and isinstance(tool_output, str):
                        try:
                            parsed = json.loads(tool_output)
                        except (json.JSONDecodeError, ValueError):
                            parsed = None
                    if isinstance(parsed, dict) and "ui_action" in parsed:
                        yield SSEEvent(
                            event="ui_action",
                            data=parsed["ui_action"],
                        ).to_sse()

        except Exception as e:
            logger.error("copilot_stream_error", error=str(e), conversation_id=conv_id)
            yield SSEEvent(
                event="error",
                data={
                    "message": "Ocurrió un error procesando tu mensaje. Intenta de nuevo."
                },
            ).to_sse()
            full_response = ""
            accumulated_messages = []

        # 6. Persist messages (full chain including tool_calls)
        if full_response or accumulated_messages:
            new_messages = self._serialize_messages(
                [HumanMessage(content=message), *accumulated_messages]
            )
            # Fallback: if no accumulated messages, persist simple format
            if not accumulated_messages:
                new_messages = [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": full_response},
                ]

            self.conv_repo.append_messages(conv_uuid, tenant_id, new_messages)

            # Auto-title on first message
            if not existing_conv.title and message:
                title = message[:80] + ("..." if len(message) > 80 else "")
                self.conv_repo.update_title(conv_uuid, tenant_id, title)

            self.db.commit()

            # Cache in Redis for fast access
            self._cache_history(conv_id, tenant_id, new_messages)

        # 7. Emit done
        yield SSEEvent(event="status", data={"state": "done"}).to_sse()
        yield SSEEvent(event="done", data={"conversation_id": conv_id}).to_sse()

    def _load_history(self, conv_id: str, tenant_id: UUID, conv_model) -> list:
        """Load conversation history, preferring Redis cache."""
        # Try Redis first
        redis_key = f"{REDIS_CONV_PREFIX}{conv_id}"
        try:
            cached = redis_client.get(redis_key) if redis_client else None
            if cached:
                raw_messages = json.loads(cached)
                return self._deserialize_messages(raw_messages)
        except Exception as e:
            logger.debug("redis_history_miss", conv_id=conv_id, error=str(e))

        # Fallback to DB
        if conv_model and conv_model.messages:
            # Re-cache in Redis
            try:
                if redis_client:
                    redis_client.setex(
                        redis_key,
                        REDIS_CONV_TTL,
                        json.dumps(conv_model.messages, ensure_ascii=False),
                    )
            except Exception:  # noqa: S110
                pass
            return self._deserialize_messages(conv_model.messages)

        return []

    def _cache_history(self, conv_id: str, tenant_id: UUID, new_messages: list) -> None:
        """Append new messages to Redis cache."""
        redis_key = f"{REDIS_CONV_PREFIX}{conv_id}"
        try:
            if not redis_client:
                return
            cached = redis_client.get(redis_key)
            existing = json.loads(cached) if cached else []
            existing.extend(new_messages)
            redis_client.setex(
                redis_key,
                REDIS_CONV_TTL,
                json.dumps(existing, ensure_ascii=False),
            )
        except Exception as e:
            logger.debug("redis_cache_error", error=str(e))

    @staticmethod
    def _serialize_messages(messages: list) -> list[dict]:
        """Convert LangChain message objects to persistable dicts.

        Preserves tool_calls on AIMessages and ToolMessages for full
        conversation replay.
        """
        result = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                d: dict = {"role": "assistant", "content": msg.content}
                if msg.tool_calls:
                    d["tool_calls"] = [
                        {"id": tc["id"], "name": tc["name"], "args": tc["args"]}
                        for tc in msg.tool_calls
                    ]
                result.append(d)
            elif isinstance(msg, ToolMessage):
                result.append(
                    {
                        "role": "tool",
                        "content": msg.content,
                        "tool_call_id": msg.tool_call_id,
                        "name": msg.name,
                    }
                )
        return result

    @staticmethod
    def _deserialize_messages(raw_messages: list) -> list:
        """Convert persisted dict messages to LangChain message objects.

        Backward compatible: messages without tool_calls or tool role
        are handled as before.
        """
        result = []
        for msg in raw_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                result.append(HumanMessage(content=content))
            elif role == "assistant":
                if msg.get("tool_calls"):
                    result.append(
                        AIMessage(content=content, tool_calls=msg["tool_calls"])
                    )
                else:
                    result.append(AIMessage(content=content))
            elif role == "tool":
                result.append(
                    ToolMessage(
                        content=content,
                        tool_call_id=msg.get("tool_call_id", ""),
                        name=msg.get("name", ""),
                    )
                )
        return result
