"""
Core Services Package
====================
All essential services for the marketing bot
"""

import logging

logger = logging.getLogger(__name__)

# Import core services
try:
    from services.ai_service import ai_service, AIService
    from services.google_slides_service import google_slides_service, GoogleSlidesService
    from services.google_calendar_service import google_calendar_service, GoogleCalendarService
    from services.google_docs_service import google_docs_service, GoogleDocsService
    from services.monday_service import monday_service, MondayService
    
    __all__ = [
        'ai_service', 'AIService',
        'google_slides_service', 'GoogleSlidesService', 
        'google_calendar_service', 'GoogleCalendarService',
        'google_docs_service', 'GoogleDocsService',
        'monday_service', 'MondayService'
    ]
    
    logger.info("✅ All core services loaded successfully")
    
except ImportError as e:
    logger.error(f"❌ Failed to load some services: {e}")
    __all__ = []

def get_service_status():
    """Get status of all services."""
    status = {}
    
    try:
        status['ai'] = ai_service.is_configured()
        status['google_slides'] = google_slides_service.is_configured()
        status['google_calendar'] = google_calendar_service.is_configured()
        status['google_docs'] = google_docs_service.is_configured()
        status['monday'] = monday_service.is_configured()
    except Exception as e:
        logger.error(f"Error checking service status: {e}")
        status = {'error': str(e)}
    
    return status
