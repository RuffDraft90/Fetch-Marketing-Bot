"""
Slack Text Formatting Standards
==============================
Centralized formatting utilities for consistent, professional Slack UI
"""

import re
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class SlackFormatter:
    """Professional Slack text formatting utilities."""
    
    # Brand colors and emojis
    FETCH_BRAND = {
        "primary_emoji": "🎯",
        "success_emoji": "✅", 
        "warning_emoji": "⚠️",
        "error_emoji": "❌",
        "info_emoji": "💡",
        "ai_emoji": "🤖",
        "calendar_emoji": "📅",
        "location_emoji": "📍",
        "link_emoji": "🔗"
    }
    
    # Team member email mapping for Slack user lookup
    TEAM_EMAIL_MAP = {
        "kelly redding": "k.redding@fetchrewards.com",
        "karen": "k.lowry@fetchrewards.com",
        "kate": "k.jeffries@fetchrewards.com", 
        "jennifer porter": "j.porter@fetchrewards.com",
        "jamie mann": "j.mann@fetchrewards.com",
        "karen lowry": "k.lowry@fetchrewards.com",
        "kate jeffries": "k.jeffries@fetchrewards.com",
        # Add variations for partial names
        "kelly": "k.redding@fetchrewards.com",
        "jennifer": "j.porter@fetchrewards.com",
        "jamie": "j.mann@fetchrewards.com",
        # Handle common variations
        "k. redding": "k.redding@fetchrewards.com",
        "k.redding": "k.redding@fetchrewards.com",
        "k. lowry": "k.lowry@fetchrewards.com", 
        "k.lowry": "k.lowry@fetchrewards.com",
        "k. jeffries": "k.jeffries@fetchrewards.com",
        "k.jeffries": "k.jeffries@fetchrewards.com",
        "j. porter": "j.porter@fetchrewards.com",
        "j.porter": "j.porter@fetchrewards.com",
        "j. mann": "j.mann@fetchrewards.com",
        "j.mann": "j.mann@fetchrewards.com"
    }
    
    @staticmethod
    def header(text: str, emoji: str = None) -> str:
        """Create a professional header with optional emoji."""
        emoji_prefix = f"{emoji} " if emoji else f"{SlackFormatter.FETCH_BRAND['primary_emoji']} "
        return f"{emoji_prefix}*{text}*"
    
    @staticmethod
    def subheader(text: str) -> str:
        """Create a subheader in mrkdwn format."""
        return f"*{text}*"
    
    @staticmethod
    def bold(text: str) -> str:
        """Make text bold."""
        return f"*{text}*"
    
    @staticmethod
    def italic(text: str) -> str:
        """Make text italic."""
        return f"_{text}_"
    
    @staticmethod
    def code(text: str) -> str:
        """Format as inline code."""
        return f"`{text}`"
    
    @staticmethod
    def code_block(text: str, language: str = None) -> str:
        """Format as code block with optional language specification."""
        if language:
            return f"```{language}\n{text}\n```"
        return f"```{text}```"
    
    @staticmethod
    def user_mention(user_id: str) -> str:
        """Create a user mention."""
        return f"<@{user_id}>"
    
    @staticmethod
    def channel_mention(channel_id: str) -> str:
        """Create a channel mention."""
        return f"<#{channel_id}>"
    
    @staticmethod
    def link(url: str, text: str) -> str:
        """Create a formatted link."""
        return f"<{url}|{text}>"
    
    @staticmethod
    def bullet_list(items: List[str], emoji: str = "•") -> str:
        """Create a professional bullet list."""
        return "\n".join([f"{emoji} {item}" for item in items])
    
    @staticmethod
    def numbered_list(items: List[str]) -> str:
        """Create a numbered list."""
        return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
    
    @staticmethod
    def status_message(status: str, message: str, emoji_override: str = None) -> str:
        """Create a status message with appropriate emoji."""
        status_emojis = {
            "success": SlackFormatter.FETCH_BRAND["success_emoji"],
            "error": SlackFormatter.FETCH_BRAND["error_emoji"], 
            "warning": SlackFormatter.FETCH_BRAND["warning_emoji"],
            "info": SlackFormatter.FETCH_BRAND["info_emoji"]
        }
        
        emoji = emoji_override or status_emojis.get(status.lower(), SlackFormatter.FETCH_BRAND["info_emoji"])
        return f"{emoji} {message}"
    
    @staticmethod
    def campaign_summary(name: str, date: str, location: str, goals: str = None) -> str:
        """Format a professional campaign summary."""
        lines = [
            SlackFormatter.subheader(name),
            f"{SlackFormatter.FETCH_BRAND['calendar_emoji']} *Date:* {date}",
            f"{SlackFormatter.FETCH_BRAND['location_emoji']} *Location:* {location}"
        ]
        
        if goals:
            # Truncate long goals professionally
            goal_text = goals[:100] + "..." if len(goals) > 100 else goals
            lines.append(f"{SlackFormatter.FETCH_BRAND['primary_emoji']} *Goals:* {goal_text}")
        
        return "\n".join(lines)
    
    @staticmethod
    def resource_links(links: Dict[str, str]) -> str:
        """Format resource links section with clean, professional formatting."""
        if not links:
            return ""
        
        lines = ["*🔗 Resources:*"]
        for name, url in links.items():
            # Clean up the name formatting and use proper link formatting
            clean_name = name.replace("🔔 ", "").replace("📄 ", "").replace("📋 ", "").replace("🗓️ ", "")
            
            # Add appropriate emoji based on content type
            if "Brief" in name or "Doc" in name:
                emoji = "📄"
            elif "Monday" in name or "Tickets" in name:
                emoji = "📋"
            elif "Calendar" in name:
                emoji = "🗓️"
            elif "Reminder" in name:
                emoji = "🔔"
            else:
                emoji = "🔗"
            
            # Format as clean link if URL is valid, otherwise just show the text
            if url and url != "#" and url.startswith(("http://", "https://")):
                lines.append(f"   {emoji} {SlackFormatter.link(url, clean_name)}")
            else:
                lines.append(f"   {emoji} {clean_name}")
        
        return "\n".join(lines)
    
    @staticmethod
    def modal_description(title: str, subtitle: str) -> str:
        """Format modal description consistently."""
        return f"{SlackFormatter.header(title)}\n{subtitle}"
    
    @staticmethod
    def ai_suggestion_item(index: int, suggestion: str) -> str:
        """Format AI suggestion list item."""
        # Remove existing numbering if present (e.g., "1. Campaign name" -> "Campaign name")
        cleaned_suggestion = suggestion
        if suggestion.strip():
            # Check if suggestion starts with number and dot
            import re
            cleaned_suggestion = re.sub(r'^\d+\.\s*', '', suggestion.strip())
        
        return f"*{index}.* {cleaned_suggestion}"
    
    @staticmethod
    def campaign_status_badge(status: str) -> str:
        """Create status badge with appropriate formatting."""
        status_map = {
            "active": "🟢 *Active*",
            "planning": "🟡 *Planning*", 
            "completed": "🔵 *Completed*",
            "paused": "🔴 *Paused*",
            "draft": "⚪ *Draft*"
        }
        return status_map.get(status.lower(), f"• *{status.title()}*")
    
    @staticmethod
    def workflow_confirmation(workflow_type: str, name: str, details: Dict[str, str]) -> str:
        """Format workflow confirmation message."""
        if workflow_type == "simple":
            header = SlackFormatter.status_message("success", f"Simple Event Created: {name}")
        else:
            header = SlackFormatter.status_message("success", f"Full Campaign Workflow Created: {name}", "🚀")
        
        lines = [header, ""]
        
        # Add details
        for key, value in details.items():
            if key == "date":
                lines.append(f"{SlackFormatter.FETCH_BRAND['calendar_emoji']} *Date:* {value}")
            elif key == "location":
                lines.append(f"{SlackFormatter.FETCH_BRAND['location_emoji']} *Location:* {value}")
            elif key == "goals":
                goal_text = value[:100] + "..." if len(value) > 100 else value
                lines.append(f"{SlackFormatter.FETCH_BRAND['primary_emoji']} *Goals:* {goal_text}")
        
        return "\n".join(lines)
    
    @staticmethod
    async def lookup_slack_user(client, name: str) -> Optional[str]:
        """Lookup Slack user by name and return formatted mention."""
        if not name or not client:
            return None
        
        # Normalize name for lookup
        name_lower = name.lower().strip()
        
        # Get email from mapping
        email = SlackFormatter.TEAM_EMAIL_MAP.get(name_lower)
        if not email:
            logger.debug(f"No email mapping found for: {name}")
            return None
        
        try:
            # Look up user by email
            response = await client.users_lookupByEmail(email=email)
            if response.get("ok") and response.get("user"):
                user_id = response["user"]["id"]
                user_name = response["user"].get("real_name", response["user"].get("name", ""))
                logger.info(f"✅ Found Slack user: {name} ({email}) -> @{user_name} ({user_id})")
                return f"<@{user_id}>"
            else:
                logger.info(f"❌ User not found for email: {email}")
                return None
        except Exception as e:
            logger.info(f"⚠️ Error looking up user {email}: {e}")
            return None
    
    @staticmethod
    async def format_assignee_name(client, name: str) -> str:
        """Format assignee name with Slack mention if possible, otherwise bold."""
        if not name:
            return ""
        
        # Handle multiple assignees (e.g., "Karen or Kate")
        if " or " in name.lower():
            parts = [part.strip() for part in name.split(" or ")]
            formatted_parts = []
            
            for part in parts:
                slack_mention = await SlackFormatter.lookup_slack_user(client, part)
                if slack_mention:
                    formatted_parts.append(slack_mention)
                else:
                    formatted_parts.append(SlackFormatter.bold(part))
            
            return " or ".join(formatted_parts)
        
        # Single assignee - try to get Slack mention
        slack_mention = await SlackFormatter.lookup_slack_user(client, name)
        if slack_mention:
            return slack_mention
        
        # Fallback to bold formatting
        return SlackFormatter.bold(name)
    
    @staticmethod
    def campaign_success_message(name: str, links: Dict[str, str] = None, workflow_tasks: list = None) -> str:
        """Format a complete campaign success message with all components."""
        lines = [
            SlackFormatter.status_message("success", f"Campaign Created: {name}", "✅"),
            ""
        ]
        
        # Add resources section
        if links:
            lines.append(SlackFormatter.resource_links(links))
            lines.append("")
        
        # Add workflow summary
        if workflow_tasks:
            lines.append("*📋 Automated Workflow Created:*")
            for task in workflow_tasks[:3]:  # Show first 3 tasks
                assignee = SlackFormatter.bold(task.get('assignee', 'Assigned'))
                lines.append(f"   • {task.get('name', 'Task')} → {assignee}")
            
            if len(workflow_tasks) > 3:
                lines.append(f"   • ... and {len(workflow_tasks) - 3} more tasks")
        
        return "\n".join(lines)
    
    @staticmethod
    async def campaign_success_message_with_mentions(client, name: str, links: Dict[str, str] = None, workflow_tasks: list = None) -> str:
        """Format a complete campaign success message with Slack user mentions."""
        lines = [
            SlackFormatter.status_message("success", f"Campaign Created: {name}", "✅"),
            ""
        ]
        
        # Add resources section
        if links:
            lines.append(SlackFormatter.resource_links(links))
            lines.append("")
        
        # Add workflow summary with user mentions
        if workflow_tasks:
            lines.append("*📋 Automated Workflow Created:*")
            for task in workflow_tasks[:3]:  # Show first 3 tasks
                assignee_raw = task.get('assignee', 'Assigned')
                assignee_formatted = await SlackFormatter.format_assignee_name(client, assignee_raw)
                lines.append(f"   • {task.get('name', 'Task')} → {assignee_formatted}")
            
            if len(workflow_tasks) > 3:
                lines.append(f"   • ... and {len(workflow_tasks) - 3} more tasks")
        
        return "\n".join(lines)
    
    @staticmethod
    def error_message(message: str, context: str = None) -> str:
        """Format error message professionally."""
        error_msg = SlackFormatter.status_message("error", f"*Error:* {message}")
        if context:
            error_msg += f"\n{SlackFormatter.italic(f'Context: {context}')}"
        return error_msg
    
    @staticmethod
    def validation_errors(errors: Dict[str, str]) -> str:
        """Format validation errors for Slack."""
        if not errors:
            return ""
        
        lines = [SlackFormatter.status_message("error", "*Please fix the following:*")]
        for field, error in errors.items():
            field_name = field.replace('_', ' ').title()
            lines.append(f"• *{field_name}:* {error}")
        
        return "\n".join(lines)
    
    @staticmethod
    def tip_message(message: str) -> str:
        """Format helpful tip message."""
        return SlackFormatter.status_message("info", f"*Tip:* {message}")
    
    @staticmethod
    def progress_indicator(current: int, total: int, description: str = "") -> str:
        """Create a progress indicator."""
        percentage = int((current / total) * 100) if total > 0 else 0
        bar_length = 10
        filled = int((current / total) * bar_length) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        
        progress = f"▎{bar} {percentage}% ({current}/{total})"
        return f"{progress}\n{description}" if description else progress
    
    @staticmethod
    def section_divider(text: str = None) -> str:
        """Create a section divider."""
        if text:
            return f"\n━━━ {text} ━━━\n"
        return "\n━━━━━━━━━━━━━━━━━━━━━\n"

class FetchBrandFormatter(SlackFormatter):
    """Fetch-specific formatting extensions."""
    
    @staticmethod
    def receipt_hero_message(user_name: str, points: int, story: str) -> str:
        """Format Receipt Hero feature message."""
        return SlackFormatter.modal_description(
            "Receipt Hero Spotlight",
            f"Meet {SlackFormatter.bold(user_name)} - earned {SlackFormatter.bold(f'{points:,} points')}!\n\n{story}"
        )
    
    @staticmethod
    def scan_streak_message(streak: int, user_name: str = None) -> str:
        """Format scan streak achievement."""
        streak_emoji = "🔥" if streak >= 7 else "⚡"
        user_text = f" {user_name}" if user_name else ""
        return f"{streak_emoji} *{streak}-day scan streak{user_text}!*"
    
    @staticmethod
    def partner_spotlight(brand_name: str, offer: str, multiplier: str = None) -> str:
        """Format partner brand spotlight."""
        lines = [
            SlackFormatter.header(f"Partner Spotlight: {brand_name}", "🎯"),
            f"🎁 *Current Offer:* {offer}"
        ]
        
        if multiplier:
            lines.append(f"⚡ *Bonus:* {multiplier}")
        
        return "\n".join(lines)
    
    @staticmethod
    def points_milestone(points: int, milestone_type: str = "achievement") -> str:
        """Format points milestone message."""
        milestone_emojis = {
            "first": "🎉",
            "achievement": "🏆", 
            "major": "💎",
            "record": "🌟"
        }
        
        emoji = milestone_emojis.get(milestone_type, "🎯")
        formatted_points = f"{points:,}"
        
        return SlackFormatter.status_message("success", 
            f"Milestone Reached: {SlackFormatter.bold(f'{formatted_points} points')}!", emoji)

# Convenience functions for common patterns
def format_modal_header(title: str, subtitle: str = None) -> Dict[str, str]:
    """Create standardized modal header block."""
    text = SlackFormatter.header(title)
    if subtitle:
        text += f"\n{subtitle}"
    
    return {
        "type": "section",
        "text": {"type": "mrkdwn", "text": text}
    }

def format_divider() -> Dict[str, str]:
    """Create divider block."""
    return {"type": "divider"}

def format_button_section(text: str, button_text: str, action_id: str, style: str = None) -> Dict[str, str]:
    """Create section with button accessory."""
    section = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": text},
        "accessory": {
            "type": "button",
            "text": {"type": "plain_text", "text": button_text},
            "action_id": action_id
        }
    }
    
    if style:
        section["accessory"]["style"] = style
    
    return section

def format_context_footer(message: str) -> Dict[str, str]:
    """Create context footer block."""
    return {
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": SlackFormatter.tip_message(message)}
        ]
    }

# Export main classes and functions
__all__ = [
    'SlackFormatter',
    'FetchBrandFormatter', 
    'format_modal_header',
    'format_divider',
    'format_button_section',
    'format_context_footer'
]