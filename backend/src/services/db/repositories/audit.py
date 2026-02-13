from typing import List, Dict, Optional, Any
from sqlalchemy import desc, func
from sqlalchemy.orm import selectinload
from src.services.db.models.lead import Lead
from src.services.db.models.observability import Message, AgentTrace, LLMCallLog
from src.services.db.models.business import JourneyProgress
from src.core.domain.schema import FunnelStage, LeadStatus
from .base import BaseRepository
import logging

logger = logging.getLogger(__name__)

class AuditRepository(BaseRepository):
    def log_message(self, user_id, role, content, channel=None, product_context_id=None):
        try:
            msg = Message(
                lead_id=user_id,
                role=role,
                content=content,
                channel=channel,
                product_context_id=product_context_id
            )
            self._set_tenant(msg)
            self.db.add(msg)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error logging message to DB: {e}")
            self.db.rollback()

    def get_last_message(self, user_id) -> Optional[Message]:
        return self.db.query(Message).filter(
            Message.lead_id == user_id,
            Message.role == "user"
        ).order_by(desc(Message.created_at)).first()

    def get_chat_history(self, user_id, limit=20) -> List[Dict[str, str]]:
        messages = self.db.query(Message).filter(
            Message.lead_id == user_id
        ).order_by(desc(Message.created_at)).limit(limit).all()
        
        messages.reverse()
        
        history = []
        for m in messages:
            history.append({
                "role": m.role,
                "content": m.content
            })
        return history

    def get_recent_users(self, tenant_id, limit=20) -> List[Any]:
        # 1. Subconsulta para encontrar la fecha del último mensaje por usuario
        # IMPORTANTE: Usamos label("lead_id") porque la columna en DB es "user_id"
        # y al usar subquery(), SQLAlchemy expone el nombre de la columna DB, no el atributo.
        subquery = self.db.query(
            Message.lead_id.label("lead_id"),
            func.max(Message.created_at).label("last_activity")
        ).filter(Message.tenant_id == tenant_id)\
        .group_by(Message.lead_id).subquery()
        
        # 2. Join con la tabla Lead para obtener datos del usuario + fecha actividad
        results = self.db.query(Lead, subquery.c.last_activity)\
            .join(subquery, Lead.id == subquery.c.lead_id)\
            .filter(Lead.tenant_id == tenant_id)\
            .order_by(desc(subquery.c.last_activity))\
            .limit(limit)\
            .all()
            
        return results
            
    def get_full_timeline(self, user_id: str, tenant_id: Any = None, limit: int = 50) -> List[Dict]:
        # Messages
        query_msg = self.db.query(Message).filter(Message.lead_id == user_id)
        if tenant_id:
            query_msg = query_msg.filter(Message.tenant_id == tenant_id)
        messages = query_msg.order_by(desc(Message.created_at)).limit(limit).all()

        # Traces
        query_trace = self.db.query(AgentTrace).filter(AgentTrace.lead_id == user_id).options(selectinload(AgentTrace.llm_logs))
        if tenant_id:
            query_trace = query_trace.filter(AgentTrace.tenant_id == tenant_id)
        traces = query_trace.order_by(desc(AgentTrace.created_at)).limit(limit).all()

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
            llm_summary = None
            if t.llm_logs:
                total_input = sum(log.tokens_input or 0 for log in t.llm_logs)
                total_output = sum(log.tokens_output or 0 for log in t.llm_logs)
                model = t.llm_logs[0].model if t.llm_logs else None
                
                llm_summary = {
                    "model": model,
                    "total_tokens": total_input + total_output
                }

            timeline.append({
                "type": "trace",
                "id": str(t.id),
                "node_name": t.node_name,
                "execution_time_ms": t.execution_time_ms,
                "created_at": t.created_at,
                "timestamp": t.created_at.timestamp(),
                "llm_summary": llm_summary
            })

        timeline.sort(key=lambda x: x["timestamp"])
        return timeline

    def get_trace_details(self, trace_id: str, tenant_id: Any = None) -> Optional[Dict]:
        query = self.db.query(AgentTrace).filter(AgentTrace.id == trace_id)
        if tenant_id:
            query = query.filter(AgentTrace.tenant_id == tenant_id)
        trace = query.first()
        
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

    def create_trace(self, user_id, session_id, node_name, input_state, output_state, execution_time_ms, action=None, reward=None, feedback=None) -> Optional[AgentTrace]:
        try:
            trace = AgentTrace(
                lead_id=user_id,
                session_id=session_id,
                node_name=node_name,
                input_state=input_state,
                output_state=output_state,
                execution_time_ms=execution_time_ms,
                action=action,
                reward=reward,
                feedback=feedback
            )
            self._set_tenant(trace)
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
            self._set_tenant(log)
            self.db.add(log)
            self.db.commit()
            return log
        except Exception as e:
            logger.error(f"Error creating LLM log: {e}")
            self.db.rollback()
            return None
    def clear_user_history(self, user_id, tenant_id=None) -> bool:
        try:
            # Delete messages
            q_msg = self.db.query(Message).filter(Message.lead_id == user_id)
            if tenant_id:
                q_msg = q_msg.filter(Message.tenant_id == tenant_id)
            q_msg.delete(synchronize_session=False)
            
            # Get traces to delete logs
            q_trace = self.db.query(AgentTrace).filter(AgentTrace.lead_id == user_id)
            if tenant_id:
                q_trace = q_trace.filter(AgentTrace.tenant_id == tenant_id)
            traces = q_trace.all()
            trace_ids = [t.id for t in traces]
            
            if trace_ids:
                # Logs
                # LLMCallLog might check tenant too, but trace ownership implies safety usually.
                # Adding tenant check if model supports it (LLMCallLog has tenant_id)
                q_logs = self.db.query(LLMCallLog).filter(LLMCallLog.trace_id.in_(trace_ids))
                if tenant_id:
                    q_logs = q_logs.filter(LLMCallLog.tenant_id == tenant_id)
                q_logs.delete(synchronize_session=False)
                
                # Delete traces
                q_trace.delete(synchronize_session=False)
                
            # Journeys (formerly Enrollments)
            q_journey = self.db.query(JourneyProgress).filter(JourneyProgress.lead_id == user_id)
            if tenant_id:
                q_journey = q_journey.filter(JourneyProgress.tenant_id == tenant_id)
            journeys = q_journey.all()
            
            for j in journeys:
                j.stage = FunnelStage.RAPPORT.value
                j.status = LeadStatus.AWARENESS.value
                j.lead_score = 0
                j.objections = []
                j.objection_status = None # Reset new field
            
            # Profile Data
            q_lead = self.db.query(Lead).filter(Lead.id == user_id)
            if tenant_id:
                q_lead = q_lead.filter(Lead.tenant_id == tenant_id)
            user = q_lead.first()
            if user:
                user.profile_data = {}
            
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            self.db.rollback()
            return False
