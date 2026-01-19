from typing import List, Dict, Optional, Any
from sqlalchemy import desc, func
from src.services.db.models.user import User
from src.services.db.models.observability import Message, AgentTrace, LLMCallLog
from src.services.db.models.business import Enrollment
from src.core.schema import FunnelStage, LeadStatus
from .base import BaseRepository
import logging

logger = logging.getLogger(__name__)

class AuditRepository(BaseRepository):
    def log_message(self, user_id, role, content, channel=None, product_context_id=None):
        try:
            msg = Message(
                user_id=user_id,
                role=role,
                content=content,
                channel=channel,
                product_context_id=product_context_id
            )
            self.db.add(msg)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error logging message to DB: {e}")
            self.db.rollback()

    def get_last_message(self, user_id) -> Optional[Message]:
        return self.db.query(Message).filter(
            Message.user_id == user_id,
            Message.role == "user"
        ).order_by(desc(Message.created_at)).first()

    def get_chat_history(self, user_id, limit=20) -> List[Dict[str, str]]:
        messages = self.db.query(Message).filter(
            Message.user_id == user_id
        ).order_by(desc(Message.created_at)).limit(limit).all()
        
        messages.reverse()
        
        history = []
        for m in messages:
            history.append({
                "role": m.role,
                "content": m.content
            })
        return history

    def get_recent_users(self, limit=20) -> List[Any]:
        subquery = self.db.query(
            Message.user_id,
            func.max(Message.created_at).label("last_activity")
        ).group_by(Message.user_id).subquery()
        
        results = self.db.query(User, subquery.c.last_activity)\
            .join(subquery, User.id == subquery.c.user_id)\
            .order_by(desc(subquery.c.last_activity))\
            .limit(limit)\
            .all()
            
        return results

    def get_full_timeline(self, user_id: str, limit: int = 50) -> List[Dict]:
        # Messages
        messages = self.db.query(Message).filter(
            Message.user_id == user_id
        ).order_by(desc(Message.created_at)).limit(limit).all()

        # Traces
        traces = self.db.query(AgentTrace).filter(
            AgentTrace.user_id == user_id
        ).order_by(desc(AgentTrace.created_at)).limit(limit).all()

        timeline = []
        for m in messages:
            timeline.append({
                "type": "message",
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at,
                "timestamp": m.created_at.timestamp()
            })

        for t in traces:
            timeline.append({
                "type": "trace",
                "id": str(t.id),
                "node_name": t.node_name,
                "execution_time_ms": t.execution_time_ms,
                "created_at": t.created_at,
                "timestamp": t.created_at.timestamp()
            })

        timeline.sort(key=lambda x: x["timestamp"])
        return timeline

    def get_trace_details(self, trace_id: str) -> Optional[Dict]:
        trace = self.db.query(AgentTrace).filter(AgentTrace.id == trace_id).first()
        if not trace:
            return None
            
        llm_logs = []
        for log in trace.llm_logs:
            llm_logs.append({
                "id": str(log.id),
                "model": log.model,
                "prompt_template": log.prompt_template,
                "prompt_rendered": log.prompt_rendered,
                "response_text": log.response_text,
                "tokens_input": log.tokens_input,
                "tokens_output": log.tokens_output,
                "metadata": log.metadata_info
            })
            
        return {
            "id": str(trace.id),
            "node_name": trace.node_name,
            "input_state": trace.input_state,
            "output_state": trace.output_state,
            "execution_time_ms": trace.execution_time_ms,
            "created_at": trace.created_at,
            "llm_logs": llm_logs
        }

    def create_trace(self, user_id, session_id, node_name, input_state, output_state, execution_time_ms) -> Optional[AgentTrace]:
        try:
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
        except Exception as e:
            logger.error(f"Error creating trace: {e}")
            self.db.rollback()
            return None

    def create_llm_log(self, trace_id, model, prompt_template, prompt_rendered, response_text, tokens_input=0, tokens_output=0, metadata=None) -> Optional[LLMCallLog]:
        try:
            log = LLMCallLog(
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
        except Exception as e:
            logger.error(f"Error creating LLM log: {e}")
            self.db.rollback()
            return None
    def clear_user_history(self, user_id) -> bool:
        try:
            self.db.query(Message).filter(Message.user_id == user_id).delete(synchronize_session=False)
            
            traces = self.db.query(AgentTrace).filter(AgentTrace.user_id == user_id).all()
            trace_ids = [t.id for t in traces]
            
            if trace_ids:
                self.db.query(LLMCallLog).filter(LLMCallLog.trace_id.in_(trace_ids)).delete(synchronize_session=False)
                self.db.query(AgentTrace).filter(AgentTrace.user_id == user_id).delete(synchronize_session=False)
                
            enrollments = self.db.query(Enrollment).filter(Enrollment.user_id == user_id).all()
            for e in enrollments:
                e.stage = FunnelStage.RAPPORT.value
                e.status = LeadStatus.AWARENESS.value
                e.lead_score = 0
                e.objections = []
            
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.profile_data = {}
            
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            self.db.rollback()
            return False
