"""
Google Slides Service
====================
Service for creating Fetch Rewards branded Google Slides presentations
"""

import os
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FetchBrandColors:
    """Fetch Rewards brand color palette."""
    FETCH_BLUE = "#0074E4"
    DARK_NAVY = "#00263B"
    LIGHT_GREY = "#F5F7F9"
    ACCENT_GREEN = "#00C48C"
    WARM_ORANGE = "#FF8A3C"
    DEEP_CHARCOAL = "#333333"
    WHITE = "#FFFFFF"

@dataclass
class SlideTemplate:
    """Template configuration for different slide types."""
    name: str
    theme: str
    background_color: str
    accent_color: str
    font_family: str = "Montserrat"
    use_logo: bool = True

class FetchSlideTemplates:
    """Fetch Rewards slide template configurations."""
    
    EXECUTIVE = SlideTemplate(
        name="Executive Overview",
        theme="premium",
        background_color=FetchBrandColors.DARK_NAVY,
        accent_color=FetchBrandColors.WARM_ORANGE
    )
    
    COMMUNITY = SlideTemplate(
        name="Community Retrospective", 
        theme="fun",
        background_color=FetchBrandColors.FETCH_BLUE,
        accent_color=FetchBrandColors.ACCENT_GREEN
    )
    
    DATA_INSIGHTS = SlideTemplate(
        name="Data Insights",
        theme="insight-driven",
        background_color=FetchBrandColors.LIGHT_GREY,
        accent_color=FetchBrandColors.FETCH_BLUE
    )
    
    PRODUCT_LAUNCH = SlideTemplate(
        name="Product Launch",
        theme="innovative",
        background_color=FetchBrandColors.WHITE,
        accent_color=FetchBrandColors.WARM_ORANGE
    )

class GoogleSlidesService:
    """Service for Google Slides integration with Fetch branding."""
    
    def __init__(self):
        """Initialize Google Slides service."""
        self.credentials_file = os.path.join(os.path.dirname(__file__), 'google_credentials.json')
        self.service = None
        self.colors = FetchBrandColors()
        self.templates = FetchSlideTemplates()
        
    async def create_presentation(self, title: str, outline: str = "", presentation_type: str = "executive") -> Optional[Dict[str, Any]]:
        """
        Create a Fetch-branded Google Slides presentation.
        
        Args:
            title: Presentation title
            outline: Content outline
            presentation_type: Template type (executive, community, data_insights, product_launch)
            
        Returns:
            Dict with presentation info or None if failed
        """
        try:
            logger.info(f"Creating Fetch-branded Google Slides presentation: {title}")
            
            # Get template configuration
            template = self._get_template(presentation_type)
            
            # Generate slide structure
            slide_structure = self._generate_slide_structure(title, outline, template)
            
            # Mock response with enhanced details
            presentation_id = f"fetch_presentation_{hash(title) % 10000}"
            return {
                "id": presentation_id,
                "url": f"https://docs.google.com/presentation/d/fetch_presentation_{hash(title) % 10000}/edit",
                "title": title,
                "template": template.name,
                "theme": template.theme,
                "slide_count": len(slide_structure),
                "slides": slide_structure,
                "brand_colors": {
                    "primary": template.background_color,
                    "accent": template.accent_color
                },
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create Google Slides presentation: {e}")
            return None
    
    def _get_template(self, presentation_type: str) -> SlideTemplate:
        """Get template configuration based on type."""
        template_map = {
            "executive": self.templates.EXECUTIVE,
            "community": self.templates.COMMUNITY,
            "data_insights": self.templates.DATA_INSIGHTS,
            "product_launch": self.templates.PRODUCT_LAUNCH
        }
        return template_map.get(presentation_type, self.templates.EXECUTIVE)
    
    def _generate_slide_structure(self, title: str, outline: str, template: SlideTemplate) -> List[Dict[str, Any]]:
        """Generate slide structure based on template and content."""
        slides = []
        
        # Slide 1: Cover
        slides.append(self._create_cover_slide(title, template))
        
        # Slide 2: Agenda (if outline provided)
        if outline:
            slides.append(self._create_agenda_slide(outline, template))
        
        # Template-specific slides
        if template.theme == "premium":
            slides.extend(self._create_executive_slides(template))
        elif template.theme == "fun":
            slides.extend(self._create_community_slides(template))
        elif template.theme == "insight-driven":
            slides.extend(self._create_data_slides(template))
        elif template.theme == "innovative":
            slides.extend(self._create_product_slides(template))
        
        # Final slide: Next Steps
        slides.append(self._create_next_steps_slide(template))
        
        return slides
    
    def _create_cover_slide(self, title: str, template: SlideTemplate) -> Dict[str, Any]:
        """Create branded cover slide."""
        current_time = datetime.now().strftime("%A, %b %d • %I:%M %p CT")
        
        return {
            "slide_number": 1,
            "type": "cover",
            "title": title,
            "subtitle": current_time,
            "background_color": template.background_color,
            "title_color": self.colors.WHITE if template.background_color == self.colors.DARK_NAVY else self.colors.DEEP_CHARCOAL,
            "font_family": template.font_family,
            "font_size": "54pt",
            "font_weight": "bold",
            "logo_position": "bottom-right",
            "layout": "center"
        }
    
    def _create_agenda_slide(self, outline: str, template: SlideTemplate) -> Dict[str, Any]:
        """Create agenda slide from outline."""
        agenda_items = self._parse_outline_to_bullets(outline)
        
        return {
            "slide_number": 2,
            "type": "agenda",
            "title": "In This Deck",
            "background_color": self.colors.LIGHT_GREY,
            "title_color": self.colors.DEEP_CHARCOAL,
            "bullet_color": template.accent_color,
            "font_family": template.font_family,
            "items": agenda_items
        }
    
    def _create_executive_slides(self, template: SlideTemplate) -> List[Dict[str, Any]]:
        """Create executive-style slides."""
        return [
            {
                "slide_number": 3,
                "type": "metrics",
                "title": "Key Metrics",
                "background_color": self.colors.WHITE,
                "chart_type": "bar_and_line",
                "accent_color": self.colors.FETCH_BLUE,
                "highlight_color": self.colors.ACCENT_GREEN,
                "layout": "chart_with_callout"
            },
            {
                "slide_number": 4,
                "type": "next_steps",
                "title": "Next Steps",
                "background_color": self.colors.WHITE,
                "footer_color": self.colors.DARK_NAVY,
                "layout": "three_column_cards",
                "accent_color": template.accent_color
            }
        ]
    
    def _create_community_slides(self, template: SlideTemplate) -> List[Dict[str, Any]]:
        """Create community-style slides."""
        return [
            {
                "slide_number": 3,
                "type": "highlights",
                "title": "Community Highlights",
                "background_color": self.colors.WHITE,
                "callout_color": self.colors.WARM_ORANGE,
                "bullets": [
                    "🎯 Reached 150+ participants across 5 cities",
                    "📸 Generated 18 pieces of authentic UGC content", 
                    "💬 Achieved average NPS score of 92!"
                ],
                "layout": "rounded_callout"
            },
            {
                "slide_number": 4,
                "type": "testimonials",
                "title": "What Our Community Says",
                "background_color": self.colors.LIGHT_GREY,
                "layout": "dual_testimonials",
                "accent_color": template.accent_color
            }
        ]
    
    def _create_data_slides(self, template: SlideTemplate) -> List[Dict[str, Any]]:
        """Create data-insight slides."""
        return [
            {
                "slide_number": 3,
                "type": "data_visualization",
                "title": "Performance Analysis",
                "background_color": self.colors.WHITE,
                "chart_types": ["bar", "line", "pie"],
                "primary_color": self.colors.FETCH_BLUE,
                "accent_color": self.colors.ACCENT_GREEN,
                "layout": "multi_chart"
            },
            {
                "slide_number": 4,
                "type": "insights",
                "title": "Key Insights",
                "background_color": self.colors.LIGHT_GREY,
                "callout_style": "data_cards",
                "accent_color": template.accent_color
            }
        ]
    
    def _create_product_slides(self, template: SlideTemplate) -> List[Dict[str, Any]]:
        """Create product launch slides."""
        return [
            {
                "slide_number": 3,
                "type": "product_features",
                "title": "New Features",
                "background_color": self.colors.WHITE,
                "layout": "feature_grid",
                "accent_color": template.accent_color,
                "highlight_color": self.colors.FETCH_BLUE
            },
            {
                "slide_number": 4,
                "type": "launch_timeline",
                "title": "Launch Timeline",
                "background_color": self.colors.LIGHT_GREY,
                "layout": "timeline",
                "accent_color": template.accent_color
            }
        ]
    
    def _create_next_steps_slide(self, template: SlideTemplate) -> Dict[str, Any]:
        """Create final next steps slide."""
        return {
            "slide_number": 5,
            "type": "next_steps",
            "title": "Next Steps",
            "background_color": self.colors.WHITE,
            "footer_color": template.accent_color,
            "layout": "cta_buttons",
            "font_family": template.font_family
        }
    
    def _parse_outline_to_bullets(self, outline: str) -> List[str]:
        """Parse outline text into bullet points."""
        if not outline:
            return [
                "Overview & Objectives",
                "Key Findings", 
                "Strategic Recommendations",
                "Next Steps & Timeline"
            ]
        
        # Simple parsing - split by lines and clean up
        lines = [line.strip() for line in outline.split('\n') if line.strip()]
        return lines[:6]  # Limit to 6 bullets for readability
    
    def get_template_options(self) -> Dict[str, Dict[str, Any]]:
        """Get available template options with descriptions."""
        return {
            "executive": {
                "name": "Executive Overview",
                "description": "Premium design for leadership presentations",
                "theme": "premium",
                "best_for": ["Strategy reviews", "Board presentations", "Executive summaries"],
                "colors": [self.colors.DARK_NAVY, self.colors.WARM_ORANGE]
            },
            "community": {
                "name": "Community Retrospective", 
                "description": "Fun, engaging design for community updates",
                "theme": "fun",
                "best_for": ["Event recaps", "Community highlights", "User stories"],
                "colors": [self.colors.FETCH_BLUE, self.colors.ACCENT_GREEN]
            },
            "data_insights": {
                "name": "Data Insights",
                "description": "Clean, data-focused design for analytics",
                "theme": "insight-driven", 
                "best_for": ["Performance reports", "Analytics reviews", "KPI updates"],
                "colors": [self.colors.LIGHT_GREY, self.colors.FETCH_BLUE]
            },
            "product_launch": {
                "name": "Product Launch",
                "description": "Bold, innovative design for product announcements",
                "theme": "innovative",
                "best_for": ["Feature launches", "Product updates", "Roadmap reviews"],
                "colors": [self.colors.WHITE, self.colors.WARM_ORANGE]
            }
        }
    
    def get_brand_guidelines(self) -> Dict[str, Any]:
        """Get Fetch Rewards brand guidelines for slides."""
        return {
            "dimensions": {
                "aspect_ratio": "16:9",
                "resolution": "1920x1080px",
                "margins": "≥0.5 inches"
            },
            "typography": {
                "headline": {
                    "font": "Montserrat Bold",
                    "size": "44-54pt",
                    "case": "Title case or ALL CAPS"
                },
                "subheading": {
                    "font": "Montserrat SemiBold", 
                    "size": "28-36pt",
                    "case": "Sentence case"
                },
                "body": {
                    "font": "Montserrat Regular",
                    "size": "18-24pt",
                    "bullets": "• style"
                },
                "captions": {
                    "font": "Montserrat Light",
                    "size": "14-16pt",
                    "style": "Italicize"
                }
            },
            "colors": {
                "primary": self.colors.FETCH_BLUE,
                "navy": self.colors.DARK_NAVY,
                "background": self.colors.LIGHT_GREY,
                "success": self.colors.ACCENT_GREEN,
                "accent": self.colors.WARM_ORANGE,
                "text": self.colors.DEEP_CHARCOAL
            },
            "best_practices": [
                "Keep ≥4.5:1 contrast ratio for accessibility",
                "Use whitespace generously - avoid clutter",
                "Maintain visual hierarchy with color blocks and font weight",
                "Choose consistent iconography (line or filled)",
                "Label all charts and interpret data clearly"
            ]
        }
    
    def is_configured(self) -> bool:
        """Check if Google Slides service is properly configured."""
        return os.path.exists(self.credentials_file)

# Global instance
google_slides_service = GoogleSlidesService()