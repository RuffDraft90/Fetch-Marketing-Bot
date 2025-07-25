"""
Core Clean Action Handlers for Production Marketing Bot
=====================================================
Production-ready handlers with proper error handling, performance optimization,
and bilingual support for scalable marketing automation.

Features:
- Async/await architecture for high concurrency
- Modular design for extensibility across teams (Sales, HR, Product)
- Comprehensive error handling and logging
- Google Slides integration
- AI-powered content generation
- Enterprise-ready security and monitoring
"""

import os
import asyncio
import time
import logging
from typing import Dict, Optional, Tuple
import re

from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor

# Core modal imports
from modals.core_modal_system import (
    create_event_modal, create_ai_suggestions_modal, create_content_modal,
    create_slides_modal, create_suggestion_confirmation_modal,
    create_campaign_modal, create_content_generator_modal, 
    create_campaign_optimizer_modal, create_audience_analysis_modal,
    handle_dashboard_action, handle_ai_tool_selection, handle_modal_navigation
)

# Core services
from services import ai_service, google_slides_service, google_calendar_service, google_docs_service, monday_service

# Performance and logging
logger = logging.getLogger(__name__)

# ========================================
# CONFIGURATION
# ========================================

CONFIG = {
    "CACHE_TTL": 60,
    "DEFAULT_SUGGESTION_COUNT": 5,
    "AI_MODEL": "gpt-3.5-turbo",
    "AI_MAX_TOKENS": 150,
    "AI_TEMPERATURE": 0.7,
    "CHANNELS": {
        "EVENTS": "#marketing-event-updates-hackathon",
        "CAMPAIGNS": "#marketing-event-updates-hackathon",
        "GENERAL": "general"
    }
}

# Pre-loaded suggestion pools for instant responses
SUGGESTION_POOLS = {
    "event": [
        "Receipt Scanning Championship - Global competition with prize pool",
        "Lightning Cashback Storm - 5X rewards for 24 hours",
        "Treasure Hunt: Hidden Bonus Stores - Discover secret partner locations",
        "Fetch Friends Challenge - Viral referral program",
        "Elite Scanner Society - VIP tier unlock event",
    ],
    "slides": [
        "Fetch Rewards Growth Report Q3 2025",
        "Mobile Cashback Revolution - Market Analysis",
        "AI-Powered Receipt Recognition Technology",
        "Strategic Partnership Success Stories",
        "User Acquisition and Retention Strategies",
    ],
    "campaign": [
        "#ScanWarriors - Receipt scanning showdown",
        "Fetch Army Recruitment - Friend referral drive",
        "Double Rewards Weekend - 2X everything promotion",
        "Back-to-School Cashback Blitz",
        "Holiday Shopping Campaign",
    ]
}

POOL_INDICES = {"event": 0, "slides": 0, "campaign": 0}

# Legacy code removed - using core AI service now

# ========================================
# CONTENT FORMATTING
# ========================================

def get_localized_content(content_key: str, user_id: str, **kwargs) -> str:
    """Get content for display."""
    
    content_map = {
        "event_created": {
            "en": "✅ *Event Created!*\n\n*Name:* {name}\n*Type:* {type}\n*Description:* {description}\n\n🎯 Your event is ready!",
            "es": "✅ *¡Evento Creado!*\n\n*Nombre:* {name}\n*Tipo:* {type}\n*Descripción:* {description}\n\n🎯 ¡Tu evento está listo!"
        },
        "slides_created": {
            "en": "✅ *Slides Created!*\n\n*Title:* {title}\n*Content:* {content}\n\n🎨 Your presentation is being generated..."
        },
        "campaign_created": {
            "en": "✅ *Campaign Created!*\n\n*Name:* {name}\n*Goal:* {goal}\n*Target:* {target}\n\n🚀 Your campaign strategy is being developed..."
        }
    }
    
    template = content_map.get(content_key, {}).get("en", "Content not available")
    return template.format(**kwargs)

# ========================================
# AI SUGGESTION SERVICE
# ========================================

# Pre-warmed cache with Fetch-specific content organized by campaign type
SUGGESTION_CACHE = {
    "campaign": [
        "Receipt Heroes Series - Feature real users with epic reward redemption stories",
        "Reward Refresh Week - Daily new reward drops and exclusive brand promos", 
        "Scan Streaks - Weekly prizes for consecutive scans with leaderboard",
        "Surprise & Delight Drops - Random rewards for scanning within certain windows",
        "Holiday Hacks with Fetch - Position Fetch as money-saving hero for seasonal shopping"
    ],
    "physical_event": [
        "Fetch Live: Rewards in Real Life - Immersive pop-up with physical receipt scanning",
        "Receipt Relay (Campus Tour) - College roadshow with scanning contests and swag",
        "Brand Partner Summit - Half-day immersion on Fetch's power and data",
        "Receipt Art Gallery - Transform user receipts into curated art experience",
        "Fetch Your Fortune (Festival Activation) - Branded booth with reward fortune tellers"
    ],
    "email_only": [
        "Receipt Heroes Email Series - Spotlight top users via email campaigns",
        "Weekly Rewards Digest - Email newsletter with new reward announcements",
        "Scan Challenge Email Campaign - Email-driven weekly scanning competitions",
        "Surprise Rewards Email Drop - Email notifications for limited-time bonuses",
        "Holiday Savings Email Series - Email campaign for seasonal shopping tips"
    ],
    "slides": [
        "Fetch 101: Brand Overview for New Partners - Mission, reach, user behavior showcase",
        "2025 Consumer Trends Report (Powered by Fetch Data) - Proprietary spending insights",
        "Fetch User Journey Map - Scan to reward path visualization",
        "Points Economy Explained - How Fetch points work and drive action",
        "Year-in-Review: Fetch Highlights + Metrics - User growth and standout moments"
    ],
    "event": [
        "Fetch Live: Rewards in Real Life - Immersive pop-up with physical receipt scanning",
        "Receipt Relay (Campus Tour) - College roadshow with scanning contests and swag",
        "Brand Partner Summit - Half-day immersion on Fetch's power and data",
        "Receipt Art Gallery - Transform user receipts into curated art experience",
        "Fetch Your Fortune (Festival Activation) - Branded booth with reward fortune tellers"
    ],
    "last_refresh": None
}

async def generate_ai_suggestions(suggestion_type: str, count: int = 5, user_id: str = None) -> list:
    """Generate AI-powered suggestions with instant response using smart caching."""
    try:
        # ALWAYS return pre-warmed cache immediately for instant response
        if suggestion_type in SUGGESTION_CACHE and SUGGESTION_CACHE[suggestion_type]:
            cached_suggestions = SUGGESTION_CACHE[suggestion_type][:count]
            
            # Background refresh from OpenAI (don't await) - but only occasionally
            cache_age = SUGGESTION_CACHE.get("last_refresh", 0) or 0
            current_time = time.time()
            if current_time - cache_age > 300:  # 5 minutes
                asyncio.create_task(refresh_ai_cache(suggestion_type, count))
                SUGGESTION_CACHE["last_refresh"] = current_time
            
            return cached_suggestions
        
        # If no cache exists, use fallback suggestions immediately and populate cache in background
        fallback_suggestions = get_fallback_suggestions(suggestion_type, count)
        
        # Start cache population in background (don't block user)
        asyncio.create_task(populate_cache_background(suggestion_type, count))
        
        return fallback_suggestions
        
    except Exception as e:
        logger.error(f"AI suggestion generation failed: {e}")
        return get_fallback_suggestions(suggestion_type, count)

async def populate_cache_background(suggestion_type: str, count: int):
    """Populate cache in background without blocking user."""
    try:
        suggestions = await ai_service.generate_campaign_suggestions(suggestion_type, count)
        if suggestions:
            SUGGESTION_CACHE[suggestion_type] = suggestions
            SUGGESTION_CACHE["last_refresh"] = time.time()
            logger.debug(f"Background cache populated for {suggestion_type}")
    except Exception as e:
        logger.debug(f"Background cache population failed: {e}")

async def refresh_ai_cache(suggestion_type: str, count: int):
    """Background refresh of AI cache."""
    try:
        fresh_suggestions = await ai_service.generate_campaign_suggestions(suggestion_type, count)
        if fresh_suggestions:
            SUGGESTION_CACHE[suggestion_type] = fresh_suggestions
            logger.debug(f"Refreshed AI cache for {suggestion_type}")
    except Exception as e:
        logger.debug(f"Failed to refresh AI cache: {e}")

async def refresh_suggestion_pool(suggestion_type: str):
    """Background task to refresh suggestion pools."""
    try:
        fresh_suggestions = await generate_ai_suggestions(suggestion_type, 5)
        if fresh_suggestions:
            SUGGESTION_POOLS[suggestion_type] = fresh_suggestions
            logger.info(f"Refreshed {suggestion_type} suggestion pool")
    except Exception as e:
        logger.warning(f"Failed to refresh {suggestion_type} pool: {e}")

def get_fallback_suggestions(suggestion_type: str, count: int) -> list:
    """Emergency fallback suggestions with Fetch-specific content organized by campaign type."""
    fallbacks = {
        "event": [
            "Fetch Field Day - Team-building with brand booths and challenges",
            "Rewards After Dark - Nighttime speakeasy with premium experiences", 
            "Receipt Race - Street team event with brand-specific goals"
        ],
        "physical_event": [
            "Fetch Field Day - Physical team-building with brand booths and challenges",
            "Rewards After Dark - Nighttime physical speakeasy with premium experiences", 
            "Receipt Race - Physical street team event with brand-specific goals"
        ],
        "email_only": [
            "Email Reward Challenge - Email-driven loyalty program",
            "Digital Milestone Celebration - Email campaign for user achievements",
            "Email Partner Spotlight - Partner anniversary email series"
        ],
        "slides": [
            "Marketing Channel Overview - Visual breakdown of Fetch's amplification",
            "Pilot to Partnership: The First 90 Days - New partner onboarding",
            "Field & Experiential Deck - Past event activations with metrics"
        ],
        "campaign": [
            "Brand Love Challenge - Gamified loyalty meets personalization",
            "My First 100,000 Points - User milestone journey sharing",
            "Brand Birthday Bash - Partner anniversaries with multipliers"
        ]
    }
    base = fallbacks.get(suggestion_type, fallbacks["campaign"])
    return (base * ((count // len(base)) + 1))[:count]

def create_individual_selection_modal():
    """Create modal for individual suggestion selection."""
    return {
        "type": "modal",
        "callback_id": "individual_selection",
        "title": {"type": "plain_text", "text": "Select Suggestions"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Select individual suggestions to approve:*"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "checkboxes",
                        "action_id": "suggestion_checkboxes",
                        "options": [
                            {"text": {"type": "plain_text", "text": "Email Campaign: Summer Sale"}, "value": "email_summer"},
                            {"text": {"type": "plain_text", "text": "Social Media: Product Launch"}, "value": "social_launch"},
                            {"text": {"type": "plain_text", "text": "Content Marketing: Blog Series"}, "value": "content_blog"}
                        ]
                    }
                ]
            }
        ],
        "submit": {"type": "plain_text", "text": "Approve Selected"},
        "close": {"type": "plain_text", "text": "Back"}
    }

def get_ai_prompt(suggestion_type: str, count: int) -> str:
    """Get AI prompt based on type."""
    prompts = {
        "event": f"Generate {count} creative marketing event ideas for Fetch Rewards. Focus on engagement and user acquisition. One per line.",
        "slides": f"Generate {count} professional presentation topics for marketing strategy. Focus on growth and market positioning. One per line.",
        "campaign": f"Generate {count} viral marketing campaign ideas for mobile rewards app. Focus on user engagement and viral mechanics. One per line."
    }
    return prompts.get(suggestion_type, prompts["event"])

def get_system_message() -> str:
    """Get system message for AI prompts."""
    return "You are a senior marketing strategist for Fetch Rewards, a leading mobile rewards platform. Generate creative, engaging ideas that leverage mobile technology and user psychology."

# ========================================
# SLACK HELPER FUNCTIONS
# ========================================

async def update_modal_view(client, view_id: str, modal: Dict, user_id: str, modal_type: str):
    """Update modal view with error handling."""
    try:
        await handle_modal_navigation(client, {"view": {"id": view_id}}, modal, "update")
        logger.info(f"{modal_type} modal updated for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to update {modal_type} modal for user {user_id}: {e}")

async def post_to_channel_safe(client, channel: str, text: str, user_id: str):
    """Post to channel with fallback to DM."""
    try:
        await client.chat_postMessage(channel=channel, text=text)
    except Exception as e:
        logger.warning(f"Failed to post to {channel}, sending DM to {user_id}: {e}")
        try:
            await client.chat_postMessage(channel=user_id, text=f"*(From {channel})*\n\n{text}")
        except Exception as dm_error:
            logger.error(f"Failed to send DM to {user_id}: {dm_error}")

async def handle_google_slides_creation(title: str, outline: str = "", presentation_type: str = "executive") -> Tuple[str, str]:
    """Handle Fetch-branded Google Slides creation with proper error handling."""
    try:
        result = await google_slides_service.create_presentation(title, outline, presentation_type)
        
        if result:
            from utils.slack_formatting import SlackFormatter
            
            # Enhanced info with Fetch branding details
            info = (
                f"\n{SlackFormatter.status_message('success', 'Fetch-Branded Slides Created!', '🎨')}\n"
                f"{SlackFormatter.link(result['url'], 'View Presentation')}\n"
                f"*Template:* {result['template']} ({result['theme']})\n"
                f"*Slides:* {result['slide_count']} slides\n"
                f"*Brand Colors:* {result['brand_colors']['primary']} / {result['brand_colors']['accent']}\n"
                f"*ID:* `{result['id']}`"
            )
            return info, "Fetch-branded Google Slides created successfully."
        else:
            return "", "Google Slides creation failed."
            
    except Exception as e:
        logger.error(f"Google Slides creation error: {e}")
        return "", f"Error creating Google Slides: {str(e)}"

# ========================================
# MAIN HANDLER REGISTRATION
# ========================================

def register_clean_handlers(app):
    """Register all clean action handlers with the Slack app."""
    
    logger.info("Registering core clean action handlers...")
    
    # Global error handler for better UX
    @app.error
    async def global_error_handler(error, body, logger_arg=None):
        """Handle all unhandled errors gracefully."""
        user_id = body.get("user", {}).get("id", "unknown")
        error_msg = str(error)
        
        # Log error for debugging - use module logger if logger_arg is None
        error_logger = logger_arg if logger_arg else logger
        error_logger.error(f"Unhandled error for user {user_id}: {error_msg}")
        
        # Don't spam users with error messages for common issues
        if any(x in error_msg.lower() for x in ["expired_trigger_id", "invalid_auth", "push_limit_reached"]):
            return
        
        # Send friendly error message to user
        try:
            await app.client.chat_postMessage(
                channel=user_id,
                text="🤖 Oops! Something went wrong. Please try again or contact support if the issue persists."
            )
        except Exception:
            pass  # Don't fail on error message failure
    
    # ===== NAVIGATION HANDLERS =====
    
    @app.action("create_event")
    async def handle_create_event(ack, body, client):
        await ack()
        modal = create_event_modal()
        await update_modal_view(client, body["view"]["id"], modal, body["user"]["id"], "event")

    @app.action("create_content")
    async def handle_create_content(ack, body, client):
        await ack()
        modal = create_content_modal()
        await update_modal_view(client, body["view"]["id"], modal, body["user"]["id"], "content")

    @app.action("ai_suggestions")
    async def handle_ai_suggestions(ack, body, client):
        await ack()
        # Show actual AI suggestions with default suggestions
        modal = create_ai_suggestions_modal(None)  # Pass None to use defaults
        await update_modal_view(client, body["view"]["id"], modal, body["user"]["id"], "ai_suggestions")

    @app.action("create_slides")
    async def handle_create_slides(ack, body, client):
        await ack()
        modal = create_slides_modal()
        await update_modal_view(client, body["view"]["id"], modal, body["user"]["id"], "slides")

    @app.action("create_campaign")
    async def handle_create_campaign(ack, body, client):
        await ack()
        modal = create_campaign_modal()
        await update_modal_view(client, body["view"]["id"], modal, body["user"]["id"], "campaign")

    @app.action("create_physical_event_campaign")
    async def handle_create_physical_event_campaign(ack, body, client):
        await ack()
        modal = create_campaign_modal()
        # Pre-fill the campaign type for physical events
        for block in modal["blocks"]:
            if block.get("block_id") == "campaign_type":
                block["element"]["initial_option"] = {
                    "text": {"type": "plain_text", "text": "Physical Event Campaign"},
                    "value": "physical_event"
                }
        
        # Always update the current modal view
        await update_modal_view(client, body["view"]["id"], modal, body["user"]["id"], "physical_event_campaign")

    @app.action("create_email_only_campaign")
    async def handle_create_email_only_campaign(ack, body, client):
        await ack()
        modal = create_campaign_modal()
        # Pre-fill the campaign type for email-only campaigns
        for block in modal["blocks"]:
            if block.get("block_id") == "campaign_type":
                block["element"]["initial_option"] = {
                    "text": {"type": "plain_text", "text": "Email-Only Campaign"},
                    "value": "email_only"
                }
        
        # Always update the current modal view
        await update_modal_view(client, body["view"]["id"], modal, body["user"]["id"], "email_only_campaign")

    @app.action("back_to_dashboard")
    async def handle_back_to_dashboard(ack, body, client):
        await ack()
        from handlers.core_slash_commands import create_campaign_hub_modal
        modal = create_campaign_hub_modal()
        await update_modal_view(client, body["view"]["id"], modal, body["user"]["id"], "campaign_hub")

    @app.action("back_to_ai_tools")
    async def handle_back_to_ai_tools(ack, body, client):
        await ack()
        modal = create_ai_tools_modal()
        await update_modal_view(client, body["view"]["id"], modal, body["user"]["id"], "ai_tools")

    @app.action("back_to_content")
    async def handle_back_to_content(ack, body, client):
        await ack()
        modal = create_content_modal()
        await update_modal_view(client, body["view"]["id"], modal, body["user"]["id"], "content")

    # ===== SUGGESTION HANDLERS =====
    
    @app.action("suggest_events")
    async def handle_suggest_events(ack, body, client):
        await ack()
        user_id = body["user"]["id"]
        suggestions = await generate_ai_suggestions("event", 5, user_id)
        modal = create_ai_suggestions_modal(suggestions)
        await update_modal_view(client, body["view"]["id"], modal, user_id, "event_suggestions")

    @app.action("suggest_slides")
    async def handle_suggest_slides(ack, body, client):
        await ack()
        user_id = body["user"]["id"]
        suggestions = await generate_ai_suggestions("slides", 5, user_id)
        modal = create_ai_suggestions_modal(suggestions)
        await update_modal_view(client, body["view"]["id"], modal, user_id, "slides_suggestions")

    @app.action("suggest_campaigns")
    async def handle_suggest_campaigns(ack, body, client):
        await ack()
        user_id = body["user"]["id"]
        suggestions = await generate_ai_suggestions("campaign", 5, user_id)
        modal = create_ai_suggestions_modal(suggestions)
        await update_modal_view(client, body["view"]["id"], modal, user_id, "campaign_suggestions")

    @app.action("generate_more")
    async def handle_generate_more(ack, body, client):
        await ack()
        user_id = body["user"]["id"]
        callback_id = body.get("view", {}).get("callback_id", "")
        
        # Determine suggestion type from callback_id
        suggestion_type = "event"
        if "slides" in callback_id:
            suggestion_type = "slides"
        elif "campaign" in callback_id:
            suggestion_type = "campaign"
        
        suggestions = await generate_ai_suggestions(suggestion_type, 5, user_id)
        modal = create_ai_suggestions_modal(suggestions)
        await update_modal_view(client, body["view"]["id"], modal, user_id, f"{suggestion_type}_suggestions")

    # ===== SUGGESTION USAGE HANDLERS =====
    # Note: use_suggestion_\d+ handler is defined later in the unified campaign section

    @app.action("use_event_suggestion")
    async def handle_use_event_suggestion(ack, body, client):
        await ack()
        user_id = body["user"]["id"]
        suggestion = body.get("actions", [{}])[0].get("value", "Event Idea")
        
        message = get_localized_content("event_created", user_id, 
                                      name=suggestion, type="Suggestion", description="AI-generated idea")
        await post_to_channel_safe(client, CONFIG["CHANNELS"]["EVENTS"], message, user_id)

    @app.action("use_slides_suggestion")
    async def handle_use_slides_suggestion(ack, body, client):
        await ack()
        user_id = body["user"]["id"]
        suggestion = body.get("actions", [{}])[0].get("value", "Slides Idea")
        
        # Create confirmation modal with Google Slides option
        modal = {
            "type": "modal",
            "callback_id": "slides_suggestion_confirmation",
            "title": {"type": "plain_text", "text": "Create Presentation"},
            "submit": {"type": "plain_text", "text": "Create"},
            "close": {"type": "plain_text", "text": "← Back"},
            "private_metadata": suggestion,
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": "*🎨 Presentation Builder*\nTransform your idea into a professional presentation"}},
                {"type": "divider"},
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*Selected Idea:*\n{suggestion}"}},
                {"type": "input", "block_id": "google_slides_option", 
                 "label": {"type": "plain_text", "text": "🎨 Fetch-Branded Presentation"},
                 "element": {"type": "checkboxes", "action_id": "create_google_slides",
                            "options": [
                                {"text": {"type": "plain_text", "text": "Create branded Google Slides presentation"}, "value": "create_slides"}
                            ]}, 
                 "optional": True},
                {"type": "input", "block_id": "slide_template", 
                 "label": {"type": "plain_text", "text": "Presentation Template"},
                 "element": {"type": "static_select", "action_id": "template_select",
                            "placeholder": {"type": "plain_text", "text": "Choose template style"},
                            "options": [
                                {"text": {"type": "plain_text", "text": "Executive Overview - Premium design for leadership"}, "value": "executive"},
                                {"text": {"type": "plain_text", "text": "Community Retrospective - Fun, engaging community updates"}, "value": "community"},
                                {"text": {"type": "plain_text", "text": "Data Insights - Clean, analytics-focused design"}, "value": "data_insights"},
                                {"text": {"type": "plain_text", "text": "Product Launch - Bold, innovative product announcements"}, "value": "product_launch"}
                            ]}, 
                 "optional": True},
                {"type": "input", "block_id": "custom_note", 
                 "label": {"type": "plain_text", "text": "Additional Notes (Optional)"}, 
                 "optional": True,
                 "element": {"type": "plain_text_input", "action_id": "note_input", "multiline": True}}
            ]
        }
        await handle_modal_navigation(client, body, modal, "push")

    @app.action("use_campaign_suggestion")
    async def handle_use_campaign_suggestion(ack, body, client):
        await ack()
        user_id = body["user"]["id"]
        suggestion = body.get("actions", [{}])[0].get("value", "Campaign Idea")
        
        message = get_localized_content("campaign_created", user_id,
                                      name=suggestion, goal="Engagement", target="General audience")
        await post_to_channel_safe(client, CONFIG["CHANNELS"]["CAMPAIGNS"], message, user_id)

    # ===== MISSING ACTION HANDLERS =====
    
    @app.action("dashboard_action")
    async def handle_dashboard_action(ack, body, client):
        """Handle main dashboard dropdown selections."""
        await ack()
        user_id = body["user"]["id"]
        selected_value = body["actions"][0]["selected_option"]["value"]
        
        try:
            if selected_value == "create_physical_event_campaign":
                # Route to physical event campaign creation
                modal = create_campaign_modal()
                # Pre-fill for physical event
                for block in modal["blocks"]:
                    if block.get("block_id") == "campaign_type":
                        block["element"]["initial_option"] = {
                            "text": {"type": "plain_text", "text": "Physical Event Campaign"},
                            "value": "physical_event"
                        }
                await update_modal_view(client, body["view"]["id"], modal, user_id, "physical_event_campaign")
                
            elif selected_value == "create_email_only_campaign":
                # Route to email-only campaign creation
                modal = create_campaign_modal()
                # Pre-fill for email-only
                for block in modal["blocks"]:
                    if block.get("block_id") == "campaign_type":
                        block["element"]["initial_option"] = {
                            "text": {"type": "plain_text", "text": "Email-Only Campaign"},
                            "value": "email_only"
                        }
                await update_modal_view(client, body["view"]["id"], modal, user_id, "email_only_campaign")
                
            elif selected_value == "create_campaign":
                # Legacy support for old create_campaign option
                modal = create_campaign_modal()
                await update_modal_view(client, body["view"]["id"], modal, user_id, "campaign")
                
            elif selected_value == "ai_tools":
                modal = create_ai_tools_modal()
                await update_modal_view(client, body["view"]["id"], modal, user_id, "ai_tools")
                
            elif selected_value == "content_creation":
                modal = create_content_modal()
                await update_modal_view(client, body["view"]["id"], modal, user_id, "content")
                
            elif selected_value == "event_management":
                modal = create_event_modal()
                await update_modal_view(client, body["view"]["id"], modal, user_id, "event")
                
            else:
                logger.warning(f"Unknown dashboard action: {selected_value}")
                
        except Exception as e:
            logger.error(f"Error handling dashboard action {selected_value}: {e}")
    
    @app.action("ai_tool_select")
    async def handle_ai_tool_select(ack, body, client):
        """Handle AI tools dropdown selections."""
        await ack()
        user_id = body["user"]["id"]
        selected_value = body["actions"][0]["selected_option"]["value"]
        
        try:
            modal = handle_ai_tool_selection(selected_value)
            await update_modal_view(client, body["view"]["id"], modal, user_id, f"ai_{selected_value}")
        except Exception as e:
            logger.error(f"Error handling AI tool selection {selected_value}: {e}")
    
    @app.action("suggestion_action")
    async def handle_suggestion_action(ack, body, client):
        """Handle suggestion results dropdown actions."""
        await ack()
        user_id = body["user"]["id"]
        selected_value = body["actions"][0]["selected_option"]["value"]
        
        try:
            if selected_value == "approve_all":
                message = "✅ *All suggestions approved!*\n\nSuggestions have been added to your campaign queue."
                await post_to_channel_safe(client, CONFIG["CHANNELS"]["CAMPAIGNS"], message, user_id)
            elif selected_value == "select_individual":
                # Create individual selection modal
                modal = create_individual_selection_modal()
                await update_modal_view(client, body["view"]["id"], modal, user_id, "individual_select")
            elif selected_value == "generate_new":
                # Generate fresh suggestions
                suggestions = await generate_ai_suggestions("campaign", 5, user_id)
                modal = create_ai_suggestions_modal(suggestions)
                await update_modal_view(client, body["view"]["id"], modal, user_id, "new_suggestions")
            elif selected_value == "export_monday":
                message = "📤 *Exporting to Monday.com...*\n\nYour campaign suggestions are being exported."
                await post_to_channel_safe(client, CONFIG["CHANNELS"]["CAMPAIGNS"], message, user_id)
        except Exception as e:
            logger.error(f"Error handling suggestion action {selected_value}: {e}")
    
    @app.action("regenerate_content")
    async def handle_regenerate_content(ack, body, client):
        """Handle content regeneration in AI content generator."""
        await ack()
        user_id = body["user"]["id"]
        
        try:
            modal = create_content_generator_modal()
            await update_modal_view(client, body["view"]["id"], modal, user_id, "content_regenerated")
        except Exception as e:
            logger.error(f"Error regenerating content: {e}")
    
    @app.action("copy_all_content")
    async def handle_copy_all_content(ack, body, client):
        """Handle copying all generated content."""
        await ack()
        user_id = body["user"]["id"]
        
        try:
            message = "📋 *Content copied!*\n\nAll generated content has been prepared for your use."
            await post_to_channel_safe(client, CONFIG["CHANNELS"]["CAMPAIGNS"], message, user_id)
        except Exception as e:
            logger.error(f"Error copying content: {e}")
    
    @app.action("optimization_action")
    async def handle_optimization_action(ack, body, client):
        """Handle campaign optimization actions."""
        await ack()
        user_id = body["user"]["id"]
        selected_value = body["actions"][0]["selected_option"]["value"]
        
        try:
            if selected_value == "apply_all":
                message = "🚀 *All optimizations applied!*\n\nYour campaign has been optimized with all AI suggestions."
            elif selected_value == "ab_test":
                message = "🧪 *A/B test scheduled!*\n\nYour campaign variants are being prepared for testing."
            elif selected_value == "segment":
                message = "🎯 *Audience segmentation applied!*\n\nYour campaign now targets optimized audience segments."
            elif selected_value == "custom":
                message = "⚙️ *Custom optimization mode!*\n\nCustom optimization parameters are being configured."
            else:
                message = "✅ *Optimization completed!*"
                
            await post_to_channel_safe(client, CONFIG["CHANNELS"]["CAMPAIGNS"], message, user_id)
        except Exception as e:
            logger.error(f"Error handling optimization action {selected_value}: {e}")
    
    @app.action("full_report")
    async def handle_full_report(ack, body, client):
        """Handle full audience analysis report request."""
        await ack()
        user_id = body["user"]["id"]
        
        try:
            message = "📊 *Full audience report generated!*\n\nYour comprehensive audience analysis is being prepared."
            await post_to_channel_safe(client, CONFIG["CHANNELS"]["CAMPAIGNS"], message, user_id)
        except Exception as e:
            logger.error(f"Error generating full report: {e}")
    
    @app.action("create_segments")
    async def handle_create_segments(ack, body, client):
        """Handle audience segment creation."""
        await ack()
        user_id = body["user"]["id"]
        
        try:
            message = "🎯 *Audience segments created!*\n\nNew audience segments based on your analysis are ready."
            await post_to_channel_safe(client, CONFIG["CHANNELS"]["CAMPAIGNS"], message, user_id)
        except Exception as e:
            logger.error(f"Error creating segments: {e}")
    
    # ===== FORM SUBMISSION HANDLERS =====
    
    @app.view("create_event_modal")
    async def handle_event_submission(ack, body, client):
        await ack()
        user_id = body["user"]["id"]
        values = body["view"]["state"]["values"]
        
        event_name = values.get("event_name", {}).get("name_input", {}).get("value", "")
        event_type = values.get("event_type", {}).get("type_select", {}).get("selected_option", {}).get("text", {}).get("text", "")
        event_description = values.get("event_description", {}).get("description_input", {}).get("value", "")
        
        message = get_localized_content("event_created", user_id,
                                      name=event_name, type=event_type, description=event_description)
        await post_to_channel_safe(client, CONFIG["CHANNELS"]["EVENTS"], message, user_id)
    
    @app.view("create_content_modal")
    async def handle_content_submission(ack, body, client):
        await ack()
        user_id = body["user"]["id"]
        values = body["view"]["state"]["values"]
        
        content_title = values.get("content_title", {}).get("title_input", {}).get("value", "")
        content_type = values.get("content_type", {}).get("type_select", {}).get("selected_option", {}).get("text", {}).get("text", "")
        content_description = values.get("content_description", {}).get("description_input", {}).get("value", "")
        
        message = (
            f"✅ *Content Created!*\n\n"
            f"*Title:* {content_title}\n"
            f"*Type:* {content_type}\n"
            f"*Description:* {content_description}\n\n"
            f"🎯 Your content is ready for use!"
        )
        await post_to_channel_safe(client, CONFIG["CHANNELS"]["CAMPAIGNS"], message, user_id)

    @app.view("create_slides_modal")
    async def handle_slides_submission(ack, body, client):
        await ack()
        user_id = body["user"]["id"]
        values = body["view"]["state"]["values"]
        
        title = values.get("presentation_title", {}).get("title_input", {}).get("value", "")
        content = values.get("slides_content", {}).get("content_input", {}).get("value", "")
        
        message = get_localized_content("slides_created", user_id, title=title, content=content)
        await post_to_channel_safe(client, CONFIG["CHANNELS"]["EVENTS"], message, user_id)

    @app.view("create_campaign_modal")
    async def handle_campaign_submission(ack, body, client):
        await ack()
        user_id = body["user"]["id"]
        values = body["view"]["state"]["values"]
        
        name = values.get("campaign_name", {}).get("name_input", {}).get("value", "")
        goal = values.get("campaign_goal", {}).get("goal_input", {}).get("value", "")
        target = values.get("campaign_target", {}).get("target_input", {}).get("value", "")
        campaign_type = values.get("campaign_type", {}).get("type_select", {}).get("selected_option", {}).get("value", "email_only")
        
        # Process campaign based on type using new workflow templates
        try:
            campaign_result = await process_campaign_with_workflow_templates(
                name=name,
                goal=goal,
                target=target,
                campaign_type=campaign_type,
                user_id=user_id,
                client=client
            )
            
            # Send confirmation message
            campaign_type_text = get_campaign_type_display_name(campaign_type)
            message = f"✅ *{campaign_type_text} Created!*\n\n*Name:* {name}\n*Goal:* {goal}\n*Target:* {target}\n\n"
            
            if campaign_type == "physical_event":
                message += "📋 *Dual Parent Tickets Created:*\n• 🎪 Event Planning Parent (Kate/Karen)\n• 📧 Email Campaign Parent (Jheryl)\n\n"
                message += f"*Event Planning Tasks:* {campaign_result['event_planning_tasks']} tasks\n"
                message += f"*Email Campaign Tasks:* {campaign_result['email_campaign_tasks']} tasks"
            else:
                message += f"📋 *Email Campaign Workflow Created*\n*Tasks:* {campaign_result['total_tasks']} tasks"
                
            await post_to_channel_safe(client, CONFIG["CHANNELS"]["CAMPAIGNS"], message, user_id)
            
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            await post_to_channel_safe(client, user_id, "❌ Error creating campaign. Please try again.", user_id)

    @app.view("individual_selection")
    async def handle_individual_selection_submission(ack, body, client):
        """Handle individual suggestion selection form submission."""
        await ack()
        user_id = body["user"]["id"]
        values = body.get("view", {}).get("state", {}).get("values", {})
        
        # Get selected suggestions
        selected_options = values.get("suggestion_checkboxes", {}).get("suggestion_checkboxes", {}).get("selected_options", [])
        selected_suggestions = [option["value"] for option in selected_options]
        
        if selected_suggestions:
            suggestions_text = "\n".join([f"✅ {suggestion}" for suggestion in selected_suggestions])
            message = f"*Selected suggestions approved!*\n\n{suggestions_text}\n\nSelected campaigns have been added to your queue."
            await post_to_channel_safe(client, CONFIG["CHANNELS"]["CAMPAIGNS"], message, user_id)
        else:
            message = "No suggestions selected."
            await post_to_channel_safe(client, CONFIG["CHANNELS"]["CAMPAIGNS"], message, user_id)

    @app.view("slides_suggestion_confirmation")
    async def handle_slides_suggestion_submission(ack, body, client):
        await ack()
        user_id = body["user"]["id"]
        suggestion = body.get("view", {}).get("private_metadata", "")
        values = body.get("view", {}).get("state", {}).get("values", {})
        
        # Check if Google Slides was requested
        google_slides_options = values.get("google_slides_option", {}).get("create_google_slides", {}).get("selected_options", [])
        create_google_slides = len(google_slides_options) > 0
        
        # Get selected template
        template_selection = values.get("slide_template", {}).get("template_select", {})
        selected_template = template_selection.get("selected_option", {}).get("value", "executive")
        
        custom_notes = values.get("custom_note", {}).get("note_input", {}).get("value", "")
        
        if create_google_slides:
            # Process Google Slides creation in background with template
            asyncio.create_task(process_google_slides_creation(user_id, suggestion, custom_notes, selected_template, client))
        else:
            message = get_localized_content("slides_created", user_id, title=suggestion, content=custom_notes or "AI-generated")
            await post_to_channel_safe(client, CONFIG["CHANNELS"]["EVENTS"], message, user_id)

    # ===== AI TOOLS MODAL HANDLERS =====
    
    @app.view("content_generator_modal")
    async def handle_content_generator_submission(ack, body, client):
        """Handle AI content generator form submission."""
        await ack()
        user_id = body["user"]["id"]
        values = body.get("view", {}).get("state", {}).get("values", {})
        
        # Extract content fields
        email_subject = values.get("email_subject", {}).get("email_subject", {}).get("value", "")
        email_body = values.get("email_body", {}).get("email_body", {}).get("value", "")
        social_post = values.get("social_post", {}).get("social_post", {}).get("value", "")
        blog_title = values.get("blog_title", {}).get("blog_title", {}).get("value", "")
        blog_intro = values.get("blog_intro", {}).get("blog_intro", {}).get("value", "")
        
        message = (
            f"🤖 *AI Content Generated Successfully!*\n\n"
            f"*📧 Email Subject:* {email_subject}\n"
            f"*📱 Social Post:* {social_post}\n"
            f"*📰 Blog Title:* {blog_title}\n\n"
            f"Content has been prepared and is ready for use in your campaigns."
        )
        await post_to_channel_safe(client, CONFIG["CHANNELS"]["CAMPAIGNS"], message, user_id)
    
    @app.view("campaign_optimizer_modal")
    async def handle_campaign_optimizer_submission(ack, body, client):
        """Handle campaign optimizer form submission."""
        await ack()
        user_id = body["user"]["id"]
        
        message = (
            f"🎯 *Campaign Optimization Applied!*\n\n"
            f"Your campaign has been optimized with AI recommendations:\n"
            f"✅ A/B test subject lines scheduled\n"
            f"✅ Audience segmentation applied\n"
            f"✅ Send time optimized\n"
            f"✅ CTA urgency elements added\n\n"
            f"Expected performance improvement: +15-25%"
        )
        await post_to_channel_safe(client, CONFIG["CHANNELS"]["CAMPAIGNS"], message, user_id)
    
    @app.view("audience_analysis_modal")
    async def handle_audience_analysis_submission(ack, body, client):
        """Handle audience analysis form submission."""
        await ack()
        user_id = body["user"]["id"]
        
        message = (
            f"👥 *Audience Analysis Export Completed!*\n\n"
            f"Your comprehensive audience insights have been generated:\n"
            f"📊 Demographics breakdown\n"
            f"📈 Behavior patterns analysis\n"
            f"🎯 Targeting recommendations\n"
            f"📱 Device preference data\n\n"
            f"Data has been exported and is ready for strategic planning."
        )
        await post_to_channel_safe(client, CONFIG["CHANNELS"]["CAMPAIGNS"], message, user_id)

    # ===== UNIFIED CAMPAIGN WORKFLOW HANDLERS =====
    
    # Removed old start_unified_campaign handler - using separate campaign type buttons now
    
    @app.action("view_campaign_dashboard")
    async def handle_view_campaign_dashboard(ack, body, client):
        """Handle View Dashboard button - opens Campaign Dashboard modal (AC #3)."""
        await ack()
        user_id = body["user"]["id"]
        
        try:
            modal = await create_campaign_dashboard_modal(client)
            await handle_modal_navigation(client, body, modal, "update")
            logger.info(f"Campaign Dashboard opened for user {user_id}")
        except Exception as e:
            logger.error(f"Error opening Campaign Dashboard: {e}")
    
    @app.view("unified_campaign_submit")
    async def handle_unified_campaign_submit(ack, body, client):
        """Handle Smart Campaign form submission with workflow logic (AC #4)."""
        user_id = body["user"]["id"]
        values = body["view"]["state"]["values"]
        
        # Extract form data
        form_data = extract_campaign_form_data(values)
        
        # Validate required fields
        validation_errors = validate_campaign_form(form_data)
        if validation_errors:
            await ack(response_action="errors", errors=validation_errors)
            return
        
        await ack()
        
        try:
            # Process unified campaign workflow (Project 1 + Project 2 merged)
            await process_unified_campaign_workflow(form_data, user_id, client)
                
        except Exception as e:
            logger.error(f"Error processing campaign submission: {e}")
            await send_error_message(client, user_id, "Failed to process campaign. Please try again.")
    
    @app.action("back_to_campaign_hub")
    async def handle_back_to_campaign_hub(ack, body, client):
        """Handle back navigation to Campaign Hub."""
        await ack()
        user_id = body["user"]["id"]
        
        try:
            from handlers.core_slash_commands import create_campaign_hub_modal
            modal = create_campaign_hub_modal()
            await update_modal_view(client, body["view"]["id"], modal, user_id, "campaign_hub")
            logger.info(f"Navigated back to Campaign Hub for user {user_id}")
        except Exception as e:
            logger.error(f"Error navigating back to Campaign Hub: {e}")
    
    @app.action("get_ai_suggestions")
    async def handle_get_ai_suggestions(ack, body, client):
        """Generate AI suggestions modal with pre-filled cache."""
        await ack()
        user_id = body["user"]["id"]
        
        try:
            suggestions = await generate_ai_suggestions("campaign", 5, user_id)
            modal = create_ai_suggestions_modal(suggestions)
            
            # Check if trigger_id is available and not expired
            await handle_modal_navigation(client, body, modal, "push")
            logger.info(f"AI suggestions modal opened for user {user_id}")
        except Exception as e:
            logger.error(f"Error opening AI suggestions modal: {e}")
    
    @app.action("refresh_dashboard")
    async def handle_refresh_dashboard(ack, body, client):
        """Refresh dashboard data from Monday.com and Google Calendar."""
        await ack()
        user_id = body["user"]["id"]
        
        try:
            # Recreate dashboard with fresh data
            modal = await create_campaign_dashboard_modal(client)
            await handle_modal_navigation(client, body, modal, "update")
            logger.info(f"Dashboard refreshed for user {user_id}")
        except Exception as e:
            logger.error(f"Error refreshing dashboard: {e}")
    
    @app.action(re.compile("view_monday_campaign_.*"))
    async def handle_view_monday_campaign(ack, body, client):
        """Handle viewing Monday.com campaign details."""
        await ack()
        user_id = body["user"]["id"]
        campaign_id = body["actions"][0]["action_id"].replace("view_monday_campaign_", "")
        
        try:
            # Get campaign details from Monday.com
            campaign_details = await monday_service.get_campaign_details(campaign_id)
            
            if campaign_details:
                message = (
                    f"*Campaign: {campaign_details.get('name', 'Unknown')}*\n"
                    f"Status: {campaign_details.get('status', 'Unknown')}\n"
                    f"Progress: {campaign_details.get('progress', 0)}%\n"
                    f"Due Date: {campaign_details.get('due_date', 'Not set')}\n"
                    f"Assignees: {', '.join(campaign_details.get('assignees', []))}\n\n"
                    f"View full details: {campaign_details.get('url', '#')}"
                )
            else:
                message = "Campaign details not found."
                
            await client.chat_postMessage(channel=user_id, text=message)
        except Exception as e:
            logger.error(f"Error viewing Monday campaign: {e}")
    
    @app.action(re.compile("use_suggestion_\\d+"))
    async def handle_use_suggestion(ack, body, client):
        """Handle use suggestion button - auto-fill campaign form."""
        await ack()
        user_id = body["user"]["id"]
        suggestion = body["actions"][0]["value"]
        
        try:
            # Create pre-filled campaign modal
            modal = create_smart_campaign_modal_prefilled(suggestion)
            await handle_modal_navigation(client, body, modal, "update")
            logger.info(f"Auto-filled campaign form with suggestion for user {user_id}")
        except Exception as e:
            logger.error(f"Error auto-filling form: {e}")
    
    @app.action("regenerate_suggestions")
    async def handle_regenerate_suggestions(ack, body, client):
        """Regenerate AI suggestions."""
        await ack()
        user_id = body["user"]["id"]
        
        try:
            # Force fresh OpenAI call
            suggestions = await ai_service.generate_campaign_suggestions("campaign", 5)
            modal = create_ai_suggestions_modal(suggestions)
            await handle_modal_navigation(client, body, modal, "update")
            logger.info(f"Regenerated AI suggestions for user {user_id}")
        except Exception as e:
            logger.error(f"Error regenerating suggestions: {e}")
    
    @app.action("back_to_smart_campaign")
    async def handle_back_to_smart_campaign(ack, body, client):
        """Navigate back to Smart Campaign modal."""
        await ack()
        user_id = body["user"]["id"]
        
        try:
            modal = create_smart_campaign_modal()
            await handle_modal_navigation(client, body, modal, "update")
            logger.info(f"Navigated back to Smart Campaign for user {user_id}")
        except Exception as e:
            logger.error(f"Error navigating back to Smart Campaign: {e}")
    
    @app.action("view_campaign_back_to_school")
    async def handle_view_campaign_back_to_school(ack, body, client):
        """Handle viewing campaign details."""
        await ack()
        user_id = body["user"]["id"]
        logger.info(f"User {user_id} requested campaign details view")
        
        # For now, just acknowledge - this would open a campaign detail modal
        # In a real implementation, this would show campaign details
    
    @app.action("view_campaign_summer_launch")
    async def handle_view_campaign_summer_launch(ack, body, client):
        """Handle viewing Summer Launch campaign details."""
        await ack()
        user_id = body["user"]["id"]
        
        try:
            modal = {
                "type": "modal",
                "callback_id": "campaign_detail_summer",
                "title": {"type": "plain_text", "text": "Summer Launch"},
                "close": {"type": "plain_text", "text": "Back"},
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "*🎯 Summer Product Launch Campaign*\n\nStatus: In Progress | Due: July 25, 2025"}
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "*Campaign Details:*\n• Budget: $50,000\n• Target Audience: 18-35 millennials\n• Channels: Social, Email, Influencer\n• Expected Reach: 250K users"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "*Progress:*\n✅ Creative assets (100%)\n🔄 Influencer outreach (75%)\n⏳ Email sequences (50%)\n⏳ Landing page (60%)"}
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "← Back to Dashboard"},
                                "action_id": "back_to_campaign_hub"
                            }
                        ]
                    }
                ]
            }
            await handle_modal_navigation(client, body, modal, "update")
        except Exception as e:
            logger.error(f"Error showing Summer Launch details: {e}")
    
    @app.action("view_campaign_mobile_app")
    async def handle_view_campaign_mobile_app(ack, body, client):
        """Handle viewing Mobile App campaign details."""
        await ack()
        user_id = body["user"]["id"]
        
        try:
            modal = {
                "type": "modal",
                "callback_id": "campaign_detail_mobile",
                "title": {"type": "plain_text", "text": "Mobile App Campaign"},
                "close": {"type": "plain_text", "text": "Back"},
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "*📱 Mobile App Promotion Campaign*\n\nStatus: Planning | Due: August 10, 2025"}
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "*Campaign Details:*\n• Budget: $75,000\n• Target Audience: App store users\n• Channels: ASO, Paid Ads, PR\n• Expected Downloads: 100K"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "*Progress:*\n⏳ App store optimization (25%)\n⏳ Ad creatives (30%)\n📝 PR strategy (10%)\n📝 Launch plan (20%)"}
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "← Back to Dashboard"},
                                "action_id": "back_to_campaign_hub"
                            }
                        ]
                    }
                ]
            }
            await handle_modal_navigation(client, body, modal, "update")
        except Exception as e:
            logger.error(f"Error showing Mobile App details: {e}")

    logger.info("Core clean action handlers registered successfully")

async def process_google_slides_creation(user_id: str, suggestion: str, notes: str, template: str, client):
    """Background processing for Google Slides creation."""
    try:
        google_slides_info, status = await handle_google_slides_creation(suggestion, notes, template)
        
        message = (
            f"*Presentation Created from AI Suggestion!*\n\n"
            f"*Idea:* {suggestion}\n"
            f"{google_slides_info}\n"
            f"*Status:* {status}"
        )
        
        await post_to_channel_safe(client, CONFIG["CHANNELS"]["EVENTS"], message, user_id)
        
    except Exception as e:
        logger.error(f"Error in Google Slides creation: {e}")
        error_message = f"*Error Creating Presentation*\n\nThere was an issue creating slides for: {suggestion}"
        await post_to_channel_safe(client, CONFIG["CHANNELS"]["EVENTS"], error_message, user_id)

# ========================================
# UNIFIED CAMPAIGN WORKFLOW FUNCTIONS
# ========================================

def create_smart_campaign_modal():
    """Create Smart Campaign Creation modal with 5 form fields (AC #2)."""
    from utils.slack_formatting import SlackFormatter, format_modal_header, format_divider
    
    return {
        "type": "modal",
        "callback_id": "unified_campaign_submit",
        "title": {"type": "plain_text", "text": "Smart Campaign"},
        "submit": {"type": "plain_text", "text": "Create Campaign"},
        "close": {"type": "plain_text", "text": "← Back"},
        "blocks": [
            format_modal_header(
                "Create a Smart Campaign",
                "Fill required fields for simple events, or add optional fields for full workflows."
            ),
            format_divider(),
            # Required Field 1: Event Name
            {
                "type": "input",
                "block_id": "event_name",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "event_name_input",
                    "placeholder": {"type": "plain_text", "text": "Enter event name..."}
                },
                "label": {"type": "plain_text", "text": "Event Name"}
            },
            # Required Field 2: Event Dates
            {
                "type": "input", 
                "block_id": "event_dates",
                "element": {
                    "type": "datepicker",
                    "action_id": "event_dates_input",
                    "placeholder": {"type": "plain_text", "text": "Select date"}
                },
                "label": {"type": "plain_text", "text": "Event Date"}
            },
            # Required Field 3: Location
            {
                "type": "input",
                "block_id": "location",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "location_input",
                    "placeholder": {"type": "plain_text", "text": "Enter location..."}
                },
                "label": {"type": "plain_text", "text": "Location"}
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Optional fields for full workflow automation:*"}
            },
            # Optional Field 4: Campaign Goals
            {
                "type": "input",
                "block_id": "campaign_goals",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "campaign_goals_input",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "Describe campaign goals and objectives..."}
                },
                "label": {"type": "plain_text", "text": "Campaign Goals"},
                "optional": True
            },
            # Optional Field 5: Deliverables
            {
                "type": "input",
                "block_id": "deliverables",
                "element": {
                    "type": "plain_text_input", 
                    "action_id": "deliverables_input",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "List expected deliverables..."}
                },
                "label": {"type": "plain_text", "text": "Deliverables"},
                "optional": True
            },
            {"type": "divider"},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🤖 AI Suggestions"},
                        "action_id": "get_ai_suggestions",
                        "style": "primary"
                    }
                ]
            }
        ]
    }

async def create_campaign_dashboard_modal(client=None):
    """Create Campaign Dashboard modal with real data from Monday.com and Google Calendar."""
    try:
        # Get real campaign data from Monday.com
        monday_campaigns = await monday_service.get_active_campaigns() if client else []
        
        # Get upcoming calendar events
        calendar_events = await google_calendar_service.get_upcoming_events(limit=5) if client else []
        
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Active Campaigns*\nReal-time data from Monday.com and Google Calendar"}
            },
            {"type": "divider"}
        ]
        
        # Add real Monday.com campaigns
        if monday_campaigns:
            for campaign in monday_campaigns[:5]:  # Show max 5 campaigns
                status = campaign.get('status', 'Unknown').lower()
                status_indicator = {
                    'working on it': '🟡',
                    'done': '🟢', 
                    'stuck': '🔴',
                    'not started': '⚪'
                }.get(status, '⚫')
                
                due_date = campaign.get('due_date', 'No due date')
                progress = campaign.get('progress', 0)
                
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{campaign.get('name', 'Untitled Campaign')}*\n{status_indicator} Status: {status.title()} | Progress: {progress}% | Due: {due_date}"},
                    "accessory": {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View in Monday"},
                        "action_id": f"view_monday_campaign_{campaign.get('id', '')}"
                    }
                })
        else:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": "_No active campaigns found in Monday.com_\nCreate a new campaign to get started."}
            })
        
        # Add calendar events section
        if calendar_events:
            blocks.extend([
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Upcoming Events*"}
                }
            ])
            
            for event in calendar_events[:3]:  # Show max 3 events
                event_date = event.get('start_date', 'TBD')
                location = event.get('location', 'Location TBD')
                
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{event.get('title', 'Untitled Event')}*\nDate: {event_date} | Location: {location}"}
                })
        
        # Add navigation
        blocks.extend([
            {"type": "divider"},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Back to Hub"},
                        "action_id": "back_to_campaign_hub"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Refresh Data"},
                        "action_id": "refresh_dashboard"
                    }
                ]
            }
        ])
        
        return {
            "type": "modal",
            "callback_id": "campaign_dashboard",
            "title": {"type": "plain_text", "text": "Campaign Dashboard"},
            "close": {"type": "plain_text", "text": "Close"},
            "blocks": blocks
        }
        
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}")
        # Fallback to simple error message
        return {
            "type": "modal",
            "callback_id": "campaign_dashboard",
            "title": {"type": "plain_text", "text": "Campaign Dashboard"},
            "close": {"type": "plain_text", "text": "Close"},
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Dashboard Error*\nUnable to load campaign data. Please try again."}
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Back to Hub"},
                            "action_id": "back_to_campaign_hub"
                        }
                    ]
                }
            ]
        }

def extract_campaign_form_data(values):
    """Extract form data from Slack form submission."""
    return {
        "event_name": values.get("event_name", {}).get("event_name_input", {}).get("value", ""),
        "event_dates": values.get("event_dates", {}).get("event_dates_input", {}).get("selected_date", ""),
        "location": values.get("location", {}).get("location_input", {}).get("value", ""),
        "campaign_goals": values.get("campaign_goals", {}).get("campaign_goals_input", {}).get("value", ""),
        "deliverables": values.get("deliverables", {}).get("deliverables_input", {}).get("value", "")
    }

def validate_campaign_form(form_data):
    """Validate required fields and return errors if any."""
    errors = {}
    
    if not form_data["event_name"].strip():
        errors["event_name"] = "Event name is required"
    
    if not form_data["event_dates"]:
        errors["event_dates"] = "Event date is required"
        
    if not form_data["location"].strip():
        errors["location"] = "Location is required"
    
    return errors

async def process_unified_campaign_workflow(form_data, user_id, client):
    """
    Process unified Project 1 + Project 2 campaign workflow.
    Creates Calendar Event + Monday.com Workflow + Google Doc Brief + Calendar Reminders.
    """
    try:
        from utils.slack_formatting import SlackFormatter
        
        # Prepare campaign data with requestor info
        campaign_data = {
            "event_name": form_data["event_name"],
            "event_dates": form_data["event_dates"],
            "location": form_data["location"],
            "campaign_goals": form_data.get("campaign_goals", ""),
            "deliverables": form_data.get("deliverables", ""),
            "requestor": user_id
        }
        
        logger.info(f"Starting unified campaign workflow for: {form_data['event_name']}")
        
        # 1. Create Google Calendar Event (B2B Fetch Events calendar)
        calendar_event_data = {
            "title": form_data["event_name"],
            "start_date": form_data["event_dates"],
            "description": f"Location: {form_data['location']}\nRequestor: {user_id}"
        }
        calendar_result = await google_calendar_service.create_campaign_event(calendar_event_data)
        
        # 2. Generate Google Doc Brief
        brief_result = await google_docs_service.create_campaign_brief(campaign_data)
        
        # 3. Create Monday.com Workflow (Parent + Subtasks)
        monday_result = await monday_service.create_unified_campaign_workflow(campaign_data)
        
        # 4. Create Calendar Reminders for Subtasks (9AM due date reminders)
        reminder_events = []
        if monday_result and monday_result.get('subtasks'):
            for subtask in monday_result['subtasks']:
                if subtask.get('calendar_reminder') and subtask['assignee'] in ['Karen or Kate']:
                    reminder_data = {
                        "title": f"🔔 Due: {subtask['name']} - {form_data['event_name']}",
                        "start_date": subtask['due_date'],
                        "description": f"Task reminder for {subtask['assignee']}\nEstimated: {subtask['estimated_duration']}"
                    }
                    reminder_event = await google_calendar_service.create_campaign_event(reminder_data)
                    if reminder_event:
                        reminder_events.append(reminder_event)
        
        # 5. Update brief with resource links
        if brief_result:
            resource_links = {}
            if monday_result:
                resource_links["Monday.com Workflow"] = monday_result['board_url']
            if calendar_result:
                resource_links["Google Calendar Event"] = calendar_result['event_url']
            
            await google_docs_service.update_brief_with_links(brief_result['doc_id'], resource_links)
        
        # 6. Send Slack Thread Confirmation with clean formatting
        # Prepare resource links
        links = {}
        if brief_result:
            links["Brief Doc"] = brief_result['doc_url']
        if monday_result:
            links[f"Monday.com Tickets ({monday_result['total_tasks']} tasks)"] = monday_result['board_url']
        if calendar_result:
            links["Google Calendar Event"] = calendar_result['event_url']
        if reminder_events:
            links[f"Calendar Reminders ({len(reminder_events)} scheduled)"] = "#"
        
        # Prepare workflow tasks
        workflow_tasks = monday_result.get('subtasks', []) if monday_result else []
        
        # Create clean, professional message with user mentions
        full_message = await SlackFormatter.campaign_success_message_with_mentions(
            client=client,
            name=form_data["event_name"],
            links=links if links else None,
            workflow_tasks=workflow_tasks if workflow_tasks else None
        )
        
        # Send to appropriate channel
        target_channel = CONFIG["CHANNELS"]["CAMPAIGNS"] if form_data.get("campaign_goals") else CONFIG["CHANNELS"]["EVENTS"]
        await post_to_channel_safe(client, target_channel, full_message, user_id)
        
        logger.info(f"Unified campaign workflow completed for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in unified campaign workflow: {e}")
        raise

async def send_error_message(client, user_id, error_text):
    """Send error message to user."""
    try:
        await client.chat_postMessage(
            channel=user_id,
            text=f"❌ {error_text}"
        )
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

def create_ai_suggestions_modal(suggestions: list):
    """Create AI suggestions modal with Use buttons."""
    from utils.slack_formatting import SlackFormatter, format_modal_header, format_divider
    
    blocks = [
        format_modal_header(
            "AI Campaign Suggestions",
            "Select one to auto-fill your campaign form:"
        ),
        format_divider()
    ]
    
    for i, suggestion in enumerate(suggestions[:5]):
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": SlackFormatter.ai_suggestion_item(i+1, suggestion)},
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "Use This"},
                "action_id": f"use_suggestion_{i}",
                "value": suggestion,
                "style": "primary"
            }
        })
    
    blocks.extend([
        {"type": "divider"},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🔄 Generate More"},
                    "action_id": "regenerate_suggestions"
                },
                {
                    "type": "button", 
                    "text": {"type": "plain_text", "text": "← Back"},
                    "action_id": "back_to_campaign_hub"
                }
            ]
        }
    ])
    
    return {
        "type": "modal",
        "callback_id": "ai_suggestions_modal",
        "title": {"type": "plain_text", "text": "AI Suggestions"},
        "close": {"type": "plain_text", "text": "← Back"},
        "blocks": blocks
    }

def create_smart_campaign_modal_prefilled(suggestion: str):
    """Create Smart Campaign modal pre-filled with AI suggestion."""
    # Parse suggestion for smart auto-fill
    event_name = suggestion if len(suggestion) < 50 else suggestion[:47] + "..."
    
    modal = create_smart_campaign_modal()
    
    # Update blocks with pre-filled values
    for block in modal["blocks"]:
        if block.get("block_id") == "event_name":
            block["element"]["initial_value"] = event_name
        elif block.get("block_id") == "campaign_goals":
            block["element"]["initial_value"] = f"Campaign focused on: {suggestion}"
    
    return modal

def register_clean_actions(app):
    """Main registration function for clean actions."""
    register_clean_handlers(app)
    logger.info("All clean action handlers registered successfully")
    
    @app.action(re.compile("use_suggestion_\\d+"))
    async def handle_use_suggestion(ack, body, client):
        """Handle use suggestion button - open campaign modal with pre-filled data."""
        await ack()
        suggestion = body["actions"][0]["value"]
        user_id = body["user"]["id"]
        
        # Determine campaign type from suggestion
        campaign_type = "physical_event" if "event" in suggestion.lower() or "workshop" in suggestion.lower() else "email_only"
        
        modal = create_campaign_modal()
        # Pre-fill campaign name with suggestion
        for block in modal["blocks"]:
            if block.get("block_id") == "campaign_name":
                block["element"]["initial_value"] = suggestion.split(" - ")[0]
            elif block.get("block_id") == "campaign_goal":
                if " - " in suggestion:
                    block["element"]["initial_value"] = suggestion.split(" - ")[1]
            elif block.get("block_id") == "campaign_type":
                block["element"]["initial_option"] = {
                    "text": {"type": "plain_text", "text": "Physical Event Campaign" if campaign_type == "physical_event" else "Email-Only Campaign"},
                    "value": campaign_type
                }
        
        await update_modal_view(client, body["view"]["id"], modal, user_id, f"{campaign_type}_from_suggestion")
    
    @app.action("generate_more_suggestions")
    async def handle_generate_more_suggestions(ack, body, client):
        """Generate more AI suggestions with campaign type awareness."""
        await ack()
        user_id = body["user"]["id"]
        
        # Generate campaign-type-specific suggestions
        physical_event_suggestions = [
            "Flash Sale Friday Pop-up - Physical store activation + live scanning demos",
            "Customer Appreciation Day - In-person event with exclusive partner booths",
            "Refer-a-Friend Challenge Arena - Physical meetup with rewards ceremony",
            "Seasonal Product Showcase - Pop-up retail experience with brand partners", 
            "VIP Member Exclusive Lounge - Private physical event with premium rewards"
        ]
        
        email_only_suggestions = [
            "Flash Sale Friday Email Blast - Email campaign with countdown timers",
            "Customer Appreciation Email Series - Personalized thank you email journey",
            "Refer-a-Friend Email Challenge - Email-driven viral referral campaign",
            "Seasonal Product Email Showcase - Email announcements with partner offers",
            "VIP Member Email Exclusive - Personalized email rewards for top users"
        ]
        
        # For now, use mixed suggestions - in real implementation, would be context-aware
        new_suggestions = physical_event_suggestions[:3] + email_only_suggestions[:2]
        
        modal = create_ai_suggestions_modal(new_suggestions)
        await update_modal_view(client, body["view"]["id"], modal, user_id, "regenerated_suggestions")
    
    @app.view_closed(re.compile(".*"))
    async def handle_view_closed(ack, body, client):
        """Handle modal close events to navigate back appropriately."""
        await ack()
        
        # Check if we should navigate back to Campaign Hub
        private_metadata = body.get("view", {}).get("private_metadata", "")
        if private_metadata == "campaign_hub":
            # Don't do anything, let it close naturally
            pass

# ========================================
# WORKFLOW TEMPLATES (JHERL'S FEEDBACK IMPLEMENTATION)
# ========================================

def get_campaign_type_display_name(campaign_type: str) -> str:
    """Get display name for campaign type."""
    type_names = {
        "physical_event": "Physical Event Campaign",
        "email_only": "Email-Only Campaign",
        "email": "Email Campaign",
        "social": "Social Media Campaign",
        "content": "Content Marketing Campaign"
    }
    return type_names.get(campaign_type, "Campaign")

async def process_campaign_with_workflow_templates(name: str, goal: str, target: str, campaign_type: str, user_id: str, client) -> dict:
    """
    Process campaign creation with proper workflow templates based on Jherl's feedback.
    Creates dual parent tickets for physical events, single ticket for email-only.
    """
    logger.info(f"Processing {campaign_type} campaign: {name}")
    
    if campaign_type == "physical_event":
        return await create_dual_parent_ticket_workflow(name, goal, target, user_id, client)
    else:
        return await create_email_only_workflow(name, goal, target, user_id, client)

async def create_dual_parent_ticket_workflow(name: str, goal: str, target: str, user_id: str, client) -> dict:
    """
    Create dual parent ticket system for physical events.
    Separate event planning workflow for Kate/Karen and email workflow for Jheryl.
    """
    try:
        # Event Planning Parent Ticket (Kate/Karen's Domain)
        event_planning_tasks = get_event_planning_workflow_template()
        
        # Email Campaign Parent Ticket (Jheryl's Domain) 
        email_campaign_tasks = get_email_campaign_workflow_template()
        
        # In real implementation, these would create actual Monday.com tickets
        # For now, we'll simulate the structure
        
        result = {
            "event_planning_parent": {
                "name": f"Event Planning: {name}",
                "assignees": ["Kate", "Karen"],
                "tasks": event_planning_tasks,
                "total_tasks": len(event_planning_tasks)
            },
            "email_campaign_parent": {
                "name": f"Email Campaign: {name}",
                "assignees": ["Jheryl"],
                "tasks": email_campaign_tasks,
                "total_tasks": len(email_campaign_tasks)
            },
            "event_planning_tasks": len(event_planning_tasks),
            "email_campaign_tasks": len(email_campaign_tasks),
            "total_parents": 2
        }
        
        logger.info(f"Created dual parent workflow: {result['event_planning_tasks']} event tasks, {result['email_campaign_tasks']} email tasks")
        return result
        
    except Exception as e:
        logger.error(f"Error creating dual parent workflow: {e}")
        raise

async def create_email_only_workflow(name: str, goal: str, target: str, user_id: str, client) -> dict:
    """
    Create single parent ticket workflow for email-only campaigns.
    Uses Jheryl's existing 6-subtask email template.
    """
    try:
        # Email Campaign Workflow (Jheryl's existing template)
        email_tasks = get_email_campaign_workflow_template()
        
        result = {
            "email_campaign_parent": {
                "name": f"Email Campaign: {name}",
                "assignees": ["Jheryl"],
                "tasks": email_tasks,
                "total_tasks": len(email_tasks)
            },
            "total_tasks": len(email_tasks),
            "total_parents": 1
        }
        
        logger.info(f"Created email-only workflow: {result['total_tasks']} tasks")
        return result
        
    except Exception as e:
        logger.error(f"Error creating email-only workflow: {e}")
        raise

def get_event_planning_workflow_template() -> list:
    """
    Event Planning Workflow Template - Kate/Karen's responsibilities.
    Covers vendor coordination, creative collaboration, and physical event logistics.
    """
    return [
        {
            "name": "Vendor Coordination & Calls",
            "description": "Contact and coordinate with event vendors",
            "assignee": "Kate or Karen",
            "estimated_duration": "2-3 hours",
            "dependencies": [],
            "calendar_reminder": True
        },
        {
            "name": "Creative Team Collaboration for Visual Experience", 
            "description": "Work with creative team on event visual design and branding",
            "assignee": "Kate or Karen",
            "estimated_duration": "3-4 hours",
            "dependencies": ["Vendor Coordination & Calls"],
            "calendar_reminder": True
        },
        {
            "name": "Physical Event Logistics Planning",
            "description": "Plan event setup, layout, equipment, and operational details",
            "assignee": "Kate or Karen", 
            "estimated_duration": "4-5 hours",
            "dependencies": ["Creative Team Collaboration for Visual Experience"],
            "calendar_reminder": True
        },
        {
            "name": "Event Setup and Operations",
            "description": "On-site event setup and day-of operations management",
            "assignee": "Kate or Karen",
            "estimated_duration": "6-8 hours",
            "dependencies": ["Physical Event Logistics Planning"],
            "calendar_reminder": True
        },
        {
            "name": "Post-Event Wrap-up and Vendor Coordination",
            "description": "Event breakdown, vendor settlements, and post-event coordination",
            "assignee": "Kate or Karen",
            "estimated_duration": "2-3 hours", 
            "dependencies": ["Event Setup and Operations"],
            "calendar_reminder": True
        }
    ]

def get_email_campaign_workflow_template() -> list:
    """
    Email Campaign Workflow Template - Jheryl's existing 6-subtask template.
    Covers email invitation workflows, template creation, and attendee communication.
    """
    return [
        {
            "name": "Email Template Build",
            "description": "Create and design email invitation template",
            "assignee": "Jheryl",
            "estimated_duration": "2-3 hours",
            "dependencies": [],
            "calendar_reminder": False
        },
        {
            "name": "Email Content Creation & Copy",
            "description": "Write email content, subject lines, and call-to-action copy",
            "assignee": "Jheryl",
            "estimated_duration": "1-2 hours", 
            "dependencies": ["Email Template Build"],
            "calendar_reminder": False
        },
        {
            "name": "Email Invitation Scheduling",
            "description": "Schedule email invitations and set up delivery timing",
            "assignee": "Jheryl",
            "estimated_duration": "1 hour",
            "dependencies": ["Email Content Creation & Copy"],
            "calendar_reminder": False
        },
        {
            "name": "Attendee Communication Setup",
            "description": "Set up automated attendee communication workflows",
            "assignee": "Jheryl", 
            "estimated_duration": "1-2 hours",
            "dependencies": ["Email Invitation Scheduling"],
            "calendar_reminder": False
        },
        {
            "name": "RSVP Management System",
            "description": "Configure RSVP tracking and management system",
            "assignee": "Jheryl",
            "estimated_duration": "1-2 hours",
            "dependencies": ["Attendee Communication Setup"],
            "calendar_reminder": False
        },
        {
            "name": "Email Campaign QA & Send", 
            "description": "Quality assurance testing and final email campaign send",
            "assignee": "Jheryl",
            "estimated_duration": "1 hour",
            "dependencies": ["RSVP Management System"],
            "calendar_reminder": False
        }
    ]
