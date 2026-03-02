from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.crm.infrastructure.repositories.lead_repository import LeadRepository
# from src.modules.scheduling.infrastructure.repositories.appointment_repository import AppointmentRepository
from src.modules.scheduling.infrastructure.models.appointment_model import AppointmentModel
from datetime import datetime, timedelta

router = APIRouter(tags=["Sales Dashboard"])

@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get high-level sales statistics for the dashboard.
    """
    # 1. Total Sales (Mock for now, needs Order module)
    total_sales = 0.0
    
    # 2. Appointments Today/Total
    # We don't have AppointmentRepository imported yet, let's check if it exists or mock it
    # Assuming we can count appointments via a repository or direct query
    # For now, let's mock the count based on Lead activity or just return 0 if no repo ready
    
    # 3. Active Leads
    lead_repo = LeadRepository(db)
    # Assuming we can filter by tenant
    # Using a direct count query would be more efficient, but let's use what we have
    # We need to implement count methods in LeadRepository ideally
    
    # Quick fix: Count all leads for tenant
    # This is inefficient for large datasets but works for MVP
    # leads = lead_repo.get_all(user.tenant_id) -> Not implemented yet
    
    # Let's use a direct query for speed in this specific endpoint
    from src.modules.crm.infrastructure.models.lead_model import LeadModel
    active_leads_count = db.query(LeadModel).filter(
        LeadModel.tenant_id == user.tenant_id,
        LeadModel.is_blacklisted == False
    ).count()
    
    # 4. Conversion Rate (Mock)
    conversion_rate = 0.0
    
    return {
        "total_sales": total_sales,
        "appointments_today": 0, # Placeholder until we connect Scheduling module
        "conversion_rate": conversion_rate,
        "active_leads": active_leads_count
    }

@router.get("/activity")
async def get_recent_activity(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get recent activity feed (Leads created, Appointments booked, etc.)
    """
    # Fetch recent leads
    from src.modules.crm.infrastructure.models.lead_model import LeadModel
    
    recent_leads = db.query(LeadModel).filter(
        LeadModel.tenant_id == user.tenant_id
    ).order_by(LeadModel.created_at.desc()).limit(5).all()
    
    activities = []
    
    for lead in recent_leads:
        # Check profile data for name
        name = "Nuevo Lead"
        if lead.profile_data and isinstance(lead.profile_data, dict):
            name = lead.profile_data.get("name", "Nuevo Lead")
            
        activities.append({
            "id": str(lead.id),
            "type": "lead",
            "title": f"Nuevo Lead: {name}",
            "description": "Se ha registrado un nuevo lead en el sistema.",
            "timestamp": lead.created_at.isoformat() if lead.created_at else datetime.now().isoformat(),
            "amount": None
        })
        
    # TODO: Merge with appointments and sales
    
    return activities
