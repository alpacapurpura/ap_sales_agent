"""Seed script: Calendario Comercial Perú 2026.

Upsert idempotente: no inserta si ya existe (country_code, date, name, tenant_id IS NULL).
Ejecutar:
    docker exec -t visionarias_brain_dev bash -c "cd /app && python scripts/seed_commercial_calendar_peru_2026.py"
"""

import os
import sys
from datetime import date, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uuid

import src.shared.infrastructure.model_registry  # noqa: F401
from src.core.database import SessionLocal
from src.modules.commercial_calendar.domain.calendar_event import CalendarEvent
from src.modules.commercial_calendar.domain.enums import EventCategory
from src.modules.commercial_calendar.infrastructure.repositories.calendar_event_repository import (
    CalendarEventRepository,
)

COUNTRY_CODE = "PE"

# ─────────────────────────────────────────────────────────────────────────────
# Definición de eventos (rangos). start y end son fechas inclusive.
# ─────────────────────────────────────────────────────────────────────────────
RAW_EVENTS = [
    # ── FERIADOS NACIONALES ──────────────────────────────────────────────────
    {
        "name": "Año Nuevo",
        "category": EventCategory.FERIADO,
        "start": date(2026, 1, 1),
        "end": None,
        "description": "Feriado nacional",
    },
    {
        "name": "Carnaval",
        "category": EventCategory.FERIADO,
        "start": date(2026, 2, 16),
        "end": date(2026, 2, 17),
        "description": "Feriado regional extendido",
    },
    {
        "name": "Semana Santa",
        "category": EventCategory.FERIADO,
        "start": date(2026, 4, 2),
        "end": date(2026, 4, 5),
        "description": "Jueves y Viernes Santo + puente",
    },
    {
        "name": "Día del Trabajo",
        "category": EventCategory.FERIADO,
        "start": date(2026, 5, 1),
        "end": None,
        "description": "Feriado nacional",
    },
    {
        "name": "San Pedro y San Pablo",
        "category": EventCategory.FERIADO,
        "start": date(2026, 6, 29),
        "end": None,
        "description": "Feriado nacional",
    },
    {
        "name": "Fiestas Patrias",
        "category": EventCategory.FERIADO,
        "start": date(2026, 7, 28),
        "end": date(2026, 7, 29),
        "description": "Independencia del Perú",
    },
    {
        "name": "Santa Rosa de Lima",
        "category": EventCategory.FERIADO,
        "start": date(2026, 8, 30),
        "end": None,
        "description": "Feriado nacional",
    },
    {
        "name": "Combate de Angamos",
        "category": EventCategory.FERIADO,
        "start": date(2026, 10, 8),
        "end": None,
        "description": "Feriado nacional",
    },
    {
        "name": "Todos los Santos",
        "category": EventCategory.FERIADO,
        "start": date(2026, 11, 1),
        "end": None,
        "description": "Feriado nacional",
    },
    {
        "name": "Inmaculada Concepción",
        "category": EventCategory.FERIADO,
        "start": date(2026, 12, 8),
        "end": None,
        "description": "Feriado nacional",
    },
    {
        "name": "Navidad",
        "category": EventCategory.FERIADO,
        "start": date(2026, 12, 25),
        "end": None,
        "description": "Feriado nacional",
    },
    # ── CAMPAÑAS COMERCIALES ─────────────────────────────────────────────────
    {
        "name": "San Valentín",
        "category": EventCategory.CAMPANA,
        "start": date(2026, 2, 14),
        "end": None,
        "description": "Día del amor y la amistad",
    },
    {
        "name": "Día de la Mujer",
        "category": EventCategory.DIA_ESPECIAL,
        "start": date(2026, 3, 8),
        "end": None,
        "description": "Día Internacional de la Mujer",
    },
    {
        "name": "Día de la Madre",
        "category": EventCategory.CAMPANA,
        "start": date(2026, 5, 10),
        "end": None,
        "description": "Segunda semana de mayo",
    },
    {
        "name": "Día del Padre",
        "category": EventCategory.CAMPANA,
        "start": date(2026, 6, 21),
        "end": None,
        "description": "Tercer domingo de junio",
    },
    {
        "name": "Día del Maestro",
        "category": EventCategory.DIA_ESPECIAL,
        "start": date(2026, 7, 6),
        "end": None,
        "description": "Feriado para docentes",
    },
    {
        "name": "Halloween",
        "category": EventCategory.CAMPANA,
        "start": date(2026, 10, 31),
        "end": None,
        "description": "Campaña previa a Todos los Santos",
    },
    {
        "name": "Campaña Navidad",
        "category": EventCategory.CAMPANA,
        "start": date(2026, 12, 1),
        "end": date(2026, 12, 24),
        "description": "Temporada alta de compras navideñas",
    },
    {
        "name": "Campaña Año Nuevo",
        "category": EventCategory.CAMPANA,
        "start": date(2026, 12, 26),
        "end": date(2026, 12, 31),
        "description": "Preparación para Año Nuevo",
    },
    # ── CYBER EVENTS ─────────────────────────────────────────────────────────
    {
        "name": "Cyber WOW Abril",
        "category": EventCategory.CYBER,
        "start": date(2026, 4, 13),
        "end": date(2026, 4, 17),
        "description": "Cyber WOW Q2 — Saga Falabella, Ripley, etc.",
    },
    {
        "name": "Cyber Days Abril",
        "category": EventCategory.CYBER,
        "start": date(2026, 4, 20),
        "end": date(2026, 4, 22),
        "description": "Cyber Days Q2 — CACE",
    },
    {
        "name": "Cyber WOW Julio",
        "category": EventCategory.CYBER,
        "start": date(2026, 7, 6),
        "end": date(2026, 7, 10),
        "description": "Cyber WOW Q3",
    },
    {
        "name": "Cyber Days Julio",
        "category": EventCategory.CYBER,
        "start": date(2026, 7, 20),
        "end": date(2026, 7, 22),
        "description": "Cyber Days Q3",
    },
    {
        "name": "Cyber WOW Octubre",
        "category": EventCategory.CYBER,
        "start": date(2026, 10, 19),
        "end": date(2026, 10, 23),
        "description": "Cyber WOW Q4",
    },
    {
        "name": "Cyber Days Octubre",
        "category": EventCategory.CYBER,
        "start": date(2026, 10, 26),
        "end": date(2026, 10, 29),
        "description": "Cyber Days Q4",
    },
    {
        "name": "Cyber Days Noviembre",
        "category": EventCategory.CYBER,
        "start": date(2026, 11, 9),
        "end": date(2026, 11, 11),
        "description": "Cyber Days pre Black Friday",
    },
    {
        "name": "Black Friday",
        "category": EventCategory.CYBER,
        "start": date(2026, 11, 27),
        "end": None,
        "description": "Black Friday",
    },
    {
        "name": "Cyber Monday",
        "category": EventCategory.CYBER,
        "start": date(2026, 11, 30),
        "end": None,
        "description": "Cyber Monday",
    },
    # ── SALES / TEMPORADAS ───────────────────────────────────────────────────
    {
        "name": "Sale Verano",
        "category": EventCategory.SALE,
        "start": date(2026, 3, 23),
        "end": date(2026, 3, 31),
        "description": "Rebajas de fin de temporada verano",
    },
    {
        "name": "Sale Otoño",
        "category": EventCategory.SALE,
        "start": date(2026, 6, 22),
        "end": date(2026, 6, 28),
        "description": "Rebajas de fin de temporada otoño",
    },
    {
        "name": "Sale Invierno",
        "category": EventCategory.SALE,
        "start": date(2026, 8, 24),
        "end": date(2026, 9, 6),
        "description": "Rebajas de fin de temporada invierno",
    },
    {
        "name": "Sale Primavera",
        "category": EventCategory.SALE,
        "start": date(2026, 11, 16),
        "end": date(2026, 11, 22),
        "description": "Rebajas de fin de temporada primavera",
    },
    # ── TEMPORADAS ───────────────────────────────────────────────────────────
    {
        "name": "Temporada Escolar",
        "category": EventCategory.TEMPORADA,
        "start": date(2026, 2, 1),
        "end": date(2026, 3, 15),
        "description": "Regreso a clases — útiles, mochilas, laptops",
    },
    {
        "name": "Temporada Universitaria",
        "category": EventCategory.TEMPORADA,
        "start": date(2026, 3, 16),
        "end": date(2026, 4, 10),
        "description": "Inicio ciclo universitario",
    },
    {
        "name": "Temporada Verano",
        "category": EventCategory.TEMPORADA,
        "start": date(2026, 1, 1),
        "end": date(2026, 3, 22),
        "description": "Temporada de verano en la costa",
    },
    # ── DÍAS ESPECIALES / CULTURALES ─────────────────────────────────────────
    {
        "name": "Día del Emprendimiento",
        "category": EventCategory.DIA_ESPECIAL,
        "start": date(2026, 4, 16),
        "end": None,
        "description": "Día del emprendedor peruano",
    },
    {
        "name": "Inti Raymi",
        "category": EventCategory.CULTURAL,
        "start": date(2026, 6, 24),
        "end": None,
        "description": "Fiesta del Sol — Cusco",
    },
    {
        "name": "Día del Libro",
        "category": EventCategory.DIA_ESPECIAL,
        "start": date(2026, 4, 23),
        "end": None,
        "description": "Día Mundial del Libro",
    },
    {
        "name": "Día del Niño",
        "category": EventCategory.CAMPANA,
        "start": date(2026, 8, 17),
        "end": None,
        "description": "Campaña infantil en Perú",
    },
    {
        "name": "Día de la Educación",
        "category": EventCategory.DIA_ESPECIAL,
        "start": date(2026, 11, 17),
        "end": None,
        "description": "Día mundial de la educación UNESCO",
    },
    # ── ELECCIONES ───────────────────────────────────────────────────────────
    {
        "name": "Elecciones Generales",
        "category": EventCategory.ELECCIONES,
        "start": date(2026, 4, 5),
        "end": None,
        "description": "Primera vuelta elecciones presidenciales 2026",
    },
    {
        "name": "Segunda Vuelta Electoral",
        "category": EventCategory.ELECCIONES,
        "start": date(2026, 6, 7),
        "end": None,
        "description": "Segunda vuelta elecciones presidenciales 2026",
    },
]


def expand_events():
    """Expand range events into one row per day."""
    rows = []
    for ev in RAW_EVENTS:
        start: date = ev["start"]
        end: date = ev["end"] if ev["end"] else start
        current = start
        while current <= end:
            iso = current.isocalendar()
            rows.append(
                {
                    "country_code": COUNTRY_CODE,
                    "date": current,
                    "year": current.year,
                    "week_number": iso[1],
                    "name": ev["name"],
                    "category": ev["category"].value if ev["category"] else None,
                    "description": ev.get("description"),
                }
            )
            current += timedelta(days=1)
    return rows


def main():
    db = SessionLocal()
    try:
        repo = CalendarEventRepository(db)
        rows = expand_events()
        inserted = 0
        skipped = 0
        for row in rows:
            if repo.exists(row["country_code"], row["date"], row["name"], tenant_id=None):
                skipped += 1
                continue
            entity = CalendarEvent(
                id=uuid.uuid4(),
                tenant_id=None,
                country_code=row["country_code"],
                date=row["date"],
                year=row["year"],
                week_number=row["week_number"],
                name=row["name"],
                category=row["category"],
                description=row["description"],
            )
            repo.create(entity)
            inserted += 1

        print(f"✅ Seed completo: {inserted} filas insertadas, {skipped} ya existían.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
