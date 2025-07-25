"""
Core Slash Commands Handler - Unified Campaign Workflow
======================================================
Implements the unified campaign workflow system per AC requirements
"""

import logging

from utils.slack_formatting import SlackFormatter, format_modal_header, format_divider, format_button_section, format_context_footer
from modals.core_modal_system import handle_modal_navigation

logger = logging.getLogger(__name__)

def register_slash_commands(app):
    """Register core slash commands with unified campaign workflow."""
    
    @app.command("/help")
    async def handle_help_command(ack, body, client):
        """Handle the /help command to open the Fetch Campaign Hub (AC #1)."""
        await ack()
        
        user_id = body.get('user_id', 'unknown')
        trigger_id = body.get('trigger_id')
        
        try:
            logger.info(f"Opening Fetch Campaign Hub for user {user_id}")
            
            # Create the unified campaign hub modal with exactly 7 blocks per AC
            modal_view = create_campaign_hub_modal()
            
            await handle_modal_navigation(client, {"trigger_id": trigger_id}, modal_view, "open")
            
            logger.info(f"Successfully opened Campaign Hub for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error opening Campaign Hub: {e}")
            # Send fallback message
            try:
                await client.chat_postMessage(
                    channel=user_id,
                    text="Sorry, there was an error opening the Campaign Hub. Please try again."
                )
            except Exception as fallback_error:
                logger.error(f"Fallback error: {fallback_error}")

def create_campaign_hub_modal():
    """Create the Fetch Campaign Hub modal with exactly 7 blocks (AC #1)."""
    
    return {
        "type": "modal",
        "callback_id": "fetch_campaign_hub",
        "title": {"type": "plain_text", "text": "Fetch Campaign Hub"},
        "close": {"type": "plain_text", "text": "Close"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Welcome to Fetch Campaign Hub*\nStreamline your marketing campaigns with unified workflows."}
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Physical Event Campaign*\nEvent planning + email invitations (Kate/Karen + Jheryl)"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Create Physical Event"},
                    "action_id": "create_physical_event_campaign",
                    "style": "primary"
                }
            },
            {
                "type": "section", 
                "text": {"type": "mrkdwn", "text": "*Email-Only Campaign*\nEmail workflows only (Jheryl)"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Create Email Campaign"},
                    "action_id": "create_email_only_campaign"
                }
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*AI Suggestions*\nGenerate campaign ideas for either workflow type"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "AI Suggestions"},
                    "action_id": "ai_suggestions"
                }
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": "Required: Event name, date, location. Optional: Campaign goals for full automation"}]
            }
        ]
    }
