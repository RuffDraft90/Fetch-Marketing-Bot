#!/usr/bin/env python3
"""
Core Marketing Bot - Simplified Entry Point
============================================

A simplified, working Slack marketing bot with core functionality:
- Main dashboard with Create and Suggest options
- Simple form handling for presentations, slides, and campaigns
- Basic AI integration ready for enhancement

Core Features:
- Slack Bot Framework with async support
- Main modal with Create/Suggest functionality
- Form submissions for content creation
- Ready for feature enhancements
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=False)

# Import local modules
from config.config import load_config, validate_config
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Reduce noise from verbose libraries
logging.getLogger('slack_bolt.AsyncApp').setLevel(logging.INFO)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class CoreMarketingBot:
    """Main application class for the Core Marketing Bot."""
    
    def __init__(self):
        self.app = None
        self.is_running = False
        self._initialized = False
    
    async def initialize(self):
        """Initialize the bot application."""
        if self._initialized:
            return
        
        try:
            logger.info("🚀 Initializing Core Marketing Bot...")
            
            # Validate configuration
            config = load_config()
            if not validate_config(config):
                raise RuntimeError("Configuration validation failed")
            
            # Create Slack app
            await self._create_slack_app()
            
            # Register core handlers
            await self._register_handlers()
            
            self._initialized = True
            logger.info("✅ Core Marketing Bot initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize bot: {e}")
            raise
    
    async def _create_slack_app(self):
        """Create and configure the Slack app."""
        from slack_bolt.async_app import AsyncApp
        
        config = load_config()
        
        self.app = AsyncApp(
            token=config.slack_bot_token,
            signing_secret=config.slack_signing_secret,
            process_before_response=True
        )
        
        logger.info("✅ Slack app created")
    
    async def _register_handlers(self):
        """Register core bot handlers only."""
        logger.info("📋 Registering core handlers...")
        
        # Import and register CLEAN handlers
        from handlers.core_slash_commands import register_slash_commands
        from handlers.simple_handlers import register_simple_handlers
        from handlers.campaign_submission import register_campaign_submission
        from handlers.core_clean_actions import register_clean_actions
        from modals.core_modal_system import register_core_modals
        
        # Register clean handlers only
        register_slash_commands(self.app)
        register_simple_handlers(self.app)
        register_campaign_submission(self.app)
        register_clean_actions(self.app)
        register_core_modals(self.app)
        
        # Core handlers only - no additional systems
        
        logger.info("✅ Core handlers registered")
    
    async def start(self, port: int = 3000):
        """Start the bot application."""
        await self.initialize()
        
        try:
            logger.info(f"🚀 Starting Core Marketing Bot on port {port}")
            self.is_running = True
            
            # Get app token for socket mode
            app_token = os.environ.get("SLACK_APP_TOKEN")
            if not app_token:
                raise RuntimeError("SLACK_APP_TOKEN is required for socket mode")
            
            # Start in socket mode with connection stability settings
            from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
            
            handler = AsyncSocketModeHandler(self.app, app_token)
            
            # Configure connection stability
            if hasattr(handler, 'client') and hasattr(handler.client, 'socket_mode_client'):
                socket_client = handler.client.socket_mode_client
                socket_client.ping_interval = 30  # Ping every 30 seconds
                socket_client.auto_reconnect_enabled = True
                socket_client.session_timeout_seconds = 90  # Longer timeout
                
            await handler.start_async()
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Stop the bot gracefully."""
        logger.info("🛑 Stopping Core Marketing Bot...")
        self.is_running = False
        logger.info("✅ Bot stopped successfully")


async def main():
    """Main application entry point."""
    bot = CoreMarketingBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        return 1
    finally:
        await bot.stop()
    
    return 0


if __name__ == "__main__":
    # Run the application
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
