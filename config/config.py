"""
Core Utilities
==============
Essential utilities for the marketing bot
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@dataclass
class BotConfig:
    """Core bot configuration."""
    # Slack configuration
    slack_bot_token: str
    slack_signing_secret: str
    slack_app_token: str
    
    # API keys
    openai_api_key: Optional[str] = None
    monday_api_token: Optional[str] = None
    
    # Bot settings
    bot_name: str = "Fetch Marketing Bot"
    environment: str = "production"
    debug: bool = False

def load_config() -> BotConfig:
    """Load configuration from environment variables."""
    return BotConfig(
        slack_bot_token=os.getenv('SLACK_BOT_TOKEN', ''),
        slack_signing_secret=os.getenv('SLACK_SIGNING_SECRET', ''),
        slack_app_token=os.getenv('SLACK_APP_TOKEN', ''),
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        monday_api_token=os.getenv('MONDAY_API_TOKEN'),
        environment=os.getenv('ENVIRONMENT', 'production'),
        debug=os.getenv('DEBUG', '').lower() == 'true'
    )

def validate_config(config: BotConfig) -> bool:
    """Validate that required configuration is present."""
    required_fields = ['slack_bot_token', 'slack_signing_secret', 'slack_app_token']
    
    for field in required_fields:
        if not getattr(config, field):
            logging.error(f"Missing required configuration: {field}")
            return False
    
    return True

def setup_logging(config: BotConfig):
    """Setup logging based on configuration."""
    level = logging.DEBUG if config.debug else logging.INFO
    logging.getLogger().setLevel(level)
    
    # Add handler for Slack errors
    slack_logger = logging.getLogger('slack_error_handler')
    slack_logger.setLevel(level)

async def safe_api_call(func, *args, **kwargs):
    """Safely execute an API call with error handling."""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        logging.error(f"API call failed: {func.__name__} - {e}")
        return None

def format_slack_message(title: str, content: str, emoji: str = "✅") -> str:
    """Format a consistent Slack message using SlackFormatter."""
    from utils.slack_formatting import SlackFormatter
    return f"{emoji} {SlackFormatter.bold(title)}\n\n{content}"

def get_env_status() -> Dict[str, Any]:
    """Get environment status for health checks."""
    config = load_config()
    
    return {
        "environment": config.environment,
        "slack_configured": bool(config.slack_bot_token),
        "openai_configured": bool(config.openai_api_key),
        "monday_configured": bool(config.monday_api_token),
        "debug_mode": config.debug
    }