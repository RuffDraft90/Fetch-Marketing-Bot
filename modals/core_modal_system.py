"""
Core Modal System
================
Core modal creation functions and action handlers for the marketing bot
"""

import logging
import re
import json
import os
import random
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)

# ========================================
# MODAL NAVIGATION HELPER
# ========================================

async def handle_modal_navigation(client, body: Dict[str, Any], modal: Dict[str, Any], navigation_type: str = "auto"):
    """
    Unified modal navigation handler to fix inconsistent view push/update behavior.
    
    Args:
        client: Slack client instance
        body: Slack event body
        modal: Modal definition to display
        navigation_type: "auto", "update", "push", or "open"
    """
    try:
        # Auto-detect best navigation method
        if navigation_type == "auto":
            if "view" in body and "id" in body["view"]:
                # We have an existing modal to update
                navigation_type = "update"
            elif "trigger_id" in body and body["trigger_id"]:
                # We have a trigger_id for new modal
                navigation_type = "open"
            else:
                # Fallback to update if we have view info
                navigation_type = "update" if "view" in body else "open"
        
        # Execute the appropriate navigation method with fallbacks
        if navigation_type == "update":
            if "view" not in body or "id" not in body["view"]:
                logger.warning("Cannot update modal: no view ID found, falling back to open")
                if "trigger_id" in body and body["trigger_id"]:
                    return await client.views_open(trigger_id=body["trigger_id"], view=modal)
                else:
                    raise ValueError("No trigger_id available for fallback")
            
            try:
                return await client.views_update(view_id=body["view"]["id"], view=modal)
            except Exception as e:
                logger.warning(f"views_update failed: {e}, attempting fallback")
                if "trigger_id" in body and body["trigger_id"]:
                    return await client.views_open(trigger_id=body["trigger_id"], view=modal)
                raise
                
        elif navigation_type == "push":
            if "trigger_id" not in body or not body["trigger_id"]:
                logger.warning("Cannot push modal: no trigger_id found, falling back to update")
                if "view" in body and "id" in body["view"]:
                    return await client.views_update(view_id=body["view"]["id"], view=modal)
                else:
                    raise ValueError("No view ID available for fallback")
            
            try:
                return await client.views_push(trigger_id=body["trigger_id"], view=modal)
            except Exception as e:
                logger.warning(f"views_push failed: {e}, attempting fallback to update")
                if "view" in body and "id" in body["view"]:
                    return await client.views_update(view_id=body["view"]["id"], view=modal)
                raise
                
        elif navigation_type == "open":
            if "trigger_id" not in body or not body["trigger_id"]:
                logger.warning("Cannot open modal: no trigger_id found, falling back to update")
                if "view" in body and "id" in body["view"]:
                    return await client.views_update(view_id=body["view"]["id"], view=modal)
                else:
                    raise ValueError("No trigger_id or view ID available")
            
            return await client.views_open(trigger_id=body["trigger_id"], view=modal)
        
        else:
            raise ValueError(f"Invalid navigation_type: {navigation_type}")
            
    except ValueError as ve:
        # Re-raise ValueError for invalid navigation_type
        raise ve
    except Exception as e:
        logger.error(f"Modal navigation failed: {e}")
        # Last resort: try any available method
        if "view" in body and "id" in body["view"]:
            try:
                return await client.views_update(view_id=body["view"]["id"], view=modal)
            except:
                pass
        if "trigger_id" in body and body["trigger_id"]:
            try:
                return await client.views_open(trigger_id=body["trigger_id"], view=modal)
            except:
                pass
        raise Exception(f"All modal navigation methods failed: {e}")

# ========================================
# VALIDATION & ERROR HANDLING
# ========================================

def validate_form_data(form_data: Dict[str, Any], required_fields: list) -> Dict[str, str]:
    """Validate form data and return errors."""
    errors = {}
    
    for field in required_fields:
        value = form_data.get(field, "")
        if isinstance(value, dict):
            # Handle select inputs
            value = value.get("selected_option", {}).get("value", "")
        
        if not str(value).strip():
            field_name = field.replace('_', ' ').title()
            errors[field] = f"{field_name} is required"
        elif field.endswith('_name'):
            # Additional validation for name fields
            if not re.match("^[a-zA-Z ]*$", str(value)):
                field_name = field.replace('_', ' ').title()
                errors[field] = f"{field_name} must only contain letters and spaces"
        elif field == 'email':
            # Validate email format
            if not re.match(r"[^@]+@[^@]+\.[^@]+", str(value)):
                errors[field] = "Invalid email address"
        elif field == 'phone':
            # Validate phone number format
            if not re.match(r"^\+?[1-9]\d{1,14}$", str(value)):
                errors[field] = "Invalid phone number"
    
    return errors

# ========================================
# MODAL ACTIONS
# ========================================

async def handle_form_submission(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle form submission and return response."""
    required_fields = ['first_name', 'last_name', 'email', 'phone']
    errors = validate_form_data(form_data, required_fields)
    
    if errors:
        return {"status": "error", "errors": errors}
    
    # Process the valid form data (e.g., save to database, send email, etc.)
    # ...
    
    return {"status": "success", "message": "Form submitted successfully"}

# ========================================
# MODAL CREATION FUNCTIONS
# ========================================

def add_dividers_to_modal(modal: Dict[str, Any]) -> Dict[str, Any]:
    """Add dividers between sections in a modal."""
    updated_blocks = []
    for block in modal.get("blocks", []):
        updated_blocks.append(block)
        if block.get("type") == "section":
            updated_blocks.append({"type": "divider"})
    modal["blocks"] = updated_blocks
    return modal

def fetch_google_calendar_events():
    """Fetch upcoming events from Google Calendar API."""
    # Enhanced placeholder for actual Google Calendar API integration
    # Replace with logic to fetch events using google_calendar_service.py
    try:
        from services.google_calendar_service import google_calendar_service
        # In production, this would use: return await google_calendar_service.get_upcoming_events()
    except ImportError:
        pass
    
    # Mock data that would come from Google Calendar API
    return [
        {
            "summary": "Summer Launch Campaign Kickoff",
            "start": "2025-07-25T10:00:00",
            "end": "2025-07-25T11:30:00",
            "location": "Conference Room A",
            "attendees": ["kelly.redding@fetchrewards.com", "karen.lowry@fetchrewards.com"],
            "description": "Campaign planning and timeline review"
        },
        {
            "summary": "Q3 Marketing Review", 
            "start": "2025-07-26T14:00:00",
            "end": "2025-07-26T15:00:00",
            "location": "Virtual Meeting",
            "attendees": ["kate.jeffries@fetchrewards.com"],
            "description": "Quarterly marketing performance review"
        },
        {
            "summary": "Community Meetup - Chicago",
            "start": "2025-07-28T09:00:00", 
            "end": "2025-07-28T17:00:00",
            "location": "Chicago Convention Center",
            "attendees": ["karen.lowry@fetchrewards.com", "kate.jeffries@fetchrewards.com"],
            "description": "Community engagement event"
        },
        {
            "summary": "Email Campaign Content Review",
            "start": "2025-07-29T09:00:00",
            "end": "2025-07-29T10:00:00", 
            "location": "Marketing Office",
            "attendees": ["jheryl@fetchrewards.com", "kelly.redding@fetchrewards.com"],
            "description": "Review email content and approve for send"
        },
        {
            "summary": "Creative Design Review - Summer Campaign",
            "start": "2025-07-30T11:00:00",
            "end": "2025-07-30T12:00:00",
            "location": "Design Studio",
            "attendees": ["kelly.redding@fetchrewards.com"],
            "description": "Review creative assets for summer product launch"
        }
    ]

def fetch_monday_campaigns():
    """Fetch active campaigns from Monday.com."""
    # Enhanced placeholder for actual Monday.com API integration
    # Replace with logic to fetch campaigns using monday_service.py
    try:
        from services.monday_service import monday_service
        # In production, this would use: return await monday_service.get_active_campaigns()
    except ImportError:
        pass
    
    # Mock data that would come from Monday.com API
    return [
        {
            "id": "12345",
            "name": "Summer Product Launch",
            "status": "In Progress",
            "progress": 75,
            "next_task": "Creative Review",
            "assignee": "Kelly Redding",
            "due_date": "2025-07-27",
            "board_url": "https://fetchrewards.monday.com/boards/12345",
            "total_tasks": 8,
            "completed_tasks": 6,
            "priority": "High"
        },
        {
            "id": "12346", 
            "name": "Q3 Email Campaign",
            "status": "Design Phase",
            "progress": 45,
            "next_task": "Content Creation",
            "assignee": "Jheryl",
            "due_date": "2025-07-30",
            "board_url": "https://fetchrewards.monday.com/boards/12346",
            "total_tasks": 12,
            "completed_tasks": 5,
            "priority": "Medium"
        },
        {
            "id": "12347",
            "name": "Community Meetup - Chicago", 
            "status": "EDEN Review",
            "progress": 80,
            "next_task": "Final Approval",
            "assignee": "Karen or Kate",
            "due_date": "2025-07-25",
            "board_url": "https://fetchrewards.monday.com/boards/12347",
            "total_tasks": 15,
            "completed_tasks": 12,
            "priority": "High"
        },
        {
            "id": "12348",
            "name": "Back-to-School Campaign",
            "status": "Planning",
            "progress": 20,
            "next_task": "Strategy Development",
            "assignee": "Team Assignment Pending",
            "due_date": "2025-08-15",
            "board_url": "https://fetchrewards.monday.com/boards/12348",
            "total_tasks": 10,
            "completed_tasks": 2,
            "priority": "Medium"
        }
    ]

def create_google_calendar_view():
    """Create a Google Calendar view for the dashboard modal."""
    events = fetch_google_calendar_events()
    event_blocks = []

    for event in events:
        try:
            start_time = datetime.strptime(event["start"], "%Y-%m-%dT%H:%M:%S").strftime("%b %d, %I:%M %p")
            end_time = datetime.strptime(event["end"], "%Y-%m-%dT%H:%M:%S").strftime("%I:%M %p")
            
            # Get days until event
            event_date = datetime.strptime(event["start"], "%Y-%m-%dT%H:%M:%S").date()
            today = datetime.now().date()
            days_until = (event_date - today).days
            
            if days_until == 0:
                urgency_indicator = "🔴"
            elif days_until == 1:
                urgency_indicator = "🟡"
            elif days_until <= 3:
                urgency_indicator = "🟠"
            else:
                urgency_indicator = "📅"
            
            attendee_info = f"👥 {len(event.get('attendees', []))} attendees" if event.get('attendees') else ""
            location_info = f"📍 {event.get('location', 'Location TBD')}"
            
            event_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{event['summary']}*\n{urgency_indicator} {start_time} - {end_time}\n{location_info} | {attendee_info}"
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Details"},
                    "action_id": "view_event_details"
                }
            })
        except Exception as e:
            logger.warning(f"Error processing event: {e}")
            # Fallback for malformed event data
            event_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{event.get('summary', 'Untitled Event')}*\n📅 Event details unavailable"
                }
            })

    return event_blocks

def create_monday_campaigns_view():
    """Create a Monday.com campaigns view for the dashboard modal."""
    campaigns = fetch_monday_campaigns()
    campaign_blocks = []
    
    for campaign in campaigns:
        status_emoji = {
            "In Progress": "🟡",
            "Design Phase": "🔵", 
            "EDEN Review": "🟠",
            "Planning": "⚪",
            "Completed": "🟢",
            "Stuck": "🔴"
        }.get(campaign["status"], "⚫")
        
        priority_indicator = {
            "High": "🔥",
            "Medium": "📋",
            "Low": "📝"
        }.get(campaign.get("priority", "Medium"), "📋")
        
        progress_bar = "█" * (campaign["progress"] // 10) + "░" * (10 - campaign["progress"] // 10)
        
        campaign_blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{campaign['name']}* {priority_indicator}\n{status_emoji} {campaign['status']} | Progress: {campaign['progress']}% [{progress_bar}]\n👤 {campaign['assignee']} | 📅 Due: {campaign['due_date']}\n🔄 Next: {campaign['next_task']} | Tasks: {campaign['completed_tasks']}/{campaign['total_tasks']}"
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "Open Board"},
                "action_id": f"open_monday_board_{campaign['id']}",
                "url": campaign["board_url"]
            }
        })
        
    return campaign_blocks

def create_integrated_dashboard_modal():
    """Create an integrated dashboard showing both Monday.com campaigns and Google Calendar events."""
    try:
        # Get data from both systems
        calendar_blocks = create_google_calendar_view()
        campaign_blocks = create_monday_campaigns_view()
        
        blocks = [
            create_banner(),
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*📊 Integrated Campaign Dashboard*\nReal-time view of campaigns and upcoming events"}
            },
            {"type": "divider"}
        ]
        
        # Monday.com Campaigns Section
        blocks.extend([
            {
                "type": "section", 
                "text": {"type": "mrkdwn", "text": "*📋 Active Campaigns (Monday.com)*"}
            },
            {"type": "divider"}
        ])
        
        # Add first 3 campaigns
        for i, block in enumerate(campaign_blocks[:3]):
            blocks.append(block)
            if i < len(campaign_blocks[:3]) - 1:
                blocks.append({"type": "divider"})
        
        # Google Calendar Events Section
        blocks.extend([
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*� Upcoming Events (Google Calendar)*"}
            },
            {"type": "divider"}
        ])
        
        # Add first 3 events
        for i, block in enumerate(calendar_blocks[:3]):
            blocks.append(block)
            if i < len(calendar_blocks[:3]) - 1:
                blocks.append({"type": "divider"})
        
        # Navigation and actions
        blocks.extend([
            {"type": "divider"},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📋 View All Campaigns"},
                        "action_id": "open_monday_dashboard",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📅 View All Events"},
                        "action_id": "open_calendar_dashboard"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🔄 Refresh Data"},
                        "action_id": "refresh_dashboard_data"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "➕ Create Campaign"},
                        "action_id": "create_campaign"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📅 Add Event"},
                        "action_id": "create_calendar_event"
                    }
                ]
            }
        ])
        
        return {
            "type": "modal",
            "callback_id": "integrated_dashboard",
            "title": {"type": "plain_text", "text": "Campaign Dashboard"},
            "blocks": blocks,
            "close": {"type": "plain_text", "text": "Close"}
        }
        
    except Exception as e:
        logger.error(f"Error creating integrated dashboard: {e}")
        return create_error_modal("Dashboard Error", "Unable to load integrated dashboard data.")


# CACHING POLICY: Dashboard modals are NOT cached to ensure fresh data.
# Always return a new modal instance to ensure real-time data consistency.
def create_main_dashboard():
    """Create the main dashboard modal with Monday.com and Google Calendar integration.
    Always returns a new modal object with fresh data. NOT cached for real-time updates."""
    try:
        # Return a fresh integrated dashboard modal every time
        return create_integrated_dashboard_modal()
    except Exception as e:
        logger.error(f"Error creating main dashboard: {e}")
        return create_error_modal("Dashboard Error", "Unable to load dashboard. Please try again.")

def create_monday_dashboard_modal():
    """Create Monday.com-focused dashboard showing active campaigns and tasks."""
    try:
        # This would fetch real data in production
        campaigns = [
            {
                "name": "Summer Product Launch",
                "status": "In Progress",
                "progress": 75,
                "next_task": "Creative Review",
                "assignee": "Kelly Redding",
                "due_date": "2025-07-27",
                "board_url": "https://fetchrewards.monday.com/boards/12345"
            },
            {
                "name": "Q3 Email Campaign",
                "status": "Design Phase",
                "progress": 45,
                "next_task": "Content Creation",
                "assignee": "Jheryl",
                "due_date": "2025-07-30",
                "board_url": "https://fetchrewards.monday.com/boards/12346"
            },
            {
                "name": "Community Meetup - Chicago",
                "status": "EDEN Review",
                "progress": 80,
                "next_task": "Final Approval",
                "assignee": "Karen or Kate",
                "due_date": "2025-07-25",
                "board_url": "https://fetchrewards.monday.com/boards/12347"
            }
        ]
        
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*📋 Monday.com Dashboard*\nActive campaigns and upcoming tasks"}
            },
            {"type": "divider"}
        ]
        
        # Add campaign blocks
        for campaign in campaigns:
            status_emoji = {
                "In Progress": "🟡",
                "Design Phase": "🔵", 
                "EDEN Review": "🟠",
                "Completed": "🟢",
                "Stuck": "🔴"
            }.get(campaign["status"], "⚫")
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{campaign['name']}*\n{status_emoji} {campaign['status']} | Progress: {campaign['progress']}%\n👤 {campaign['assignee']} | 📅 Due: {campaign['due_date']}\n🔄 Next: {campaign['next_task']}"
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Open in Monday"},
                    "action_id": f"open_monday_board",
                    "url": campaign["board_url"]
                }
            })
            blocks.append({"type": "divider"})
        
        # Add action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "📊 Task Summary"},
                    "action_id": "view_task_summary"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "📈 Progress Report"},
                    "action_id": "view_progress_report"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "← Back to Dashboard"},
                    "action_id": "back_to_main_dashboard"
                }
            ]
        })
        
        return {
            "type": "modal",
            "callback_id": "monday_dashboard",
            "title": {"type": "plain_text", "text": "Monday.com Dashboard"},
            "blocks": blocks,
            "close": {"type": "plain_text", "text": "Close"}
        }
    except Exception as e:
        logger.error(f"Error creating Monday.com dashboard: {e}")
        return create_error_modal("Monday.com Error", "Unable to load Monday.com data.")

def create_calendar_dashboard_modal():
    """Create Google Calendar-focused dashboard showing upcoming events."""
    try:
        # This would fetch real data in production
        events = [
            {
                "title": "Summer Launch Campaign Kickoff",
                "date": "2025-07-25",
                "time": "10:00 AM - 11:30 AM",
                "location": "Conference Room A",
                "attendees": ["kelly.redding@fetchrewards.com", "karen.lowry@fetchrewards.com"],
                "type": "planning"
            },
            {
                "title": "Q3 Marketing Review",
                "date": "2025-07-26",
                "time": "2:00 PM - 3:00 PM", 
                "location": "Virtual Meeting",
                "attendees": ["kate.jeffries@fetchrewards.com"],
                "type": "review"
            },
            {
                "title": "Community Meetup - Chicago",
                "date": "2025-07-28",
                "time": "All Day",
                "location": "Chicago Convention Center",
                "attendees": ["karen.lowry@fetchrewards.com", "kate.jeffries@fetchrewards.com"],
                "type": "event"
            },
            {
                "title": "Email Campaign Content Review",
                "date": "2025-07-29",
                "time": "9:00 AM - 10:00 AM",
                "location": "Marketing Office",
                "attendees": ["jheryl@fetchrewards.com", "kelly.redding@fetchrewards.com"],
                "type": "content"
            }
        ]
        
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*📅 Google Calendar Dashboard*\nUpcoming campaign events and deadlines"}
            },
            {"type": "divider"}
        ]
        
        # Group events by date
        from datetime import datetime
        today = datetime.now().date()
        
        for event in events:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
            days_until = (event_date - today).days
            
            if days_until == 0:
                date_indicator = "🔴 Today"
            elif days_until == 1:
                date_indicator = "🟡 Tomorrow"
            elif days_until <= 3:
                date_indicator = f"🟠 In {days_until} days"
            else:
                date_indicator = f"📅 {event['date']}"
            
            type_emoji = {
                "planning": "📋",
                "review": "👁️",
                "event": "🎉",
                "content": "✍️"
            }.get(event["type"], "📅")
            
            attendee_count = len(event["attendees"])
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{event['title']}*\n{date_indicator} | {event['time']}\n📍 {event['location']} | 👥 {attendee_count} attendees\n{type_emoji} {event['type'].title()} Meeting"
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Details"},
                    "action_id": f"view_event_details"
                }
            })
            blocks.append({"type": "divider"})
        
        # Add calendar actions
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "📅 Add Event"},
                    "action_id": "create_calendar_event",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🔄 Sync Calendar"},
                    "action_id": "sync_calendar_data"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "← Back to Dashboard"},
                    "action_id": "back_to_main_dashboard"
                }
            ]
        })
        
        return {
            "type": "modal",
            "callback_id": "calendar_dashboard",
            "title": {"type": "plain_text", "text": "Calendar Dashboard"},
            "blocks": blocks,
            "close": {"type": "plain_text", "text": "Close"}
        }
    except Exception as e:
        logger.error(f"Error creating calendar dashboard: {e}")
        return create_error_modal("Calendar Error", "Unable to load calendar data.")

def create_error_modal(title: str, message: str):
    """Create a simple error modal."""
    return {
        "type": "modal",
        "callback_id": "error_modal",
        "title": {"type": "plain_text", "text": title},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"❌ *{message}*"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "← Back"},
                        "action_id": "back_to_main_dashboard"
                    }
                ]
            }
        ],
        "close": {"type": "plain_text", "text": "Close"}
    }

def create_event_modal():
    """Create event management modal."""
    modal = {
        "type": "modal",
        "callback_id": "create_event_modal",
        "title": {"type": "plain_text", "text": "Event Management"},
        "blocks": [
            {
                "type": "input",
                "block_id": "event_name",
                "element": {"type": "plain_text_input", "action_id": "name_input"},
                "label": {"type": "plain_text", "text": "Event Name"}
            },
            {
                "type": "input",
                "block_id": "event_type",
                "element": {
                    "type": "static_select", 
                    "action_id": "type_select",
                    "placeholder": {"type": "plain_text", "text": "Select event type..."},
                    "options": [
                        {"text": {"type": "plain_text", "text": "Product Launch"}, "value": "product_launch"},
                        {"text": {"type": "plain_text", "text": "Webinar"}, "value": "webinar"},
                        {"text": {"type": "plain_text", "text": "Conference"}, "value": "conference"},
                        {"text": {"type": "plain_text", "text": "Workshop"}, "value": "workshop"}
                    ]
                },
                "label": {"type": "plain_text", "text": "Event Type"}
            },
            {
                "type": "input",
                "block_id": "event_description",
                "element": {"type": "plain_text_input", "multiline": True, "action_id": "description_input"},
                "label": {"type": "plain_text", "text": "Event Description"}
            }
        ],
        "submit": {"type": "plain_text", "text": "Create Event"},
        "close": {"type": "plain_text", "text": "← Back"}
    }
    return modal

def create_ai_suggestions_modal(suggestions=None):
    """Create AI suggestions modal showing actual suggestions."""
    if not suggestions:
        suggestions = [
            "Summer Product Launch Event - Interactive demos + email campaign",
            "Back-to-School Cashback Blitz - Email series with social media",
            "Holiday Shopping Rewards Event - In-store activations + email nurture",
            "New User Onboarding Workshop - Live sessions + email follow-up",
            "Brand Partnership Launch - Event announcement + email marketing"
        ]
    
    suggestion_blocks = []
    for i, suggestion in enumerate(suggestions):
        suggestion_blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"• {suggestion}"},
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "Use This"},
                "action_id": f"use_suggestion_{i}",
                "value": suggestion
            }
        })
    
    modal = {
        "type": "modal",
        "callback_id": "ai_suggestions_results",
        "title": {"type": "plain_text", "text": "AI Campaign Suggestions"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*AI-Generated Campaign Ideas*\nClick 'Use This' to create a campaign from any suggestion:"}
            },
            {"type": "divider"},
            *suggestion_blocks,
            {"type": "divider"},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Generate More"},
                        "action_id": "generate_more_suggestions"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "← Back to Hub"},
                        "action_id": "back_to_campaign_hub"
                    }
                ]
            }
        ],
        "close": {"type": "plain_text", "text": "Cancel"}
    }
    return modal

def create_content_modal():
    """Create content creation modal."""
    modal = {
        "type": "modal",
        "callback_id": "create_content_modal",
        "title": {"type": "plain_text", "text": "Content Creation"},
        "blocks": [
            {
                "type": "input",
                "block_id": "content_title",
                "element": {"type": "plain_text_input", "action_id": "title_input"},
                "label": {"type": "plain_text", "text": "Content Title"}
            },
            {
                "type": "input",
                "block_id": "content_type",
                "element": {
                    "type": "static_select", 
                    "action_id": "type_select",
                    "placeholder": {"type": "plain_text", "text": "Select content type..."},
                    "options": [
                        {"text": {"type": "plain_text", "text": "Blog Post"}, "value": "blog"},
                        {"text": {"type": "plain_text", "text": "Social Media"}, "value": "social"},
                        {"text": {"type": "plain_text", "text": "Email Newsletter"}, "value": "email"},
                        {"text": {"type": "plain_text", "text": "Video Script"}, "value": "video"}
                    ]
                },
                "label": {"type": "plain_text", "text": "Content Type"}
            },
            {
                "type": "input",
                "block_id": "content_description",
                "element": {"type": "plain_text_input", "multiline": True, "action_id": "description_input"},
                "label": {"type": "plain_text", "text": "Content Description"}
            }
        ],
        "submit": {"type": "plain_text", "text": "Create Content"},
        "close": {"type": "plain_text", "text": "← Back"}
    }
    return modal

def create_suggestions_results_modal(suggestions: list = None, suggestion_type: str = "campaign"):
    """Create suggestions results modal with dropdown actions."""
    if not suggestions:
        suggestions = ["Email Campaign: Summer Sale", "Social Media: Product Launch", "Content Marketing: Blog Series"]
    
    suggestion_text = "\n".join([f"• {suggestion}" for suggestion in suggestions])
    
    modal = {
        "type": "modal",
        "callback_id": f"{suggestion_type}_suggestions_results",
        "title": {"type": "plain_text", "text": f"{suggestion_type.title()} Suggestions"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*AI-Generated {suggestion_type.title()} Suggestions*\n\n{suggestion_text}"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "static_select",
                        "placeholder": {"type": "plain_text", "text": "Choose action..."},
                        "action_id": "suggestion_action",
                        "options": [
                            {"text": {"type": "plain_text", "text": "Approve All"}, "value": "approve_all"},
                            {"text": {"type": "plain_text", "text": "Select Individual"}, "value": "select_individual"},
                            {"text": {"type": "plain_text", "text": "Generate New"}, "value": "generate_new"},
                            {"text": {"type": "plain_text", "text": "Export to Monday.com"}, "value": "export_monday"}
                        ]
                    }
                ]
            }
        ],
        "submit": {"type": "plain_text", "text": "Execute"},
        "close": {"type": "plain_text", "text": "← Back"}
    }
    return modal

def create_slides_modal():
    """Create slides creation modal."""
    modal = {
        "type": "modal",
        "callback_id": "create_slides_modal",
        "title": {"type": "plain_text", "text": "Create Presentation"},
        "blocks": [
            {
                "type": "input",
                "block_id": "presentation_title",
                "element": {"type": "plain_text_input", "action_id": "title_input"},
                "label": {"type": "plain_text", "text": "Presentation Title"}
            },
            {
                "type": "input",
                "block_id": "slide_template",
                "element": {"type": "static_select", "action_id": "template_select", 
                          "placeholder": {"type": "plain_text", "text": "Choose template..."},
                          "options": [
                              {"text": {"type": "plain_text", "text": "Marketing Report"}, "value": "marketing"},
                              {"text": {"type": "plain_text", "text": "Sales Presentation"}, "value": "sales"},
                              {"text": {"type": "plain_text", "text": "Campaign Review"}, "value": "campaign"}
                          ]},
                "label": {"type": "plain_text", "text": "Template"}
            },
            {
                "type": "input",
                "block_id": "slides_content",
                "element": {"type": "plain_text_input", "multiline": True, "action_id": "content_input"},
                "label": {"type": "plain_text", "text": "Content Outline"},
                "optional": True
            }
        ],
        "submit": {"type": "plain_text", "text": "Create Slides"},
        "close": {"type": "plain_text", "text": "← Back"}
    }
    return modal

def create_suggestion_confirmation_modal(suggestion: str = "Selected suggestion"):
    """Create suggestion confirmation modal."""
    return {
        "type": "modal",
        "callback_id": "suggestion_confirmation",
        "title": {"type": "plain_text", "text": "Confirm Suggestion"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Confirm the following suggestion:*\n\n✅ {suggestion}"}
            }
        ],
        "submit": {"type": "plain_text", "text": "Confirm"},
        "close": {"type": "plain_text", "text": "← Back"}
    }

def create_campaign_modal():
    """Create campaign creation modal."""
    modal = {
        "type": "modal",
        "callback_id": "create_campaign_modal",
        "title": {"type": "plain_text", "text": "Create Campaign"},
        "blocks": [
            {
                "type": "input",
                "block_id": "campaign_name",
                "element": {"type": "plain_text_input", "action_id": "name_input"},
                "label": {"type": "plain_text", "text": "Campaign Name"}
            },
            {
                "type": "input",
                "block_id": "campaign_goal",
                "element": {"type": "plain_text_input", "action_id": "goal_input"},
                "label": {"type": "plain_text", "text": "Campaign Goal"}
            },
            {
                "type": "input",
                "block_id": "campaign_target",
                "element": {"type": "plain_text_input", "action_id": "target_input"},
                "label": {"type": "plain_text", "text": "Target Audience"}
            },
            {
                "type": "input",
                "block_id": "campaign_type",
                "element": {"type": "static_select", "action_id": "type_select",
                          "placeholder": {"type": "plain_text", "text": "Select campaign type..."},
                          "options": [
                              {"text": {"type": "plain_text", "text": "Physical Event Campaign"}, "value": "physical_event"},
                              {"text": {"type": "plain_text", "text": "Email-Only Campaign"}, "value": "email_only"},
                              {"text": {"type": "plain_text", "text": "Email Marketing"}, "value": "email"},
                              {"text": {"type": "plain_text", "text": "Social Media"}, "value": "social"},
                              {"text": {"type": "plain_text", "text": "Content Marketing"}, "value": "content"}
                          ]},
                "label": {"type": "plain_text", "text": "Campaign Type"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "← Back to Hub"},
                        "action_id": "back_to_campaign_hub"
                    }
                ]
            }
        ],
        "submit": {"type": "plain_text", "text": "Create Campaign"},
        "close": {"type": "plain_text", "text": "Cancel"}
    }
    return modal

def create_banner():
    """Create a banner block for modals."""
    return {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "🚀 *Marketing Bot* - Streamlined Campaign Management"}
    }

def register_core_modals(app):
    """Register all core modal handlers."""
    logger.info("✅ Core modals registered with enhanced dashboard functionality")
    # Modal handlers would be registered here
    pass

# Quick access functions for easy import
def get_main_dashboard():
    """Quick access to main dashboard modal."""
    return create_main_dashboard()

def get_monday_dashboard():
    """Quick access to Monday.com dashboard modal."""
    return create_monday_dashboard_modal()

def get_calendar_dashboard():
    """Quick access to calendar dashboard modal."""
    return create_calendar_dashboard_modal()

def get_integrated_dashboard():
    """Quick access to integrated dashboard modal."""
    return create_integrated_dashboard_modal()

def create_content_generator_modal():
    """Create content generator modal with AI-generated suggestions."""
    sample_content = {
        "email_subject": "🎉 Exclusive Summer Sale - Up to 50% Off!",
        "email_body": "Dear Valued Customer,\n\nSummer is here and we're celebrating with amazing deals! Get up to 50% off on our entire collection. Don't miss out on these limited-time offers.\n\nShop now and save big!\n\nBest regards,\nYour Marketing Team",
        "social_post": "🌞 Summer vibes are here! ☀️ Enjoy up to 50% off our entire collection. Limited time only! #SummerSale #Savings #Fashion",
        "blog_title": "10 Essential Summer Fashion Trends You Need to Know",
        "blog_intro": "As temperatures rise, it's time to refresh your wardrobe with the latest summer trends. From breezy fabrics to vibrant colors, this season's fashion is all about comfort meets style..."
    }
    
    modal = {
        "type": "modal",
        "callback_id": "content_generator_modal",
        "title": {"type": "plain_text", "text": "AI Content Generator"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*🤖 AI-Generated Content Ready for Use*"}
            },
            {
                "type": "divider"
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input", 
                    "action_id": "email_subject",
                    "initial_value": sample_content["email_subject"]
                },
                "label": {"type": "plain_text", "text": "📧 Email Subject Line"}
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input", 
                    "multiline": True, 
                    "action_id": "email_body",
                    "initial_value": sample_content["email_body"]
                },
                "label": {"type": "plain_text", "text": "📝 Email Content"}
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input", 
                    "action_id": "social_post",
                    "initial_value": sample_content["social_post"]
                },
                "label": {"type": "plain_text", "text": "📱 Social Media Post"}
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input", 
                    "action_id": "blog_title",
                    "initial_value": sample_content["blog_title"]
                },
                "label": {"type": "plain_text", "text": "📰 Blog Post Title"}
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input", 
                    "multiline": True, 
                    "action_id": "blog_intro",
                    "initial_value": sample_content["blog_intro"]
                },
                "label": {"type": "plain_text", "text": "✍️ Blog Introduction"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🔄 Regenerate Content"},
                        "action_id": "regenerate_content",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📋 Copy All"},
                        "action_id": "copy_all_content"
                    }
                ]
            }
        ],
        "submit": {"type": "plain_text", "text": "Use Content"},
        "close": {"type": "plain_text", "text": "← Back"}
    }
    return modal

def create_campaign_optimizer_modal():
    """Create campaign optimizer modal with AI suggestions."""
    return {
        "type": "modal",
        "callback_id": "campaign_optimizer_modal",
        "title": {"type": "plain_text", "text": "Campaign Optimizer"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*🎯 AI Campaign Optimization Suggestions*"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Current Campaign Performance:*\n• Open Rate: 24.5% (+2.3% vs. average)\n• Click Rate: 4.8% (+1.2% vs. average)\n• Conversion Rate: 2.1% (-0.5% vs. goal)"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*🚀 Optimization Recommendations:*\n✅ A/B test subject lines with emojis\n✅ Segment audience by purchase history\n✅ Add urgency elements to CTAs\n✅ Optimize send time to 2-4 PM"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "static_select",
                        "placeholder": {"type": "plain_text", "text": "Apply optimization..."},
                        "action_id": "optimization_action",
                        "options": [
                            {"text": {"type": "plain_text", "text": "Apply All Suggestions"}, "value": "apply_all"},
                            {"text": {"type": "plain_text", "text": "Schedule A/B Test"}, "value": "ab_test"},
                            {"text": {"type": "plain_text", "text": "Audience Segmentation"}, "value": "segment"},
                            {"text": {"type": "plain_text", "text": "Custom Optimization"}, "value": "custom"}
                        ]
                    }
                ]
            }
        ],
        "submit": {"type": "plain_text", "text": "Apply"},
        "close": {"type": "plain_text", "text": "← Back"}
    }

def create_audience_analysis_modal():
    """Create audience analysis modal with insights."""
    return {
        "type": "modal",
        "callback_id": "audience_analysis_modal",
        "title": {"type": "plain_text", "text": "Audience Analysis"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*👥 Audience Insights & Analytics*"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Demographics:*\n• Age: 25-45 (68%)\n• Gender: 52% Female, 48% Male\n• Location: Urban areas (73%)"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Behavior Patterns:*\n• Most active: Tue-Thu, 2-4 PM\n• Preferred content: How-to guides (43%)\n• Average engagement: 5.2 minutes\n• Device preference: Mobile (67%)"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*🎯 Targeting Recommendations:*\n✅ Focus on mobile-first content\n✅ Schedule posts for midweek afternoons\n✅ Create more educational content\n✅ Target urban professionals 25-45"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📊 Full Report"},
                        "action_id": "full_report",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🎯 Create Segments"},
                        "action_id": "create_segments"
                    }
                ]
            }
        ],
        "submit": {"type": "plain_text", "text": "Export Data"},
        "close": {"type": "plain_text", "text": "← Back"}
    }

@lru_cache(maxsize=128)  # Limit cache size for memory efficiency
def get_ai_tool_modal(action_id: str) -> Dict[str, Any]:
    """Retrieve AI tool modal with caching for static modals only.
    
    Note: Only use for modals that don't change based on user context or real-time data.
    Dashboard modals and user-specific modals should NOT be cached.
    """
    if action_id == "content_gen":
        return create_content_generator_modal()
    elif action_id == "campaign_opt":
        return create_campaign_optimizer_modal()
    elif action_id == "audience_analysis":
        return create_audience_analysis_modal()
    else:
        return {
            "type": "modal",
            "title": {"type": "plain_text", "text": "Error"},
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "plain_text", "text": "Invalid selection."}
                }
            ]
        }

# Update the handle_ai_tool_selection function to use caching
def handle_ai_tool_selection(action_id: str) -> Dict[str, Any]:
    """Handle AI tool selection and return the corresponding modal."""
    return get_ai_tool_modal(action_id)

# Ensure the AI tools modal action is properly linked
async def handle_dashboard_action(action_id: str):
    """Handle dashboard action selection."""
    if action_id == "ai_suggestions":
        return create_ai_suggestions_modal()
    elif action_id == "content_creation":
        return create_content_modal()
    elif action_id == "event_management":
        return create_event_modal()
    elif action_id == "create_campaign":
        return create_campaign_modal()
    elif action_id == "open_monday_dashboard":
        return create_monday_dashboard_modal()
    elif action_id == "open_calendar_dashboard":
        return create_calendar_dashboard_modal()
    elif action_id == "back_to_main_dashboard":
        return create_main_dashboard()
    elif action_id == "refresh_dashboard_data":
        # Refresh and return the integrated dashboard
        return create_integrated_dashboard_modal()
    elif action_id == "create_calendar_event":
        return create_event_modal()
    else:
        return {
            "type": "modal",
            "title": {"type": "plain_text", "text": "Error"},
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "plain_text", "text": "Invalid selection."}
                }
            ]
        }

# Export key dashboard functions for easy access from other modules
__all__ = [
    'create_main_dashboard',
    'create_monday_dashboard_modal', 
    'create_calendar_dashboard_modal',
    'create_integrated_dashboard_modal',
    'get_main_dashboard',
    'get_monday_dashboard',
    'get_calendar_dashboard', 
    'get_integrated_dashboard',
    'handle_dashboard_action',
    'handle_monday_dashboard_actions',
    'handle_calendar_dashboard_actions',
    'create_google_calendar_view',
    'create_monday_campaigns_view',
    'fetch_google_calendar_events',
    'fetch_monday_campaigns'
]

async def handle_monday_dashboard_actions(action_id: str, campaign_id: str = None):
    """Handle Monday.com dashboard specific actions."""
    if action_id == "view_task_summary":
        return create_task_summary_modal()
    elif action_id == "view_progress_report":
        return create_progress_report_modal()
    elif action_id == "open_monday_board":
        # This would open the Monday.com board in a new tab
        return None
    else:
        return create_monday_dashboard_modal()

async def handle_calendar_dashboard_actions(action_id: str, event_id: str = None):
    """Handle Google Calendar dashboard specific actions."""
    if action_id == "create_calendar_event":
        return create_event_modal()
    elif action_id == "view_event_details":
        return create_event_details_modal(event_id)
    elif action_id == "sync_calendar_data":
        # This would trigger a calendar sync
        return create_calendar_dashboard_modal()
    else:
        return create_calendar_dashboard_modal()

def create_task_summary_modal():
    """Create task summary modal showing Monday.com task breakdown."""
    return {
        "type": "modal",
        "callback_id": "task_summary",
        "title": {"type": "plain_text", "text": "Task Summary"},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📊 Task Summary*\n\n*By Status:*\n🟢 Completed: 12 tasks\n🟡 In Progress: 8 tasks\n🔴 Overdue: 2 tasks\n⚪ Not Started: 5 tasks\n\n*By Assignee:*\n👤 Kelly Redding: 9 tasks\n👤 Jheryl: 7 tasks\n👤 Karen/Kate: 11 tasks"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "← Back to Monday"},
                        "action_id": "open_monday_dashboard"
                    }
                ]
            }
        ],
        "close": {"type": "plain_text", "text": "Close"}
    }

def create_progress_report_modal():
    """Create progress report modal showing campaign analytics."""
    return {
        "type": "modal",
        "callback_id": "progress_report",
        "title": {"type": "plain_text", "text": "Progress Report"},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📈 Campaign Progress Report*\n\n*This Week:*\n• 3 campaigns launched\n• 14 tasks completed\n• 2 campaigns reached 90%+ completion\n\n*Performance Metrics:*\n• Average completion time: 5.2 days\n• On-time delivery: 85%\n• Team utilization: 92%\n\n*Upcoming Deadlines:*\n• 3 tasks due this week\n• 2 major milestones next week"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📊 Full Report"},
                        "action_id": "export_full_report"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "← Back to Monday"},
                        "action_id": "open_monday_dashboard"
                    }
                ]
            }
        ],
        "close": {"type": "plain_text", "text": "Close"}
    }

def create_event_details_modal(event_id: str = None):
    """Create event details modal for calendar events."""
    # Mock event details - would fetch real data based on event_id
    event = {
        "title": "Summer Launch Campaign Kickoff",
        "date": "July 25, 2025",
        "time": "10:00 AM - 11:30 AM",
        "location": "Conference Room A",
        "description": "Kickoff meeting for the Summer Product Launch campaign. We'll review timeline, deliverables, and assign responsibilities.",
        "attendees": [
            "kelly.redding@fetchrewards.com",
            "karen.lowry@fetchrewards.com", 
            "kate.jeffries@fetchrewards.com"
        ],
        "agenda": [
            "Campaign overview and objectives",
            "Timeline review",
            "Deliverable assignments",
            "Q&A session"
        ]
    }
    
    return {
        "type": "modal",
        "callback_id": "event_details",
        "title": {"type": "plain_text", "text": "Event Details"},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{event['title']}*\n\n📅 {event['date']}\n🕐 {event['time']}\n📍 {event['location']}\n\n*Description:*\n{event['description']}"
                }
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn", 
                    "text": f"*👥 Attendees ({len(event['attendees'])}):*\n" + "\n".join([f"• {attendee}" for attendee in event['attendees']])
                }
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📋 Agenda:*\n" + "\n".join([f"• {item}" for item in event['agenda']])
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📝 Edit Event"},
                        "action_id": "edit_calendar_event"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "← Back to Calendar"},
                        "action_id": "open_calendar_dashboard"
                    }
                ]
            }
        ],
        "close": {"type": "plain_text", "text": "Close"}
    }
