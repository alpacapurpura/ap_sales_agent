from uuid import UUID
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.modules.marketing.infrastructure.repositories.customer_repository import JourneyEventRepository, CustomerRepository
from src.modules.sales.infrastructure.lead import LeadRepository
from src.modules.marketing.infrastructure.models.customer import LifecycleStage

class MetricsService:
    def __init__(self, db: Session):
        self.journey_repo = JourneyEventRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.lead_repo = LeadRepository(db)

    def get_marketing_sankey_metrics(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Obtiene métricas para el diagrama de Sankey de marketing (7 nodos).
        
        Nodos:
        0: Adquisition (Visitors)
        1: Activation (Leads)
        2: Consideration (Qualified Leads)
        3: Decision (Opportunities)
        4: Conversion (Customers)
        5: Retention (Loyal Customers)
        6: Advocacy (Evangelists)
        """
        
        # 1. Visitors (Adquisition)
        visitors = self.journey_repo.get_unique_visitors(tenant_id)
        
        # 2. Leads (Activation)
        leads = self.lead_repo.count_total(tenant_id)
        
        # 3. Qualified (Consideration)
        qualified_leads = self.lead_repo.count_qualified(tenant_id)
        mql_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.MQL)
        qualified = max(qualified_leads, mql_count)
        
        # 4. Opportunities (Decision)
        sql_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.SQL)
        opp_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.OPPORTUNITY)
        opportunities = sql_count + opp_count
        
        # 5. Customers (Conversion)
        customers = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.CUSTOMER)
        
        # 6. Loyal Customers (Retention)
        # Placeholder heuristic: 40% of customers are retained/loyal
        retention = int(customers * 0.4)
        
        # 7. Evangelists (Advocacy)
        evangelists = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.EVANGELIST)
        
        # Ensure logical flow consistency for visualization (optional but good for Sankey)
        # We won't force-clamp to avoid hiding data issues, but we'll use these values for links.

        nodes = [
            {"name": "Adquisition"},
            {"name": "Activation"},
            {"name": "Consideration"},
            {"name": "Decision"},
            {"name": "Conversion"},
            {"name": "Retention"},
            {"name": "Advocacy"}
        ]
        
        links = [
            {"source": 0, "target": 1, "value": leads},
            {"source": 1, "target": 2, "value": qualified},
            {"source": 2, "target": 3, "value": opportunities},
            {"source": 3, "target": 4, "value": customers},
            {"source": 4, "target": 5, "value": retention},
            {"source": 5, "target": 6, "value": evangelists}
        ]
        
        return {
            "nodes": nodes,
            "links": links,
            "raw_metrics": {
                "visitors": visitors,
                "leads": leads,
                "qualified": qualified,
                "opportunities": opportunities,
                "customers": customers,
                "retention": retention,
                "evangelists": evangelists
            }
        }
