"""
Google Workspace Tools (Gmail, Calendar, Meet)
Integration with Google Cloud APIs
"""
import os
import pickle
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64

# Scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
CREDENTIALS_FILE = DATA_DIR / "google_credentials.json"
TOKEN_FILE = DATA_DIR / "google_token.pickle"


class GoogleWorkspaceTools:
    """Google Workspace API integration"""
    
    def __init__(self):
        self.creds = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google APIs"""
        # Load token if exists
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'rb') as token:
                self.creds = pickle.load(token)
        
        # If no valid credentials, authenticate
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {CREDENTIALS_FILE}\n"
                        "Please follow GOOGLE_SETUP.md to set up Google Cloud API"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_FILE), SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # Save token
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(self.creds, token)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
        attachment_paths: Optional[List[str]] = None
    ) -> Dict:
        """
        Send email via Gmail with multiple attachments
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body (HTML supported)
            cc_emails: List of CC recipients
            attachment_paths: List of file paths to attach
        
        Returns:
            Dict with success status and message ID
        """
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject
            
            if cc_emails:
                message['cc'] = ', '.join(cc_emails)
            
            # Add body
            message.attach(MIMEText(body, 'html'))
            
            # Add attachments if provided
            if attachment_paths:
                for attachment_path in attachment_paths:
                    if os.path.exists(attachment_path):
                        filename = os.path.basename(attachment_path)
                        
                        # Determine MIME type based on file extension
                        if filename.endswith('.docx'):
                            maintype = 'application'
                            subtype = 'vnd.openxmlformats-officedocument.wordprocessingml.document'
                        elif filename.endswith('.csv'):
                            maintype = 'text'
                            subtype = 'csv'
                        elif filename.endswith('.xlsx'):
                            maintype = 'application'
                            subtype = 'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        else:
                            maintype = 'application'
                            subtype = 'octet-stream'
                        
                        with open(attachment_path, 'rb') as f:
                            part = MIMEBase(maintype, subtype)
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{filename}"'
                            )
                            message.attach(part)
            
            # Encode and send
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            attachment_count = len(attachment_paths) if attachment_paths else 0
            return {
                "success": True,
                "message_id": result['id'],
                "message": f"Email sent successfully to {to_email} with {attachment_count} attachment(s)"
            }
        
        except HttpError as error:
            return {
                "success": False,
                "error": str(error),
                "message": f"Failed to send email: {error}"
            }
    
    def create_calendar_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        attendees: Optional[List[str]] = None,
        add_meet_link: bool = False
    ) -> Dict:
        """
        Create Google Calendar event
        
        Args:
            summary: Event title
            start_time: Start datetime
            end_time: End datetime
            description: Event description
            attendees: List of attendee emails
            add_meet_link: Whether to add Google Meet link
        
        Returns:
            Dict with success status, event link, and meet link
        """
        try:
            service = build('calendar', 'v3', credentials=self.creds)
            
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }
            
            # Add attendees
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            # Add Google Meet link
            if add_meet_link:
                event['conferenceData'] = {
                    'createRequest': {
                        'requestId': f"meet-{datetime.now().timestamp()}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
            
            # Create event
            event_result = service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1 if add_meet_link else 0,
                sendUpdates='all' if attendees else 'none'
            ).execute()
            
            meet_link = None
            if add_meet_link and 'conferenceData' in event_result:
                meet_link = event_result['conferenceData']['entryPoints'][0]['uri']
            
            return {
                "success": True,
                "event_id": event_result['id'],
                "event_link": event_result.get('htmlLink'),
                "meet_link": meet_link,
                "message": f"Event '{summary}' created successfully"
            }
        
        except HttpError as error:
            return {
                "success": False,
                "error": str(error),
                "message": f"Failed to create event: {error}"
            }
    
    def create_reminder(
        self,
        title: str,
        reminder_time: datetime,
        notes: str = ""
    ) -> Dict:
        """Create a calendar reminder (1-hour event)"""
        end_time = reminder_time + timedelta(hours=1)
        return self.create_calendar_event(
            summary=f"⏰ Reminder: {title}",
            start_time=reminder_time,
            end_time=end_time,
            description=notes,
            add_meet_link=False
        )
    
    def schedule_meeting(
        self,
        title: str,
        start_time: datetime,
        duration_minutes: int,
        attendee_emails: List[str],
        description: str = ""
    ) -> Dict:
        """Schedule a Google Meet meeting"""
        end_time = start_time + timedelta(minutes=duration_minutes)
        return self.create_calendar_event(
            summary=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            attendees=attendee_emails,
            add_meet_link=True
        )
    
    def list_upcoming_events(self, max_results: int = 10) -> Dict:
        """List upcoming calendar events"""
        try:
            service = build('calendar', 'v3', credentials=self.creds)
            
            # Get events from now onwards
            now = datetime.utcnow().isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            return {
                "success": True,
                "events": events,
                "count": len(events)
            }
        
        except HttpError as error:
            return {
                "success": False,
                "error": str(error),
                "events": []
            }
    
    def cancel_event(self, event_id: str) -> Dict:
        """Cancel/delete a specific calendar event"""
        try:
            service = build('calendar', 'v3', credentials=self.creds)
            
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            return {
                "success": True,
                "message": f"Event {event_id} cancelled successfully"
            }
        
        except HttpError as error:
            return {
                "success": False,
                "error": str(error),
                "message": f"Failed to cancel event: {error}"
            }
    
    def cancel_all_meetings(self, filter_keyword: Optional[str] = None) -> Dict:
        """Cancel all upcoming meetings (optionally filter by keyword in title)"""
        try:
            # Get all upcoming events
            result = self.list_upcoming_events(max_results=50)
            
            if not result['success']:
                return result
            
            events = result['events']
            cancelled_count = 0
            cancelled_titles = []
            
            for event in events:
                title = event.get('summary', '')
                event_id = event.get('id')
                
                # Filter by keyword if provided
                if filter_keyword and filter_keyword.lower() not in title.lower():
                    continue
                
                # Cancel the event
                cancel_result = self.cancel_event(event_id)
                if cancel_result['success']:
                    cancelled_count += 1
                    cancelled_titles.append(title)
            
            return {
                "success": True,
                "cancelled_count": cancelled_count,
                "cancelled_titles": cancelled_titles,
                "message": f"Cancelled {cancelled_count} meeting(s)"
            }
        
        except Exception as error:
            return {
                "success": False,
                "error": str(error),
                "message": f"Failed to cancel meetings: {error}"
            }


# Tool functions for agent
def send_email_tool(
    to_email: str,
    subject: str,
    body: str,
    attach_trade_blotter: bool = False
) -> str:
    """Send email via Gmail"""
    try:
        tools = GoogleWorkspaceTools()
        
        attachment = None
        if attach_trade_blotter:
            attachment = str(DATA_DIR / "trade_blotter.xlsx")
        
        result = tools.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            attachment_path=attachment
        )
        
        if result["success"]:
            return f"✅ {result['message']}\nMessage ID: {result['message_id']}"
        else:
            return f"❌ {result['message']}"
    
    except Exception as e:
        return f"❌ Error: {str(e)}"


def create_reminder_tool(title: str, reminder_datetime: str, notes: str = "") -> str:
    """Create a calendar reminder"""
    try:
        tools = GoogleWorkspaceTools()
        reminder_time = datetime.fromisoformat(reminder_datetime)
        
        result = tools.create_reminder(
            title=title,
            reminder_time=reminder_time,
            notes=notes
        )
        
        if result["success"]:
            return f"✅ {result['message']}\n📅 Event Link: {result['event_link']}"
        else:
            return f"❌ {result['message']}"
    
    except Exception as e:
        return f"❌ Error: {str(e)}"


def schedule_meeting_tool(
    title: str,
    start_datetime: str,
    duration_minutes: int,
    attendee_emails: List[str],
    description: str = ""
) -> str:
    """Schedule a Google Meet meeting"""
    try:
        tools = GoogleWorkspaceTools()
        start_time = datetime.fromisoformat(start_datetime)
        
        result = tools.schedule_meeting(
            title=title,
            start_time=start_time,
            duration_minutes=duration_minutes,
            attendee_emails=attendee_emails,
            description=description
        )
        
        if result["success"]:
            response = f"✅ {result['message']}\n"
            response += f"📅 Event Link: {result['event_link']}\n"
            if result['meet_link']:
                response += f"🎥 Google Meet: {result['meet_link']}"
            return response
        else:
            return f"❌ {result['message']}"
    
    except Exception as e:
        return f"❌ Error: {str(e)}"
