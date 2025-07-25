"""
Campaign Submission Handler
==========================
Processes actual campaign form submissions with Monday.com integration
"""

import logging
from services.monday_service import MondayService

logger = logging.getLogger(__name__)

def register_campaign_submission(app):
    """Register campaign form submission handler"""
    
    @app.view("create_campaign_modal")
    async def handle_campaign_submission(ack, body, client):
        await ack()
        
        user_id = body["user"]["id"]
        values = body["view"]["state"]["values"]
        
        # Extract form data
        campaign_name = values.get("campaign_name", {}).get("name_input", {}).get("value", "")
        campaign_goal = values.get("campaign_goal", {}).get("goal_input", {}).get("value", "")
        campaign_target = values.get("campaign_target", {}).get("target_input", {}).get("value", "")
        campaign_type = values.get("campaign_type", {}).get("type_select", {}).get("selected_option", {}).get("value", "email_only")
        
        logger.info(f"Campaign submission: {campaign_name} ({campaign_type}) by {user_id}")
        
        try:
            # Create Monday.com tickets based on campaign type
            monday = MondayService()
            
            if campaign_type == "physical_event":
                # Jheryl's Logic: Dual parent tickets for physical events
                result = await monday.create_physical_event_campaign(
                    name=campaign_name,
                    goal=campaign_goal,
                    target=campaign_target
                )
                message = f"✅ *Physical Event Campaign Created*\n\n*{campaign_name}*\n\n• Event Planning Board: {result['event_board_url']}\n• Email Campaign Board: {result['email_board_url']}\n• Assigned: Kate, Karen, Jheryl"
            else:
                # Jheryl's Logic: Single parent ticket for email-only
                result = await monday.create_email_only_campaign(
                    name=campaign_name,
                    goal=campaign_goal,
                    target=campaign_target
                )
                message = f"✅ *Email-Only Campaign Created*\n\n*{campaign_name}*\n\n• Campaign Board: {result['board_url']}\n• Assigned: Jheryl"
            
            # Send success message
            await client.chat_postMessage(
                channel=user_id,
                text=message
            )
            
        except Exception as e:
            logger.error(f"Campaign creation failed: {e}")
            await client.chat_postMessage(
                channel=user_id,
                text=f"❌ Failed to create campaign: {str(e)}"
            )
    
    logger.info("✅ Campaign submission handler registered")