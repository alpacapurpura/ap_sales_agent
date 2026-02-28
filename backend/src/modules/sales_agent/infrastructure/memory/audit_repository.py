from typing import List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.shared.infrastructure.db.models import AgentTrace, LLMLog
from src.modules.sales.infrastructure.models.lead_model import LeadModel
from src.modules.communication.infrastructure.models.message_model import MessageModel as Message
from src.modules.sales_agent.domain.memory.repository import EpisodicMemoryStore

class AuditRepository(EpisodicMemoryStore):
    def __init__(self, db: Session):
        self.db = db

    # --- EpisodicMemoryStore Implementation ---

    def get_chat_history(self, user_id: str, limit: int = 10) -> List[Any]:
        # Return last N messages in ascending order (oldest to newest) for context
        msgs = self.db.query(Message).filter(Message.lead_id == user_id).order_by(Message.created_at.desc()).limit(limit).all()
        return list(reversed(msgs))

    def log_message(self, user_id: str, role: str, content: str, channel: str) -> Any:
        msg = Message(
            lead_id=user_id,
            sender_type=role,
            content=content,
            channel=channel
        )
        self.db.add(msg)
        self.db.commit()
        return msg

    def get_last_message(self, user_id: str) -> Any:
        return self.db.query(Message).filter(Message.lead_id == user_id).order_by(Message.created_at.desc()).first()

    # --- Audit / Monitoring Specific Methods ---

    def create_trace(self, user_id, session_id, node_name, input_state, output_state, execution_time_ms):
        trace = AgentTrace(
            user_id=user_id,
            session_id=session_id,
            node_name=node_name,
            input_state=input_state,
            output_state=output_state,
            execution_time_ms=execution_time_ms
        )
        self.db.add(trace)
        self.db.commit()
        self.db.refresh(trace)
        return trace

    def create_llm_log(self, trace_id, model, prompt_template, prompt_rendered, response_text, tokens_input, tokens_output, metadata=None):
        log = LLMLog(
            trace_id=trace_id,
            model=model,
            prompt_template=prompt_template,
            prompt_rendered=prompt_rendered,
            response_text=response_text,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            metadata_info=metadata or {}
        )
        self.db.add(log)
        self.db.commit()
        return log

    def get_recent_users(self, tenant_id, limit=20):
        # Join AgentTrace with LeadModel to get recent active leads
        # Query Traces, group by user_id, max(created_at)
        
        subquery = (
            self.db.query(
                AgentTrace.user_id,
                func.max(AgentTrace.created_at).label("last_activity")
            )
            .filter(AgentTrace.tenant_id == tenant_id) if tenant_id else self.db.query(AgentTrace.user_id, func.max(AgentTrace.created_at).label("last_activity"))
        )
        
        if tenant_id:
            subquery = subquery.filter(AgentTrace.tenant_id == tenant_id)
            
        subquery = subquery.group_by(AgentTrace.user_id).subquery()
        
        query = (
            self.db.query(LeadModel, subquery.c.last_activity)
            .join(subquery, LeadModel.id == subquery.c.user_id)
            .order_by(subquery.c.last_activity.desc())
            .limit(limit)
        )
        
        return query.all()

    def clear_user_history(self, lead_id, tenant_id):
        # Delete traces for user
        self.db.query(AgentTrace).filter(AgentTrace.user_id == lead_id).delete()
        self.db.commit()
        return True

    def get_full_timeline(self, lead_id, tenant_id, limit=50):
        # Fetch Messages
        messages = self.db.query(Message).filter(Message.lead_id == lead_id).order_by(Message.created_at.desc()).limit(limit).all()
        
        # Fetch Traces
        traces = self.db.query(AgentTrace).filter(AgentTrace.user_id == lead_id).order_by(AgentTrace.created_at.desc()).limit(limit).all()
        
        timeline = []
        for m in messages:
            timeline.append({
                "type": "message",
                "id": str(m.id),
                "role": m.sender_type,
                "content": m.content,
                "created_at": m.created_at
            })
            
        for t in traces:
            timeline.append({
                "type": "trace",
                "id": str(t.id),
                "node": t.node_name,
                "input": t.input_state,
                "output": t.output_state,
                "created_at": t.created_at
            })
            
        # Sort combined
        timeline.sort(key=lambda x: x["created_at"], reverse=True)
        return timeline[:limit]

    def get_trace_details(self, trace_id, tenant_id):
        trace = self.db.query(AgentTrace).filter(AgentTrace.id == trace_id).first()
        if not trace:
            return None
            
        logs = self.db.query(LLMLog).filter(LLMLog.trace_id == trace_id).all()
        
        return {
            "trace": {
                "id": str(trace.id),
                "node": trace.node_name,
                "input": trace.input_state,
                "output": trace.output_state,
                "created_at": trace.created_at,
                "execution_time": trace.execution_time_ms
            },
            "llm_logs": [
                {
                    "model": l.model,
                    "prompt": l.prompt_rendered,
                    "response": l.response_text,
                    "tokens": {"in": l.tokens_input, "out": l.tokens_output},
                    "metadata": l.metadata_info
                } for l in logs
            ]
        }

    def close(self):
        self.db.close()
