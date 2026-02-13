from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import uuid

from src.services.db.models.lead import Lead
from src.services.db.models.business import Appointment, JourneyProgress
from src.core.domain.dashboard_schema import DashboardResponse, DashboardMetrics, ActionItem, AgendaItem, FunnelStage

class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(self, tenant_id: uuid.UUID) -> DashboardResponse:
        """
        Aggregates data to provide a high-level view of the business.
        """
        metrics = self._get_metrics(tenant_id)
        action_items = self._get_action_items(tenant_id)
        agenda = self._get_agenda(tenant_id)
        funnel = self._get_funnel(tenant_id)

        return DashboardResponse(
            metrics=metrics,
            action_items=action_items,
            agenda=agenda,
            funnel=funnel
        )

    def _get_metrics(self, tenant_id: uuid.UUID) -> DashboardMetrics:
        # Calculate Pipeline Value (Sum of deal_value_potential for active journeys)
        pipeline_value_result = self.db.query(func.sum(JourneyProgress.deal_value_potential))\
            .filter(JourneyProgress.tenant_id == tenant_id)\
            .filter(JourneyProgress.stage.notin_(['CLOSED_LOST', 'ARCHIVED']))\
            .scalar()
        
        pipeline_value = float(pipeline_value_result or 0.0)

        # Active Leads (Leads with recent interaction or active journey)
        active_leads_count = self.db.query(func.count(Lead.id))\
            .filter(Lead.tenant_id == tenant_id)\
            .filter(Lead.last_interaction_date >= datetime.utcnow() - timedelta(days=7))\
            .scalar() or 0

        # Conversion Rate (Bookings / Total Leads) * 100
        total_leads = self.db.query(func.count(Lead.id)).filter(Lead.tenant_id == tenant_id).scalar() or 1
        total_bookings = self.db.query(func.count(Appointment.id)).filter(Appointment.tenant_id == tenant_id).scalar() or 0
        
        conversion_rate = (total_bookings / total_leads) * 100 if total_leads > 0 else 0.0

        return DashboardMetrics(
            pipeline_value=pipeline_value,
            active_leads_count=active_leads_count,
            conversion_rate=round(conversion_rate, 2)
        )

    def _get_action_items(self, tenant_id: uuid.UUID) -> List[ActionItem]:
        items = []
        
        # 1. Intervention Needed (Leads asking for human)
        # Assuming we might filter by a specific tag or status. 
        # For now, let's look for leads with 'HUMAN_REQUESTED' in custom tags or similar.
        # Since 'status' isn't explicit on Lead, we check if there's a way to identify this.
        # We'll use a placeholder logic: Leads with low fit_score but high intent might need check.
        # OR better: Check for 'human_handoff' in journey status if it exists.
        
        # Real implementation would likely check a specific 'needs_attention' flag on Lead or Journey.
        # For this abstraction, we will query leads with a specific recent objection or stagnation.
        
        # Example: Leads with > 3 objections in history
        complex_leads = self.db.query(Lead).filter(Lead.tenant_id == tenant_id)\
            .filter(func.jsonb_array_length(Lead.key_objections_history) > 2)\
            .limit(3).all()

        for lead in complex_leads:
            items.append(ActionItem(
                id=str(uuid.uuid4()),
                type="INTERVENTION",
                priority="HIGH",
                title=f"Objeciones Múltiples: {lead.full_name or 'Lead'}",
                description="El lead ha presentado múltiples objeciones. Revisa la conversación.",
                link=f"/audit?lead_id={lead.id}",
                timestamp=datetime.utcnow().isoformat()
            ))

        return items

    def _get_agenda(self, tenant_id: uuid.UUID) -> List[AgendaItem]:
        # Get appointments for today and tomorrow
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0)
        end_date = start_date + timedelta(days=2)
        
        appointments = self.db.query(Appointment).filter(Appointment.tenant_id == tenant_id)\
            .filter(Appointment.scheduled_at >= start_date)\
            .filter(Appointment.scheduled_at < end_date)\
            .order_by(Appointment.scheduled_at.asc())\
            .limit(5).all()
            
        agenda_items = []
        for apt in appointments:
            lead_name = apt.lead.full_name if apt.lead else "Unknown Lead"
            agenda_items.append(AgendaItem(
                id=str(apt.id),
                title="Sesión de Venta",
                start_time=apt.scheduled_at.isoformat(),
                attendee_name=lead_name,
                status=apt.status or "scheduled"
            ))
            
        return agenda_items

    def _get_funnel(self, tenant_id: uuid.UUID) -> List[FunnelStage]:
        # Simple funnel based on Journey Stages
        # We group by stage and count
        
        stages = ["NEW_LEAD", "ENGAGED", "QUALIFIED", "PROPOSAL", "WON"]
        funnel_data = []
        
        for stage in stages:
            count = self.db.query(func.count(JourneyProgress.id))\
                .filter(JourneyProgress.tenant_id == tenant_id)\
                .filter(JourneyProgress.stage == stage)\
                .scalar() or 0
            
            funnel_data.append(FunnelStage(
                stage=stage,
                count=count,
                value=0 # Could calculate sum of value per stage
            ))
            
        return funnel_data
