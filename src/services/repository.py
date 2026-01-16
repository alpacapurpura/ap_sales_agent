from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func
from sqlalchemy.exc import SQLAlchemyError
from src.services.models import User, Product, Enrollment, Appointment, Message, OfferLog, AgentTrace, LLMCallLog
from src.services.database import SessionLocal
from src.core.schema import FunnelStage, LeadStatus, ProductLaunchStage
import datetime
import logging
from typing import Optional, List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

class Repository:
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def close(self):
        self.db.close()

    def clear_user_conversation(self, user_id) -> bool:
        """
        Deletes all Messages, Traces, and resets Enrollment for a user.
        Allows starting the conversation from scratch.
        """
        try:
            # 1. Delete Messages
            self.db.query(Message).filter(Message.user_id == user_id).delete(synchronize_session=False)
            
            # 2. Delete Traces (Cascade should handle LLM Logs, but manual safety check)
            # Find traces first
            traces = self.db.query(AgentTrace).filter(AgentTrace.user_id == user_id).all()
            trace_ids = [t.id for t in traces]
            
            if trace_ids:
                # Delete linked LLM Logs first (if not cascading)
                self.db.query(LLMCallLog).filter(LLMCallLog.trace_id.in_(trace_ids)).delete(synchronize_session=False)
                # Delete Traces
                self.db.query(AgentTrace).filter(AgentTrace.user_id == user_id).delete(synchronize_session=False)
                
            # 3. Reset Enrollment Status (Reset Funnel)
            enrollments = self.db.query(Enrollment).filter(Enrollment.user_id == user_id).all()
            for e in enrollments:
                e.stage = FunnelStage.RAPPORT.value
                e.status = LeadStatus.AWARENESS.value
                e.lead_score = 0
                e.objections = []
            
            # 4. Clear Psychographics (Optional, but good for clean slate)
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.profile_data = {}
            
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error clearing conversation for user {user_id}: {e}")
            self.db.rollback()
            return False

    # --- User Management ---
    def get_user_by_channel_id(self, channel: str, user_id: str) -> Optional[User]:
        if channel == "telegram":
            return self.db.query(User).filter(User.telegram_id == user_id).first()
        elif channel == "whatsapp":
            return self.db.query(User).filter(User.whatsapp_id == user_id).first()
        elif channel == "instagram":
            return self.db.query(User).filter(User.instagram_id == user_id).first()
        elif channel == "tiktok":
            return self.db.query(User).filter(User.tiktok_id == user_id).first()
        return None

    def create_user(self, full_name: str, channel: str, channel_user_id: str, extra_data: dict = None) -> User:
        user = User(full_name=full_name)
        if channel == "telegram":
            user.telegram_id = channel_user_id
        elif channel == "whatsapp":
            user.whatsapp_id = channel_user_id
        elif channel == "instagram":
            user.instagram_id = channel_user_id
        elif channel == "tiktok":
            user.tiktok_id = channel_user_id
            
        if extra_data:
            # Map extra data to profile or demographics if needed
            pass
            
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user_profile(self, user_id, psychographics_update: dict) -> Optional[User]:
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            # Merge JSONB
            current = dict(user.profile_data) if user.profile_data else {}
            
            # Smart merge for lists (append unique)
            for k, v in psychographics_update.items():
                if isinstance(v, list) and k in current and isinstance(current[k], list):
                    current[k] = list(set(current[k] + v))
                else:
                    current[k] = v
                    
            user.profile_data = current
            
            # --- SYNC SPECIFIC COLUMNS ---
            # Also save email/phone to main columns for easier access
            if "email" in psychographics_update and psychographics_update["email"]:
                user.email = psychographics_update["email"]
                
            if "phone" in psychographics_update and psychographics_update["phone"]:
                user.phone = psychographics_update["phone"]
                
            if "name" in psychographics_update and psychographics_update["name"]:
                 # Optional: Update full_name if provided and currently generic?
                 # user.full_name = psychographics_update["name"] 
                 pass

            self.db.commit()
            self.db.refresh(user)
        return user

    # --- Product & Journey ---
    def get_current_launch_product(self, type_filter="program") -> Tuple[Optional[Product], Optional[str]]:
        """
        Smart selection based on Date Windows (High Ticket Strategy).
        Returns tuple: (product, launch_stage)
        launch_stage: pre_launch, open_cart, close_cart, evergreen
        """
        now = datetime.datetime.now()
        products = self.db.query(Product).filter(
            Product.status == "active",
            Product.type == type_filter
        ).all()
        
        valid_candidates = []
        
        for p in products:
            dates = p.dates or {}
            start_str = dates.get("start")
            deadline_str = dates.get("offer_deadline")
            
            # 1. Evergreen (No dates)
            if not start_str:
                valid_candidates.append({
                    "product": p,
                    "stage": ProductLaunchStage.EVERGREEN.value,
                    "priority": 1 # Lowest priority
                })
                continue
            
            try:
                # Parse dates (Handling YYYY-MM-DD)
                # Ensure we compare with naive or aware correctly. Assuming naive for simplicity or local time.
                start_date = datetime.datetime.strptime(start_str, "%Y-%m-%d")
                # If deadline missing, assume evergreen from start
                deadline_date = datetime.datetime.strptime(deadline_str, "%Y-%m-%d") if deadline_str else None
                
                # 2. Pre-Launch (Before Start)
                if now < start_date:
                    # Only relevant if within 60 days of start (Expanded for early sales)
                    days_to_start = (start_date - now).days
                    if days_to_start <= 60:
                        valid_candidates.append({
                            "product": p,
                            "stage": ProductLaunchStage.PRE_LAUNCH.value,
                            "priority": 50 - days_to_start # Higher priority as it gets closer
                        })
                
                # 3. Open Cart (Between Start and Deadline)
                elif deadline_date and start_date <= now <= deadline_date:
                    hours_left = (deadline_date - now).total_seconds() / 3600
                    stage = ProductLaunchStage.CLOSE_CART.value if hours_left < 48 else ProductLaunchStage.OPEN_CART.value
                    # Highest priority: Active Cart
                    # Urgency bonus: Less time left = Higher priority
                    valid_candidates.append({
                        "product": p,
                        "stage": stage,
                        "priority": 100 + (10000 / (hours_left + 1)) 
                    })
                    
                # 4. Evergreen (Started, no deadline)
                elif not deadline_date and now >= start_date:
                    valid_candidates.append({
                        "product": p,
                        "stage": ProductLaunchStage.EVERGREEN.value,
                        "priority": 10
                    })
                    
            except ValueError:
                logger.warning(f"Invalid date format for product {p.name}")
                continue

        if not valid_candidates:
            return None, None
            
        # Sort by priority desc
        best_match = sorted(valid_candidates, key=lambda x: x["priority"], reverse=True)[0]
        return best_match["product"], best_match["stage"]

    def get_active_product(self, type="program") -> Optional[Product]:
        # Returns the first active product of the given type
        # Legacy Wrapper
        p, _ = self.get_current_launch_product(type)
        return p

    def get_enrollment(self, user_id, product_id) -> Optional[Enrollment]:
        return self.db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.product_id == product_id
        ).first()

    def update_enrollment(self, user_id, product_id, status=None, stage=None, lead_score_inc=0) -> Enrollment:
        enrollment = self.get_enrollment(user_id, product_id)
        if not enrollment:
            enrollment = Enrollment(user_id=user_id, product_id=product_id)
            self.db.add(enrollment)
        
        if status:
            enrollment.status = status
        if stage:
            enrollment.stage = stage
        if lead_score_inc:
            enrollment.lead_score = min(100, (enrollment.lead_score or 0) + lead_score_inc)
            
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment

    def persist_agent_state(self, user_id, state: dict, product_id=None):
        """
        Centralized logic to map AgentState -> DB Models.
        Updates User Profile and Enrollment Status/Stage/Score.
        """
        # 1. Update Profile (Psychographics)
        if state.get("user_profile"):
            self.update_user_profile(user_id, state["user_profile"])
            
        # 2. Update Enrollment (Funnel State)
        # Priority: State product_id (dynamic context) > Argument product_id (initial context)
        target_product_id = state.get("product_id") or product_id
        
        if target_product_id:
            enrollment = self.get_enrollment(user_id, target_product_id)
            if not enrollment:
                enrollment = Enrollment(user_id=user_id, product_id=target_product_id)
                self.db.add(enrollment)
            
            # Map AgentState fields to Enrollment columns
            
            # current_state -> stage
            if state.get("current_state"):
                enrollment.stage = state["current_state"]
                
            # lead_score -> lead_score (Direct set, not increment)
            if state.get("lead_score") is not None:
                enrollment.lead_score = state["lead_score"]
                
            # Disqualification Handling
            if state.get("disqualification_reason"):
                enrollment.status = LeadStatus.DISQUALIFIED.value
                # Add reason to objections list if not present
                reason = f"Disqualified: {state['disqualification_reason']}"
                # Ensure objections is a list
                current_objections = list(enrollment.objections) if enrollment.objections else []
                if reason not in current_objections:
                    current_objections.append(reason)
                    enrollment.objections = current_objections
            
            # Derived Status Logic (only if not disqualified)
            elif enrollment.status != LeadStatus.DISQUALIFIED.value: 
                current = state.get("current_state")
                if current in [FunnelStage.RAPPORT.value, FunnelStage.DISCOVERY.value]:
                    if enrollment.status == LeadStatus.AWARENESS.value:
                        enrollment.status = LeadStatus.QUALIFIED.value # Moved past initial check
                elif current in [FunnelStage.GAP.value, FunnelStage.PITCH.value]:
                    enrollment.status = LeadStatus.QUALIFIED.value
                elif current in [FunnelStage.ANCHORING.value, FunnelStage.CLOSING.value]:
                    enrollment.status = LeadStatus.NEGOTIATION.value
            
            self.db.commit()
            self.db.refresh(enrollment)

    # --- Logging ---
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
        except SQLAlchemyError as e:
            logger.error(f"Error logging message to DB: {e}")
            self.db.rollback()

    def get_last_message(self, user_id) -> Optional[Message]:
        """
        Retrieves the last message from the user.
        """
        return self.db.query(Message).filter(
            Message.user_id == user_id,
            Message.role == "user"
        ).order_by(desc(Message.created_at)).first()

    def get_chat_history(self, user_id, limit=20) -> List[Dict[str, str]]:
        """
        Retrieves chat history formatted for Agent State.
        Returns: [{"role": "user", "content": "..."}, ...]
        Sorted Chronologically (Oldest -> Newest).
        """
        messages = self.db.query(Message).filter(
            Message.user_id == user_id
        ).order_by(desc(Message.created_at)).limit(limit).all()
        
        # Sort back to chronological order
        messages.reverse()
        
        history = []
        for m in messages:
            history.append({
                "role": m.role,
                "content": m.content
            })
        return history

    def get_recent_users(self, limit=20) -> List[Any]:
        """
        Fetches users ordered by their most recent message activity.
        Useful for the Admin Dashboard to pick a user to audit.
        """
        # Subquery to find last message date per user
        subquery = self.db.query(
            Message.user_id,
            func.max(Message.created_at).label("last_activity")
        ).group_by(Message.user_id).subquery()
        
        # Join User with Subquery
        results = self.db.query(User, subquery.c.last_activity)\
            .join(subquery, User.id == subquery.c.user_id)\
            .order_by(desc(subquery.c.last_activity))\
            .limit(limit)\
            .all()
            
        return results

    # --- Conversion ---
    def create_appointment(self, user_id, product_id, scheduled_at, link=None) -> Appointment:
        appt = Appointment(
            user_id=user_id,
            product_id=product_id,
            scheduled_at=scheduled_at,
            meeting_link=link
        )
        self.db.add(appt)
        self.db.commit()
        return appt

    # --- Observability / Tracing ---
    def create_trace(self, user_id, session_id, node_name, input_state, output_state, execution_time_ms) -> Optional[AgentTrace]:
        """
        Logs a high-level node execution trace.
        """
        from src.services.models import AgentTrace
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
        except SQLAlchemyError as e:
            logger.error(f"Error creating trace: {e}")
            self.db.rollback()
            return None

    def create_llm_log(self, trace_id, model, prompt_template, prompt_rendered, response_text, tokens_input=0, tokens_output=0, metadata=None) -> Optional[LLMCallLog]:
        """
        Logs a low-level LLM call associated with a trace.
        """
        from src.services.models import LLMCallLog
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
        except SQLAlchemyError as e:
            logger.error(f"Error creating LLM log: {e}")
            self.db.rollback()
            return None
