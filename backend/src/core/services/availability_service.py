import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from src.services.db.models.channel_connection import ChannelConnection
from src.services.db.models.tenant import Tenant
from src.channels.google_calendar import GoogleCalendarAdapter
from src.config import settings
from src.core.domain.availability_schema import AvailabilitySchedule, WeeklySchedule, DaySchedule, TimeRange, ScheduleUpdate
from src.core.domain.event_type_schema import EventType
import uuid
import logging

logger = logging.getLogger(__name__)

class AvailabilityService:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.adapter = self._get_adapter()

    def _get_adapter(self) -> Optional[GoogleCalendarAdapter]:
        stmt = select(ChannelConnection).where(
            ChannelConnection.tenant_id == self.tenant_id,
            ChannelConnection.channel_type == 'google_calendar',
            ChannelConnection.is_active == True
        )
        connection = self.db.execute(stmt).scalar_one_or_none()
        
        if not connection or not connection.credentials:
            return None
            
        return GoogleCalendarAdapter(credentials_data=connection.credentials)

    def is_connected(self) -> bool:
        return self.adapter is not None

    # --- Schedule Management ---

    def _get_tenant(self) -> Tenant:
        return self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()

    def list_schedules(self) -> List[AvailabilitySchedule]:
        tenant = self._get_tenant()
        if not tenant:
            return []
        
        schedules_data = tenant.config_json.get('availability_schedules', [])
        if not schedules_data:
            # Create default if none exist
            default = self._create_default_schedule_object()
            self.create_schedule(default)
            return [default]
            
        return [AvailabilitySchedule(**s) for s in schedules_data]

    def _create_default_schedule_object(self) -> AvailabilitySchedule:
        # Default: Mon-Fri 9-17
        ranges = [TimeRange(start="09:00", end="17:00")]
        schedule = WeeklySchedule(
            monday=DaySchedule(active=True, ranges=ranges),
            tuesday=DaySchedule(active=True, ranges=ranges),
            wednesday=DaySchedule(active=True, ranges=ranges),
            thursday=DaySchedule(active=True, ranges=ranges),
            friday=DaySchedule(active=True, ranges=ranges)
        )
        return AvailabilitySchedule(
            name="Horas laborales",
            is_default=True,
            timezone="America/Bogota", # Default or from user config
            schedule=schedule
        )

    def create_schedule(self, schedule: AvailabilitySchedule) -> AvailabilitySchedule:
        tenant = self._get_tenant()
        config = dict(tenant.config_json)
        schedules = config.get('availability_schedules', [])
        
        # If set as default, unset others
        if schedule.is_default:
            for s in schedules:
                s['is_default'] = False
        
        schedules.append(schedule.dict())
        config['availability_schedules'] = schedules
        
        tenant.config_json = config
        flag_modified(tenant, "config_json")
        self.db.commit()
        self.db.refresh(tenant)
        return schedule

    def update_schedule(self, schedule_id: str, update: ScheduleUpdate) -> Optional[AvailabilitySchedule]:
        tenant = self._get_tenant()
        config = dict(tenant.config_json)
        schedules = config.get('availability_schedules', [])
        
        target_idx = next((i for i, s in enumerate(schedules) if s['id'] == schedule_id), None)
        if target_idx is None:
            return None
            
        current = schedules[target_idx]
        
        # If setting as default, unset others
        if update.is_default:
            for s in schedules:
                s['is_default'] = False
        
        # Merge updates
        if update.name: current['name'] = update.name
        if update.is_default is not None: current['is_default'] = update.is_default
        if update.timezone: current['timezone'] = update.timezone
        if update.schedule: current['schedule'] = update.schedule.dict()
        
        schedules[target_idx] = current
        config['availability_schedules'] = schedules
        
        tenant.config_json = config
        flag_modified(tenant, "config_json")
        self.db.commit()
        
        return AvailabilitySchedule(**current)

    def delete_schedule(self, schedule_id: str) -> bool:
        tenant = self._get_tenant()
        config = dict(tenant.config_json)
        schedules = config.get('availability_schedules', [])
        
        new_schedules = [s for s in schedules if s['id'] != schedule_id]
        
        if len(new_schedules) == len(schedules):
            return False
            
        config['availability_schedules'] = new_schedules
        tenant.config_json = config
        flag_modified(tenant, "config_json")
        self.db.commit()
        return True

    def get_schedule_by_id(self, schedule_id: str) -> Optional[AvailabilitySchedule]:
        schedules = self.list_schedules()
        return next((s for s in schedules if s.id == schedule_id), None)

    def get_active_schedule(self) -> AvailabilitySchedule:
        schedules = self.list_schedules()
        default = next((s for s in schedules if s.is_default), None)
        if default:
            return default
        return schedules[0] if schedules else self._create_default_schedule_object()

    # --- Slot Calculation ---

    def get_available_slots(self, 
                            start_date: datetime.date, 
                            end_date: datetime.date, 
                            duration_minutes: int = 30,
                            schedule_override: Optional[AvailabilitySchedule] = None) -> List[datetime.datetime]:
        
        # 1. Get Active Schedule
        schedule_config = schedule_override or self.get_active_schedule()
        
        # 2. Get Busy Periods from Google (if connected)
        busy_intervals = []
        if self.adapter:
            start_dt_q = datetime.datetime.combine(start_date, datetime.time.min).replace(tzinfo=datetime.timezone.utc)
            end_dt_q = datetime.datetime.combine(end_date, datetime.time.max).replace(tzinfo=datetime.timezone.utc)
            try:
                busy_periods = self.adapter.list_busy_periods(start_dt_q, end_dt_q)
                for period in busy_periods:
                    start_str = period['start'].replace('Z', '+00:00')
                    end_str = period['end'].replace('Z', '+00:00')
                    start = datetime.datetime.fromisoformat(start_str)
                    end = datetime.datetime.fromisoformat(end_str)
                    busy_intervals.append((start, end))
            except Exception as e:
                logger.error(f"Failed to fetch busy periods: {e}")

        available_slots = []
        
        # 3. Iterate days
        current_day = start_date
        while current_day <= end_date:
            day_name = current_day.strftime("%A").lower() # monday, tuesday...
            day_config: DaySchedule = getattr(schedule_config.schedule, day_name, None)
            
            if day_config and day_config.active:
                for time_range in day_config.ranges:
                    # Parse HH:MM
                    h_start, m_start = map(int, time_range.start.split(':'))
                    h_end, m_end = map(int, time_range.end.split(':'))
                    
                    # Create range datetimes using Schedule Timezone
                    tz = datetime.timezone.utc
                    if schedule_config.timezone:
                        try:
                            tz = ZoneInfo(schedule_config.timezone)
                        except Exception:
                            logger.warning(f"Invalid timezone {schedule_config.timezone}, falling back to UTC")

                    # Create local time then convert to UTC
                    slot_start_local = datetime.datetime.combine(current_day, datetime.time(h_start, m_start)).replace(tzinfo=tz)
                    slot_end_limit_local = datetime.datetime.combine(current_day, datetime.time(h_end, m_end)).replace(tzinfo=tz)
                    
                    slot_start = slot_start_local.astimezone(datetime.timezone.utc)
                    slot_end_limit = slot_end_limit_local.astimezone(datetime.timezone.utc)
                    
                    current_slot = slot_start
                    while current_slot + datetime.timedelta(minutes=duration_minutes) <= slot_end_limit:
                        slot_end = current_slot + datetime.timedelta(minutes=duration_minutes)
                        
                        # Check intersection with busy intervals
                        is_busy = False
                        for b_start, b_end in busy_intervals:
                            if max(current_slot, b_start) < min(slot_end, b_end):
                                is_busy = True
                                break
                        
                        if not is_busy:
                            available_slots.append(current_slot)
                        
                        current_slot += datetime.timedelta(minutes=duration_minutes)
            
            current_day += datetime.timedelta(days=1)
            
        return available_slots

    def get_event_type_slots(self, event_type: EventType, start_date: datetime.date, end_date: datetime.date) -> List[datetime.datetime]:
        schedule = None
        if event_type.availability_id:
            schedule = self.get_schedule_by_id(event_type.availability_id)
            
        return self.get_available_slots(
            start_date=start_date,
            end_date=end_date,
            duration_minutes=event_type.duration,
            schedule_override=schedule
        )

    def book_meeting(self, 
                     slot_time: datetime.datetime, 
                     duration_minutes: int, 
                     lead_data: Dict[str, Any],
                     summary: str = "Reunión de Ventas") -> Dict[str, Any]:
        
        if not self.adapter:
            raise ValueError("Calendar not connected")

        # Ensure slot_time is aware
        if slot_time.tzinfo is None:
            slot_time = slot_time.replace(tzinfo=datetime.timezone.utc)

        end_time = slot_time + datetime.timedelta(minutes=duration_minutes)
        
        # Inject metadata in description
        description = f"""
        Reunión con {lead_data.get('name', 'Lead')}
        Email: {lead_data.get('email', 'N/A')}
        
        -- System Metadata --
        LeadID: {lead_data.get('id')}
        DealContext: {lead_data.get('dealContext', 'N/A')}
        """
        
        event = self.adapter.create_event(
            summary=f"{summary} - {lead_data.get('name', 'Lead')}",
            description=description,
            start_time=slot_time,
            end_time=end_time,
            attendees=[lead_data.get('email')] if lead_data.get('email') else []
        )

        # Send Email if Gmail connected
        gmail_adapter = self._get_gmail_adapter()
        if gmail_adapter and lead_data.get('email'):
            try:
                date_str = slot_time.strftime("%d/%m/%Y %H:%M UTC")
                
                email_subject = f"Confirmación: {summary}"
                email_body = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2563eb;">¡Tu reunión está confirmada!</h2>
                    <p>Hola <strong>{lead_data.get('name', 'Lead')}</strong>,</p>
                    <p>Hemos agendado correctamente tu sesión. Aquí tienes los detalles:</p>
                    
                    <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>📅 Fecha:</strong> {date_str}</p>
                        <p style="margin: 5px 0;"><strong>⏱️ Duración:</strong> {duration_minutes} minutos</p>
                        <p style="margin: 5px 0;"><strong>🔗 Enlace:</strong> <a href="{event.get('htmlLink')}" style="color: #2563eb;">Ver en Google Calendar</a></p>
                    </div>

                    <p>Si necesitas reprogramar, por favor avísanos con anticipación.</p>
                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;" />
                    <p style="color: #6b7280; font-size: 12px;">Enviado automáticamente por Visionarias AI</p>
                </div>
                """
                gmail_adapter.send_email(lead_data['email'], email_subject, email_body)
                logger.info(f"Confirmation email sent to {lead_data['email']}")
            except Exception as e:
                logger.error(f"Failed to send confirmation email: {e}")
        
        return event

    def list_appointments(self, start_date: datetime.date, end_date: datetime.date) -> List[Dict[str, Any]]:
        if not self.adapter:
            return []
            
        start_dt = datetime.datetime.combine(start_date, datetime.time.min).replace(tzinfo=datetime.timezone.utc)
        end_dt = datetime.datetime.combine(end_date, datetime.time.max).replace(tzinfo=datetime.timezone.utc)
        
        return self.adapter.list_events(start_dt, end_dt)

    def watch_calendar(self, calendar_id: str = 'primary', channel_id: str = None, address: str = None) -> Dict[str, Any]:
        """
        Placeholder/Skeleton for Webhook Setup.
        Configures a push notification channel for Google Calendar changes.
        """
        if not self.adapter:
            logger.warning("Cannot watch calendar: No active connection")
            return {}
            
        service = self.adapter.get_service()
        
        # Use provided address or construct default webhook URL
        webhook_address = address or f"{settings.API_DOMAIN or 'https://api.visionarias.ai'}/api/v1/webhook/calendar/{self.tenant_id}"
        
        body = {
            "id": channel_id or str(uuid.uuid4()),
            "type": "web_hook",
            "address": webhook_address,
            # "token": "..." # Optional security token
        }
        
        try:
            logger.info(f"Setting up calendar watch on {webhook_address}")
            return service.events().watch(calendarId=calendar_id, body=body).execute()
        except Exception as e:
            logger.error(f"Failed to setup calendar watch: {e}")
            return {"error": str(e)}
