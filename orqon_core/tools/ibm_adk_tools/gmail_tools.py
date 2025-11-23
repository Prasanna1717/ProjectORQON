from typing import Optional, List, Dict
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.google_workspace_tools import GoogleWorkspaceTools


@tool(
    name="send_email_to_client",
    description="Send professional email to a client via Gmail. Use for client communications, trade confirmations, follow-ups, and meeting requests.",
    permission=ToolPermission.ADMIN
)
def send_email_to_client(
    to_email: str,
    subject: str,
    body: str,
    cc_emails: Optional[List[str]] = None
) -> str:
    try:
        gmail = GoogleWorkspaceTools()
        
        result = gmail.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            cc_emails=cc_emails
        )
        
        if result["success"]:
            return f"✅ Email sent successfully to {to_email}\nMessage ID: {result.get('message_id', 'N/A')}"
        else:
            return f"❌ Failed to send email: {result.get('error', 'Unknown error')}"
    
    except Exception as e:
        return f"❌ Error sending email: {str(e)}"


@tool(
    name="send_email_with_trade_blotter",
    description="Send email with trade blotter Excel file attached. Use when client requests trade summary spreadsheet or full trade report.",
    permission=ToolPermission.ADMIN
)
def send_email_with_trade_blotter(
    to_email: str,
    subject: str,
    body: str
) -> str:
    try:
        gmail = GoogleWorkspaceTools()
        
        data_dir = Path(__file__).parent.parent.parent / "data"
        trade_blotter_path = data_dir / "trade_blotter.csv"
        
        if not trade_blotter_path.exists():
            return f"❌ Trade blotter file not found at {trade_blotter_path}"
        
        result = gmail.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            attachment_path=str(trade_blotter_path)
        )
        
        if result["success"]:
            return f"✅ Email sent with trade blotter attached to {to_email}\nMessage ID: {result.get('message_id', 'N/A')}"
        else:
            return f"❌ Failed to send email with attachment: {result.get('error', 'Unknown error')}"
    
    except Exception as e:
        return f"❌ Error sending email with attachment: {str(e)}"


@tool(
    name="create_calendar_reminder",
    description="Create a calendar reminder for follow-up tasks, meetings, or important dates. Use for scheduling reminders about client follow-ups, compliance deadlines, or trade reviews.",
    permission=ToolPermission.ADMIN
)
def create_calendar_reminder(
    title: str,
    reminder_datetime: str,
    notes: str = ""
) -> str:
    try:
        from datetime import datetime
        
        gmail = GoogleWorkspaceTools()
        reminder_time = datetime.fromisoformat(reminder_datetime)
        
        result = gmail.create_reminder(
            title=title,
            reminder_time=reminder_time,
            notes=notes
        )
        
        if result["success"]:
            return f"✅ Reminder created: {title}\n📅 Event Link: {result.get('event_link', 'N/A')}"
        else:
            return f"❌ Failed to create reminder: {result.get('error', 'Unknown error')}"
    
    except Exception as e:
        return f"❌ Error creating reminder: {str(e)}"


@tool(
    name="schedule_google_meet",
    description="Schedule a Google Meet video meeting with client or team. Automatically generates Meet link and sends calendar invites to attendees.",
    permission=ToolPermission.ADMIN
)
def schedule_google_meet(
    title: str,
    start_datetime: str,
    duration_minutes: int,
    attendee_emails: List[str],
    description: str = ""
) -> str:
    try:
        from datetime import datetime
        
        gmail = GoogleWorkspaceTools()
        start_time = datetime.fromisoformat(start_datetime)
        
        result = gmail.schedule_meeting(
            title=title,
            start_time=start_time,
            duration_minutes=duration_minutes,
            attendee_emails=attendee_emails,
            description=description
        )
        
        if result["success"]:
            response = f"✅ Meeting scheduled: {title}\n"
            response += f"📅 Event Link: {result.get('event_link', 'N/A')}\n"
            if result.get('meet_link'):
                response += f"🎥 Google Meet Link: {result['meet_link']}"
            return response
        else:
            return f"❌ Failed to schedule meeting: {result.get('error', 'Unknown error')}"
    
    except Exception as e:
        return f"❌ Error scheduling meeting: {str(e)}"


@tool(
    name="get_client_email_address",
    description="Retrieve verified client email address from trade blotter CSV. Use when you need to find correct email address for a client by name.",
    permission=ToolPermission.READ_ONLY
)
def get_client_email_address(client_name: str) -> str:
    try:
        import pandas as pd
        from pathlib import Path
        
        csv_path = Path(__file__).parent.parent.parent / "data" / "trade_blotter.csv"
        
        if not csv_path.exists():
            return f"❌ Trade blotter CSV not found"
        
        df = pd.read_csv(csv_path)
        
        name_lower = client_name.lower()
        matches = df[df['Client_Name'].str.lower().str.contains(name_lower, na=False)]
        
        if matches.empty:
            return f"❌ No client found matching '{client_name}'"
        
        email = matches.iloc[0]['email']
        full_name = matches.iloc[0]['Client_Name']
        
        return f"✅ {full_name}: {email}"
    
    except Exception as e:
        return f"❌ Error retrieving email: {str(e)}"
