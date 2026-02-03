from typing import Optional, Tuple
from src.services.db.models.business import Product, JourneyProgress
from src.core.domain.schema import FunnelStage, LeadStatus, ProductLaunchStage
from .base import BaseRepository
import datetime
import logging

logger = logging.getLogger(__name__)

class BusinessRepository(BaseRepository):
    def get_current_launch_product(self, type_filter="program") -> Tuple[Optional[Product], Optional[str]]:
        """
        Smart selection based on Date Windows (High Ticket Strategy).
        Returns tuple: (product, launch_stage)
        """
        now = datetime.datetime.now()
        query = self.db.query(Product).filter(
            Product.status == "active",
            Product.type == type_filter
        )
        query = self._apply_tenant_filter(query, Product)
        products = query.all()
        
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
                start_date = datetime.datetime.strptime(start_str, "%Y-%m-%d")
                deadline_date = datetime.datetime.strptime(deadline_str, "%Y-%m-%d") if deadline_str else None
                
                # 2. Pre-Launch (Before Start)
                if now < start_date:
                    days_to_start = (start_date - now).days
                    if days_to_start <= 60:
                        valid_candidates.append({
                            "product": p,
                            "stage": ProductLaunchStage.PRE_LAUNCH.value,
                            "priority": 50 - days_to_start
                        })
                
                # 3. Open Cart (Between Start and Deadline)
                elif deadline_date and start_date <= now <= deadline_date:
                    hours_left = (deadline_date - now).total_seconds() / 3600
                    stage = ProductLaunchStage.CLOSE_CART.value if hours_left < 48 else ProductLaunchStage.OPEN_CART.value
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
            
        best_match = sorted(valid_candidates, key=lambda x: x["priority"], reverse=True)[0]
        return best_match["product"], best_match["stage"]

    def get_journey(self, user_id, product_id) -> Optional[JourneyProgress]:
        query = self.db.query(JourneyProgress).filter(
            JourneyProgress.lead_id == user_id,
            JourneyProgress.product_id == product_id
        )
        query = self._apply_tenant_filter(query, JourneyProgress)
        return query.first()

    def update_journey(self, user_id, product_id, status=None, stage=None, lead_score_inc=0) -> JourneyProgress:
        journey = self.get_journey(user_id, product_id)
        if not journey:
            journey = JourneyProgress(lead_id=user_id, product_id=product_id)
            self._set_tenant(journey)
            self.db.add(journey)
        
        if status:
            journey.status = status
        if stage:
            journey.stage = stage
        if lead_score_inc:
            journey.lead_score = min(100, (journey.lead_score or 0) + lead_score_inc)
            
        self.db.commit()
        self.db.refresh(journey)
        return journey

    def persist_agent_state(self, user_id, state: dict, product_id=None):
        """
        Centralized logic to map AgentState -> DB Models.
        Updates JourneyProgress Status/Stage/Score.
        Note: Profile update should be done via UserRepository.
        """
        # Journey Updates
        target_product_id = state.get("product_id") or product_id
        
        if target_product_id:
            journey = self.get_journey(user_id, target_product_id)
            if not journey:
                journey = JourneyProgress(lead_id=user_id, product_id=target_product_id)
                self._set_tenant(journey)
                self.db.add(journey)
            
            if state.get("current_state"):
                journey.stage = state["current_state"]
                
            if state.get("lead_score") is not None:
                journey.lead_score = state["lead_score"]
                
            if state.get("disqualification_reason"):
                journey.status = LeadStatus.DISQUALIFIED.value
                reason = f"Disqualified: {state['disqualification_reason']}"
                # Store in historical objections
                current_objections = list(journey.objections) if journey.objections else []
                if reason not in current_objections:
                    current_objections.append(reason)
                    journey.objections = current_objections
                # Also set current blocker
                journey.objection_status = "Disqualified"
            
            elif journey.status != LeadStatus.DISQUALIFIED.value: 
                current = state.get("current_state")
                if current in [FunnelStage.RAPPORT.value, FunnelStage.DISCOVERY.value]:
                    if journey.status == LeadStatus.AWARENESS.value:
                        journey.status = LeadStatus.QUALIFIED.value
                elif current in [FunnelStage.GAP.value, FunnelStage.PITCH.value]:
                    journey.status = LeadStatus.QUALIFIED.value
                elif current in [FunnelStage.ANCHORING.value, FunnelStage.CLOSING.value]:
                    journey.status = LeadStatus.NEGOTIATION.value
            
            self.db.commit()
            self.db.refresh(journey)
