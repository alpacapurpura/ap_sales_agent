import logging
from typing import Dict, Any, List, Optional
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from src.core.config import settings
from src.modules.connections.infrastructure.marketing_connectors.base import BaseConnector
import json
import datetime
import os

# Allow OAuth scope to change (e.g. if user granted extra scopes previously)
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']

class GoogleCalendarAdapter(BaseConnector):
    """
    Adapter for Google Calendar API.
    Handles OAuth2 flow and wraps calendar operations.
    """
    def __init__(self, credentials_data: Optional[Dict[str, Any]] = None):
        self.credentials_data = credentials_data
        self.creds = None
        if credentials_data:
            self.creds = Credentials.from_authorized_user_info(credentials_data, SCOPES)

    def sync_contacts(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Sync contacts implementation (Placeholder).
        """
        return []

    def sync_events(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Sync events implementation (Next 30 days).
        """
        now = datetime.datetime.utcnow()
        end = now + datetime.timedelta(days=30)
        return self.list_events(now, end)

    @staticmethod
    def get_client_config() -> Dict[str, Any]:
        return {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

    @staticmethod
    def get_authorization_url(redirect_uri: str = None) -> tuple[str, str]:
        """Generates the authorization URL and state."""
        flow = Flow.from_client_config(
            GoogleCalendarAdapter.get_client_config(),
            scopes=SCOPES
        )
        flow.redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent' # Force consent to ensure we get a refresh token
        )
        return authorization_url, state

    @staticmethod
    def exchange_code(code: str, redirect_uri: str = None) -> Dict[str, Any]:
        """Exchanges the authorization code for tokens."""
        flow = Flow.from_client_config(
            GoogleCalendarAdapter.get_client_config(),
            scopes=SCOPES
        )
        
        # Ensure redirect_uri matches exactly what was sent in get_authorization_url
        # If frontend sends one, use it. Otherwise fallback to settings.
        flow.redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
        
        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
            return json.loads(creds.to_json())
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise

    def get_service(self):
        """Returns the Google Calendar service resource."""
        if not self.creds:
            raise ValueError("Credentials not initialized")
        return build('calendar', 'v3', credentials=self.creds)

    def list_busy_periods(self, start_time: datetime.datetime, end_time: datetime.datetime, calendar_id: str = 'primary') -> List[Dict[str, Any]]:
        """Wraps the freebusy query."""
        service = self.get_service()
        body = {
            "timeMin": start_time.isoformat(), # Input should be ISO format with offset or Z
            "timeMax": end_time.isoformat(),
            "items": [{"id": calendar_id}]
        }
        try:
            events_result = service.freebusy().query(body=body).execute()
            return events_result.get('calendars', {}).get(calendar_id, {}).get('busy', [])
        except Exception as e:
            logger.error(f"Error fetching busy periods: {e}")
            raise

    def create_event(self, summary: str, description: str, start_time: datetime.datetime, end_time: datetime.datetime, attendees: List[str], calendar_id: str = 'primary') -> Dict[str, Any]:
        """Creates an event with Google Meet link."""
        service = self.get_service()
        
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
            },
            'end': {
                'dateTime': end_time.isoformat(),
            },
            'attendees': [{'email': email} for email in attendees],
            'conferenceData': {
                'createRequest': {
                    'requestId': f"req-{int(datetime.datetime.now().timestamp())}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
        }

        try:
            event = service.events().insert(
                calendarId=calendar_id, 
                body=event, 
                conferenceDataVersion=1
            ).execute()
            return event
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            raise

    def list_events(self, start_time: datetime.datetime, end_time: datetime.datetime, calendar_id: str = 'primary') -> List[Dict[str, Any]]:
        """Lists events for the sales dashboard."""
        service = self.get_service()
        try:
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except Exception as e:
            logger.error(f"Error listing events: {e}")
            raise
