from typing import Dict
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from src.modules.crm.infrastructure.repositories.customer_repository import JourneyEventRepository

class RFMCalculationEngine:
    def __init__(self, db: Session):
        self.repository = JourneyEventRepository(db)

    def calculate_rfm(self, profile_id: UUID) -> Dict[str, float]:
        """
        Calcula las métricas RFM (Recencia, Frecuencia, Valor Monetario)
        para un perfil de cliente dado.
        
        Args:
            profile_id: ID del perfil del cliente
            
        Returns:
            Diccionario con claves: recency, frequency, monetary
        """
        # 1. Obtener todos los eventos para filtrar por compras
        events = self.repository.get_timeline(profile_id)
        
        # Filtrar solo eventos de compra/orden
        purchase_events = [
            e for e in events 
            if e.event_type in ("order_placed", "purchase")
        ]
        
        if not purchase_events:
            return {
                "recency": -1.0, # Valor sentinel para indicar que no hay compras
                "frequency": 0.0,
                "monetary": 0.0
            }
            
        # 2. Calcular Frecuencia (número total de compras)
        frequency = len(purchase_events)
        
        # 3. Calcular Valor Monetario (suma total de compras)
        # Asumimos que el valor viene en properties como 'total_price' o 'amount'
        monetary = sum(
            float(event.properties.get("total_price", event.properties.get("amount", 0.0)))
            for event in purchase_events
        )
        
        # 4. Calcular Recencia (días desde la última compra)
        # Los eventos ya vienen ordenados descendente por fecha (más reciente primero)
        last_purchase_date = purchase_events[0].occurred_at
        
        # Asegurar zona horaria UTC para la comparación
        now = datetime.now(timezone.utc)
        
        # Si last_purchase_date no tiene tzinfo, asumimos UTC
        if last_purchase_date.tzinfo is None:
            last_purchase_date = last_purchase_date.replace(tzinfo=timezone.utc)
            
        recency_delta = now - last_purchase_date
        recency_days = max(0.0, recency_delta.total_seconds() / 86400.0) # Convertir a días
        
        return {
            "recency": round(recency_days, 2),
            "frequency": float(frequency),
            "monetary": float(monetary)
        }
