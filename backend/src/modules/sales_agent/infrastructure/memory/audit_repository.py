from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from src.modules.crm.infrastructure.models.lead_model import LeadModel
from src.modules.sales_agent.domain.memory.repository import EpisodicMemoryStore
from src.modules.sales_agent.infrastructure.models.agent_trace_model import AgentTrace
from src.modules.sales_agent.infrastructure.models.llm_log_model import LLMLog
from src.modules.sales_agent.infrastructure.models.message_model import (
    MessageModel as Message,
)


class AuditRepository(EpisodicMemoryStore):
    def __init__(self, db: Session):
        self.db = db

    # --- EpisodicMemoryStore Implementation ---

    def get_chat_history(self, user_id: str, limit: int = 10) -> list[Any]:
        # Return last N messages in ascending order (oldest to newest) for context
        msgs = (
            self.db.execute(
                select(Message)
                .where(Message.user_id == user_id)
                .order_by(Message.created_at.desc())
                .limit(limit),
            )
            .scalars()
            .all()
        )
        return list(reversed(msgs))

    def log_message(
        self,
        user_id: str,
        role: str,
        content: str,
        channel: str,
        tenant_id: str = None,
    ) -> Any:
        msg = Message(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            content=content,
            channel=channel,
        )
        self.db.add(msg)
        self.db.commit()
        return msg

    def get_last_message(self, user_id: str) -> Any:
        return (
            self.db.execute(
                select(Message)
                .where(Message.user_id == user_id)
                .order_by(Message.created_at.desc()),
            )
            .scalars()
            .first()
        )

    # --- Audit / Monitoring Specific Methods ---

    def create_trace(
        self,
        user_id,
        session_id,
        node_name,
        input_state,
        output_state,
        execution_time_ms,
        tenant_id=None,
    ):
        trace = AgentTrace(
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            node_name=node_name,
            input_state=input_state,
            output_state=output_state,
            execution_time_ms=execution_time_ms,
        )
        self.db.add(trace)
        self.db.commit()
        self.db.refresh(trace)
        return trace

    def create_llm_log(
        self,
        trace_id,
        model,
        prompt_template,
        prompt_rendered,
        response_text,
        tokens_input,
        tokens_output,
        metadata=None,
    ):
        log = LLMLog(
            trace_id=trace_id,
            model=model,
            prompt_template=prompt_template,
            prompt_rendered=prompt_rendered,
            response_text=response_text,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            metadata_info=metadata or {},
        )
        self.db.add(log)
        self.db.commit()
        return log

    def get_recent_users(self, tenant_id, limit=20):
        # Join AgentTrace with LeadModel to get recent active leads
        # Query Traces, group by user_id, max(created_at)
        base_stmt = select(
            AgentTrace.user_id,
            func.max(AgentTrace.created_at).label("last_activity"),
        )
        if tenant_id:
            base_stmt = base_stmt.where(AgentTrace.tenant_id == tenant_id)

        subquery = base_stmt.group_by(AgentTrace.user_id).subquery()

        stmt = (
            select(LeadModel, subquery.c.last_activity)
            .join(subquery, LeadModel.id == subquery.c.user_id)
            .order_by(subquery.c.last_activity.desc())
            .limit(limit)
        )

        return self.db.execute(stmt).all()

    def clear_user_history(self, lead_id, tenant_id):
        from sqlalchemy import text

        lead_uuid = str(lead_id)
        self.db.execute(
            text(
                "DELETE FROM llm_logs WHERE trace_id IN "
                "(SELECT id FROM agent_traces WHERE user_id = :lid)",
            ),
            {"lid": lead_uuid},
        )
        self.db.execute(
            text(
                "DELETE FROM llm_call_logs WHERE trace_id IN "
                "(SELECT id FROM agent_traces WHERE user_id = :lid)",
            ),
            {"lid": lead_uuid},
        )
        self.db.execute(
            text("DELETE FROM agent_traces WHERE user_id = :lid"),
            {"lid": lead_uuid},
        )
        self.db.execute(
            text("DELETE FROM messages WHERE user_id = :lid"),
            {"lid": lead_uuid},
        )
        self.db.execute(
            text("DELETE FROM agent_state_checkpoints WHERE lead_id = :lid"),
            {"lid": lead_uuid},
        )
        self.db.execute(
            text(
                "UPDATE leads SET "
                "profile_data = '{}', fit_score = 0, intent_score = 0, "
                "temperature = 'COLD', conversation_summary = NULL, "
                "key_objections_history = '[]', style_profile = '{}', "
                "custom_system_instruction = NULL, last_interaction_date = NULL "
                "WHERE id = :lid",
            ),
            {"lid": lead_uuid},
        )
        self.db.commit()
        return True

    def get_full_timeline(self, lead_id, tenant_id, limit=50):
        messages = (
            self.db.execute(
                select(Message)
                .where(Message.user_id == lead_id)
                .order_by(Message.created_at.desc())
                .limit(limit),
            )
            .scalars()
            .all()
        )

        traces = (
            self.db.execute(
                select(AgentTrace)
                .options(joinedload(AgentTrace.llm_logs))
                .where(AgentTrace.user_id == lead_id)
                .order_by(AgentTrace.created_at.desc())
                .limit(limit),
            )
            .scalars()
            .all()
        )

        timeline = [
            {
                "type": "message",
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at,
            }
            for m in messages
        ]

        for t in traces:
            llm_summary = None
            if t.llm_logs:
                total_tokens = sum(
                    (log_entry.tokens_input or 0) + (log_entry.tokens_output or 0)
                    for log_entry in t.llm_logs
                )
                first_log = t.llm_logs[0]
                llm_summary = {
                    "model": first_log.model,
                    "total_tokens": total_tokens,
                    "prompt_template": first_log.prompt_template,
                }

            timeline.append(
                {
                    "type": "trace",
                    "id": str(t.id),
                    "node": t.node_name,
                    "input": t.input_state,
                    "output": t.output_state,
                    "execution_time": t.execution_time_ms,
                    "llm_summary": llm_summary,
                    "created_at": t.created_at,
                },
            )

        timeline.sort(key=lambda x: x["created_at"], reverse=True)
        return timeline[:limit]

    def get_trace_details(self, trace_id, tenant_id):
        trace = (
            self.db.execute(select(AgentTrace).where(AgentTrace.id == trace_id))
            .scalars()
            .first()
        )
        if not trace:
            return None

        logs = (
            self.db.execute(select(LLMLog).where(LLMLog.trace_id == trace_id))
            .scalars()
            .all()
        )

        return {
            "trace": {
                "id": str(trace.id),
                "node": trace.node_name,
                "input": trace.input_state,
                "output": trace.output_state,
                "created_at": trace.created_at,
                "execution_time": trace.execution_time_ms,
            },
            "llm_logs": [
                {
                    "id": str(log_entry.id),
                    "model": log_entry.model,
                    "prompt_template": log_entry.prompt_template or "unknown",
                    "prompt": log_entry.prompt_rendered,
                    "response": log_entry.response_text,
                    "tokens": {
                        "in": log_entry.tokens_input,
                        "out": log_entry.tokens_output,
                    },
                    "metadata": log_entry.metadata_info,
                }
                for log_entry in logs
            ],
        }

    def close(self):
        self.db.close()
