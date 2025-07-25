"""
AI Service for Marketing Bot
===========================
Simplified AI service for generating marketing content and suggestions
"""

import os
import logging
from typing import Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIService:
    """AI service for generating marketing content and suggestions."""
    
    def __init__(self):
        """Initialize AI service with OpenAI."""
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "gpt-3.5-turbo"
        self.max_tokens = 500
        self.temperature = 0.7
    
    async def generate_campaign_suggestions(self, campaign_type: str, count: int = 5) -> list:
        """
        Generate campaign suggestions using AI.
        
        Args:
            campaign_type: Type of campaign (email, social, content, etc.)
            count: Number of suggestions to generate
            
        Returns:
            List of campaign suggestions
        """
        if not self.client:
            logger.warning("OpenAI client not configured, returning fallback suggestions")
            return self._get_fallback_suggestions(campaign_type, count)
        
        try:
            prompt = self._get_prompt_for_type(campaign_type, count)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior marketing strategist for Fetch Rewards, a leading mobile rewards platform."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            suggestions = [s.strip() for s in content.split('\n') if s.strip()]
            return suggestions[:count]
            
        except Exception as e:
            logger.error(f"AI suggestion generation failed: {e}")
            return self._get_fallback_suggestions(campaign_type, count)
    
    async def generate_content(self, content_type: str, topic: str) -> Dict[str, str]:
        """
        Generate marketing content using AI.
        
        Args:
            content_type: Type of content (email, social, blog, etc.)
            topic: Topic or theme for the content
            
        Returns:
            Dict with generated content
        """
        if not self.client:
            logger.warning("OpenAI client not configured, returning fallback content")
            return self._get_fallback_content(content_type, topic)
        
        try:
            prompt = f"Create {content_type} content about {topic} for Fetch Rewards mobile app users. Make it engaging and action-oriented."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a creative marketing copywriter for Fetch Rewards."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            return {"content": content, "type": content_type, "topic": topic}
            
        except Exception as e:
            logger.error(f"AI content generation failed: {e}")
            return self._get_fallback_content(content_type, topic)
    
    def _get_prompt_for_type(self, campaign_type: str, count: int) -> str:
        """Get AI prompt based on campaign type."""
        prompts = {
            "email": f"Generate {count} Fetch Rewards email campaigns focused on receipt scanning, points redemption, and brand partnerships. Include creative hooks. One per line.",
            "social": f"Generate {count} viral Fetch Rewards social campaigns about receipt heroes, scan streaks, and surprise rewards. Focus on UGC and gamification. One per line.",
            "content": f"Generate {count} Fetch content campaigns showcasing user journeys, partner spotlights, and points economy education. One per line.",
            "event": f"Generate {count} Fetch experiential events like pop-ups, campus tours, and brand summits. Focus on receipt scanning and rewards in real life. One per line.",
            "campaign": f"Generate {count} integrated Fetch marketing campaigns featuring receipt scanning, reward discovery, and brand partnerships. Include gamification elements. One per line.",
            "slides": f"Generate {count} Fetch presentation topics for partners, internal teams, and stakeholders. Focus on user data, journey maps, and brand case studies. One per line."
        }
        return prompts.get(campaign_type, prompts["campaign"])
    
    def _get_fallback_suggestions(self, campaign_type: str, count: int) -> list:
        """Get fallback suggestions when AI is unavailable."""
        fallbacks = {
            "email": [
                "Weekly Bonus Points Roundup",
                "Exclusive Partner Store Spotlight", 
                "Receipt Scanning Tips & Tricks",
                "Member Milestone Celebration",
                "Limited-Time Double Points Offer"
            ],
            "social": [
                "#ScanToWin Challenge",
                "Receipt Art Contest",
                "Fetch Friends Referral Drive",
                "Store Partnership Announcements",
                "User Success Story Features"
            ],
            "content": [
                "Smart Shopping Guide Blog Series",
                "Receipt Scanning Best Practices",
                "Partner Store Deep Dives",
                "Cashback Optimization Tips",
                "Mobile App Feature Tutorials"
            ],
            "event": [
                "Fetch Rewards User Meetup",
                "Partner Store Pop-up Events",
                "Mobile Scanning Workshops",
                "Cashback Celebration Days",
                "Referral Program Launch Events"
            ]
        }
        
        suggestions = fallbacks.get(campaign_type, fallbacks["email"])
        return (suggestions * ((count // len(suggestions)) + 1))[:count]
    
    def _get_fallback_content(self, content_type: str, topic: str) -> Dict[str, str]:
        """Get fallback content when AI is unavailable."""
        return {
            "content": f"Exciting {content_type} content about {topic} for Fetch Rewards users!",
            "type": content_type,
            "topic": topic
        }
    
    def is_configured(self) -> bool:
        """Check if AI service is properly configured."""
        return bool(self.client)

# Global instance
ai_service = AIService()