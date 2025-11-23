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

SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]

DATA_DIR = Path(__file__).parent.parent / "data"
CREDENTIALS_FILE = DATA_DIR / "google_credentials.json"
TOKEN_FILE = DATA_DIR / "google_token.pickle"


class GoogleWorkspaceTools:
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'rb') as token:
                self.creds = pickle.load(token)
        
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
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject
            
            if cc_emails:
                message['cc'] = ', '.join(cc_emails)
            
            message.attach(MIMEText(body, 'html'))
            
            if attachment_paths:
                for attachment_path in attachment_paths:
                    if os.path.exists(attachment_path):
                        filename = os.path.basename(attachment_path)
                        
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
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            if add_meet_link:
                event['conferenceData'] = {
                    'createRequest': {
                        'requestId': f"meet-{datetime.now().timestamp()}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
            
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
