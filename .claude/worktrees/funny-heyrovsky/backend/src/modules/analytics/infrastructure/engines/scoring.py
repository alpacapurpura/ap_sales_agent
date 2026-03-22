from uuid import UUID
from sqlalchemy.orm import Session
from src.modules.crm.infrastructure.repositories.customer_repository import JourneyEventRepository

class LeadScoringEngine:
    # Definición básica de puntajes por tipo de evento
    # Esto idealmente debería ser configurable por Tenant
    EVENT_SCORES = {
        "page_view": 1,
        "email_opened": 2,
        "link_clicked": 3,
        "form_submitted": 5,
        "resource_downloaded": 10,
        "webinar_registered": 15,
        "webinar_attended": 20,
        "demo_requested": 50,
        "order_placed": 100,
        "purchase": 100
    }

    def __init__(self, db: Session):
        self.repository = JourneyEventRepository(db)

    def calculate_score(self, profile_id: UUID) -> int:
        """
        Calcula el puntaje de lead basado en el historial de eventos.
        
        Args:
            profile_id: ID del perfil del cliente
            
        Returns:
            Puntaje total calculado.
        """
        # 1. Obtener todos los eventos del perfil
        events = self.repository.get_timeline(profile_id)
        
        total_score = 0
        
        # 2. Iterar y sumar puntajes
        for event in events:
            # Usar el tipo de evento para buscar el puntaje, default 0
            score = self.EVENT_SCORES.get(event.event_type, 0)
            total_score += score
            
        return total_score
