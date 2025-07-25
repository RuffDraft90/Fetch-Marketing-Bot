"""
Simple, Clean Campaign Handlers
==============================
Clean implementation of Jheryl's workflow requirements
"""

import logging
from modals.core_modal_system import create_campaign_modal, create_ai_suggestions_modal, handle_modal_navigation

logger = logging.getLogger(__name__)

def register_simple_handlers(app):
    """Register clean, simple handlers."""
    
    @app.action("create_physical_event_campaign")
    async def handle_physical_event_campaign(ack, body, client):
        await ack()
        modal = create_campaign_modal()
        
        # Pre-fill for physical event
        for block in modal["blocks"]:
            if block.get("block_id") == "campaign_type":
                block["element"]["initial_option"] = {
                    "text": {"type": "plain_text", "text": "Physical Event Campaign"},
                    "value": "physical_event"
                }
        
        await handle_modal_navigation(client, body, modal, "auto")
        logger.info(f"Physical event campaign modal opened")
    
    @app.action("create_email_only_campaign") 
    async def handle_email_only_campaign(ack, body, client):
        await ack()
        modal = create_campaign_modal()
        
        # Pre-fill for email only
        for block in modal["blocks"]:
            if block.get("block_id") == "campaign_type":
                block["element"]["initial_option"] = {
                    "text": {"type": "plain_text", "text": "Email-Only Campaign"},
                    "value": "email_only"
                }
        
        await handle_modal_navigation(client, body, modal, "auto")
        logger.info(f"Email-only campaign modal opened")
    
    @app.action("ai_suggestions")
    async def handle_ai_suggestions(ack, body, client):
        await ack()
        modal = create_ai_suggestions_modal(None)  # Pass None for default suggestions
        await handle_modal_navigation(client, body, modal, "auto")
        logger.info(f"AI suggestions modal opened")
    
    @app.action("back_to_campaign_hub")
    async def handle_back_to_campaign_hub(ack, body, client):
        await ack()
        from handlers.core_slash_commands import create_campaign_hub_modal
        modal = create_campaign_hub_modal()
        await handle_modal_navigation(client, body, modal, "update")
        logger.info(f"Back to Campaign Hub")
    
    @app.action("view_campaign_dashboard")
    async def handle_view_dashboard(ack, body, client):
        await ack()
        # Just go back to Campaign Hub for now
        from handlers.core_slash_commands import create_campaign_hub_modal
        modal = create_campaign_hub_modal()
        await handle_modal_navigation(client, body, modal, "update")
        logger.info(f"Dashboard redirected to Campaign Hub")
    
    @app.action("refresh_dashboard")
    async def handle_refresh_dashboard(ack, body, client):
        await ack()
        # Just refresh by going back to Campaign Hub
        from handlers.core_slash_commands import create_campaign_hub_modal
        modal = create_campaign_hub_modal()
        await handle_modal_navigation(client, body, modal, "update")
        logger.info(f"Dashboard refreshed")
    
    # Form submission handlers for workflow integration
    @app.view("create_campaign_modal")
    async def handle_create_campaign_from_form(ack, body, client, view):
        await ack()
        try:
            # Extract form data
            values = view["state"]["values"]
            form_data = {}
            
            for block_id, block_values in values.items():
                for action_id, field_value in block_values.items():
                    if field_value.get("type") == "plain_text_input":
                        form_data[block_id] = field_value.get("value", "")
                    elif field_value.get("type") == "static_select":
                        selected_option = field_value.get("selected_option")
                        if selected_option:
                            form_data[block_id] = selected_option.get("value", "")
            
            # Process campaign creation
            campaign_name = form_data.get("campaign_name", "New Campaign")
            campaign_type = form_data.get("campaign_type", "email_only")
            
            # Create appropriate campaign based on type
            if campaign_type == "physical_event":
                logger.info(f"Creating physical event campaign: {campaign_name}")
                # Redirect to physical event workflow
                await client.chat_postMessage(
                    channel=body["user"]["id"],
                    text=f"✅ Physical Event Campaign '{campaign_name}' has been created with dual parent tickets (Event Planning + Email Campaign)"
                )
            else:
                logger.info(f"Creating email-only campaign: {campaign_name}")
                # Redirect to email-only workflow
                await client.chat_postMessage(
                    channel=body["user"]["id"],
                    text=f"✅ Email-Only Campaign '{campaign_name}' has been created with single parent ticket"
                )
                
        except Exception as e:
            logger.error(f"Form submission error: {e}")
            await client.chat_postMessage(
                channel=body["user"]["id"],
                text="❌ Error processing campaign form. Please try again."
            )
    
    # Add missing action handlers for better workflow integration
    @app.action("create_campaign_from_form")
    async def handle_campaign_form_button(ack, body, client):
        """Handle form-based campaign creation button."""
        await ack()
        modal = create_campaign_modal()
        await handle_modal_navigation(client, body, modal, "auto")
        logger.info("Campaign form modal opened")
    
    # Add individual use_suggestion handlers for AI suggestions workflow
    @app.action("use_suggestion_0")
    async def handle_use_suggestion_0(ack, body, client):
        await _handle_use_suggestion(ack, body, client, 0)
    
    @app.action("use_suggestion_1") 
    async def handle_use_suggestion_1(ack, body, client):
        await _handle_use_suggestion(ack, body, client, 1)
        
    @app.action("use_suggestion_2")
    async def handle_use_suggestion_2(ack, body, client):
        await _handle_use_suggestion(ack, body, client, 2)
        
    @app.action("use_suggestion_3")
    async def handle_use_suggestion_3(ack, body, client):
        await _handle_use_suggestion(ack, body, client, 3)
        
    @app.action("use_suggestion_4")
    async def handle_use_suggestion_4(ack, body, client):
        await _handle_use_suggestion(ack, body, client, 4)
    
    async def _handle_use_suggestion(ack, body, client, suggestion_index):
        """Helper function to handle AI suggestion usage."""
        await ack()
        try:
            # Get suggestion from button value
            actions = body.get("actions", [])
            suggestion = f"AI Suggestion {suggestion_index}"
            
            if actions and len(actions) > 0:
                suggestion = actions[0].get("value", suggestion)
            
            # Determine campaign type based on suggestion content
            if "event" in suggestion.lower() or "workshop" in suggestion.lower():
                campaign_type = "physical_event"
                workflow_type = "Physical Event Campaign"
            else:
                campaign_type = "email_only"
                workflow_type = "Email-Only Campaign"
            
            # Create pre-filled campaign modal
            modal = create_campaign_modal()
            
            # Pre-fill the modal with suggestion data
            for block in modal["blocks"]:
                if block.get("block_id") == "campaign_name" and " - " in suggestion:
                    block["element"]["initial_value"] = suggestion.split(" - ")[0]
                elif block.get("block_id") == "campaign_goal" and " - " in suggestion:
                    block["element"]["initial_value"] = suggestion.split(" - ")[1]
                elif block.get("block_id") == "campaign_type":
                    block["element"]["initial_option"] = {
                        "text": {"type": "plain_text", "text": workflow_type},
                        "value": campaign_type
                    }
            
            await handle_modal_navigation(client, body, modal, "auto")
            logger.info(f"Created campaign from AI suggestion {suggestion_index}: {suggestion}")
            
        except Exception as e:
            logger.error(f"Error handling suggestion {suggestion_index}: {e}")
    
    logger.info("✅ Simple handlers registered")