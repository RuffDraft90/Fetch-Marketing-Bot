"""
Monday.com Service
=================
Service for creating and managing Monday.com boards and items with unified Project 1 + Project 2 workflow
"""

import os
import logging
import json
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MondayService:
    """Service for Monday.com integration with unified campaign workflow."""
    
    def __init__(self):
        """Initialize Monday.com service."""
        self.api_token = os.getenv('MONDAY_API_TOKEN')
        self.base_url = "https://api.monday.com/v2"
        
    async def create_physical_event_campaign(self, name: str, goal: str, target: str) -> Dict[str, Any]:
        """Create physical event campaign with dual parent tickets (Jheryl's Logic)"""
        logger.info(f"Creating physical event campaign: {name}")
        
        # Create event planning parent ticket
        event_ticket = {
            "id": f"event_{hash(name) % 10000}",
            "name": f"Event Planning: {name}",
            "assignees": ["kate@fetchrewards.com", "karen@fetchrewards.com"],
            "tasks": [
                "Venue booking and logistics", "Event timeline and agenda",
                "Speaker/presenter coordination", "Materials and setup planning", 
                "Registration process", "On-site execution", "Post-event follow-up"
            ]
        }
        
        # Create email campaign parent ticket  
        email_ticket = {
            "id": f"email_{hash(name) % 10000}",
            "name": f"Email Campaign: {name}",
            "assignees": ["jheryl@fetchrewards.com"],
            "tasks": ["Email strategy", "Content creation", "Audience segmentation", "Send automation", "Performance tracking"]
        }
        
        return {
            "status": "created", "campaign_type": "physical_event",
            "event_ticket": event_ticket, "email_ticket": email_ticket,
            "event_board_url": f"https://fetchrewards.monday.com/boards/123456",
            "email_board_url": f"https://fetchrewards.monday.com/boards/789012"
        }
    
    async def create_email_only_campaign(self, name: str, goal: str, target: str) -> Dict[str, Any]:
        """Create email-only campaign with single parent ticket (Jheryl's Logic)"""
        logger.info(f"Creating email-only campaign: {name}")
        
        email_ticket = {
            "id": f"email_only_{hash(name) % 10000}",
            "name": f"Email Campaign: {name}",
            "assignees": ["jheryl@fetchrewards.com"],
            "tasks": ["Campaign strategy", "Audience segmentation", "Content creation", "A/B testing", "Send automation", "Performance analysis"]
        }
        
        return {
            "status": "created", "campaign_type": "email_only",
            "email_ticket": email_ticket,
            "board_url": f"https://fetchrewards.monday.com/boards/789012"
        }

    async def create_unified_campaign_workflow(self, campaign_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create unified campaign workflow with parent task and subtasks.
        
        Args:
            campaign_data: Campaign details including event_name, dates, location, deliverables, requestor
            
        Returns:
            Dict with complete workflow info or None if failed
        """
        try:
            campaign_name = campaign_data.get('event_name', 'Untitled Campaign')
            event_dates = campaign_data.get('event_dates', '')
            location = campaign_data.get('location', '')
            deliverables = campaign_data.get('deliverables', '')
            requestor = campaign_data.get('requestor', 'Unknown')
            
            logger.info(f"Creating unified Monday.com workflow for campaign: {campaign_name}")
            
            # Generate parent task
            parent_task = await self._create_parent_task(campaign_name, event_dates, location, requestor)
            
            # Generate subtasks based on deliverables
            subtasks = await self._create_campaign_subtasks(parent_task['task_id'], deliverables, event_dates)
            
            # Mock board creation
            board_id = f"board_{hash(campaign_name) % 100000}"
            
            return {
                'board_id': board_id,
                'board_url': f"https://monday.com/boards/{board_id}",
                'parent_task': parent_task,
                'subtasks': subtasks,
                'total_tasks': len(subtasks) + 1,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating Monday.com workflow: {e}")
            return None
    
    async def get_active_campaigns(self) -> List[Dict[str, Any]]:
        """Get active campaigns from Monday.com."""
        try:
            # In a real implementation, this would make API calls to Monday.com
            # For now, return mock data that would come from the actual API
            logger.info("Fetching active campaigns from Monday.com")
            
            # This would be replaced with actual Monday.com API calls
            mock_campaigns = [
                {
                    'id': '12345',
                    'name': 'Summer Product Launch',
                    'status': 'working on it',
                    'progress': 75,
                    'due_date': '2025-07-25',
                    'assignees': ['Kelly Redding', 'Karen Lowry'],
                    'url': 'https://monday.com/boards/12345'
                },
                {
                    'id': '12346', 
                    'name': 'Q3 Marketing Campaign',
                    'status': 'stuck',
                    'progress': 40,
                    'due_date': '2025-08-15',
                    'assignees': ['Kate Jeffries'],
                    'url': 'https://monday.com/boards/12346'
                }
            ]
            
            return mock_campaigns
            
        except Exception as e:
            logger.error(f"Error fetching campaigns from Monday.com: {e}")
            return []
    
    async def get_campaign_details(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific campaign."""
        try:
            logger.info(f"Fetching campaign details for ID: {campaign_id}")
            
            # In a real implementation, this would query Monday.com API for specific campaign
            campaigns = await self.get_active_campaigns()
            for campaign in campaigns:
                if campaign['id'] == campaign_id:
                    return campaign
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching campaign details: {e}")
            return None
    
    
    async def _create_parent_task(self, campaign_name: str, event_dates: str, location: str, requestor: str) -> Dict[str, Any]:
        """Create the parent campaign task."""
        task_id = f"task_{hash(campaign_name) % 100000}"
        
        return {
            "task_id": task_id,
            "name": f"{campaign_name} - {event_dates}",
            "status": "New Request",
            "assignee": requestor,
            "location": location,
            "created_date": datetime.now().isoformat(),
            "type": "parent_task"
        }
    
    async def _create_campaign_subtasks(self, parent_task_id: str, deliverables: str, event_dates: str) -> List[Dict[str, Any]]:
        """Create subtasks based on deliverables and standard workflow."""
        subtasks = []
        
        # Parse event date to calculate due dates
        try:
            if event_dates:
                # Simplified date parsing - in real implementation, parse the actual date
                event_date = datetime.now() + timedelta(days=30)  # Mock: assume event is in 30 days
            else:
                event_date = datetime.now() + timedelta(days=30)
        except:
            event_date = datetime.now() + timedelta(days=30)
        
        # Standard subtasks for all campaigns
        standard_subtasks = [
            {
                "name": "Deliverable Design",
                "assignee": "Kelly Redding",
                "due_date": event_date - timedelta(days=14),  # 2 weeks before event
                "estimated_duration": "2-3 business days",
                "dependencies": []
            },
            {
                "name": "Creative Review", 
                "assignee": "Kelly Redding",
                "due_date": event_date - timedelta(days=12),  # After design completion
                "estimated_duration": "1-2 business days",
                "dependencies": ["Deliverable Design"]
            },
            {
                "name": "EDEN Review",
                "assignee": "Karen or Kate",
                "due_date": event_date - timedelta(days=10),  # After creative review
                "estimated_duration": "1-2 business days", 
                "dependencies": ["Creative Review"]
            }
        ]
        
        # Add deliverable-specific subtasks if specified
        if deliverables and deliverables.strip():
            deliverable_items = [item.strip() for item in deliverables.split('\n') if item.strip()]
            for item in deliverable_items:
                standard_subtasks.append({
                    "name": f"Custom: {item}",
                    "assignee": "To Be Assigned",
                    "due_date": event_date - timedelta(days=7),
                    "estimated_duration": "TBD",
                    "dependencies": ["EDEN Review"]
                })
        
        # Generate subtask objects
        for i, subtask_data in enumerate(standard_subtasks):
            subtask_id = f"subtask_{hash(parent_task_id + str(i)) % 100000}"
            
            subtask = {
                "task_id": subtask_id,
                "parent_id": parent_task_id,
                "name": subtask_data["name"],
                "assignee": subtask_data["assignee"],
                "due_date": subtask_data["due_date"].isoformat(),
                "estimated_duration": subtask_data["estimated_duration"],
                "dependencies": subtask_data["dependencies"],
                "status": "Not Started",
                "type": "subtask",
                "calendar_reminder": True  # Flag for calendar integration
            }
            
            subtasks.append(subtask)
        
        return subtasks
    
    async def get_active_campaigns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get active campaigns for dashboard view."""
        try:
            # Mock active campaigns - replace with actual Monday.com API call
            mock_campaigns = [
                {
                    "campaign_name": "Receipt Heroes Q3 Launch",
                    "status": "In Progress",
                    "next_due_date": (datetime.now() + timedelta(days=3)).isoformat(),
                    "next_task": "Creative Review",
                    "assignee": "Kelly Redding",
                    "board_url": "https://fetchrewards.monday.com/boards/12345"
                },
                {
                    "campaign_name": "Scan & Earn 2.0 Promo",
                    "status": "Design Phase", 
                    "next_due_date": (datetime.now() + timedelta(days=7)).isoformat(),
                    "next_task": "Deliverable Design",
                    "assignee": "Kelly Redding",
                    "board_url": "https://fetchrewards.monday.com/boards/12346"
                },
                {
                    "campaign_name": "Community Meetup - Chicago",
                    "status": "EDEN Review",
                    "next_due_date": (datetime.now() + timedelta(days=1)).isoformat(),
                    "next_task": "EDEN Review",
                    "assignee": "Karen or Kate", 
                    "board_url": "https://fetchrewards.monday.com/boards/12347"
                }
            ]
            
            return mock_campaigns[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get active campaigns: {e}")
            return []
    
    async def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status in Monday.com."""
        try:
            logger.info(f"Updating task {task_id} status to: {status}")
            # Mock implementation - replace with actual Monday.com API call
            return True
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
            return False
    
    async def create_campaign_board(self, campaign_name: str, campaign_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Legacy method - redirect to unified workflow."""
        return await self.create_unified_campaign_workflow({
            'event_name': campaign_name,
            **campaign_data
        })
    
    async def create_campaign_items(self, board_id: str, items: list) -> bool:
        """Legacy method - maintained for compatibility."""
        try:
            logger.info(f"Creating {len(items)} items in Monday.com board {board_id}")
            
            # Mock implementation - replace with actual Monday.com API calls
            for item in items:
                logger.info(f"Created item: {item.get('name', 'Unnamed item')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Monday.com items: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Check if Monday.com service is properly configured."""
        return bool(self.api_token)

# Global instance
monday_service = MondayService()