from backend.bots.github_bot import GitHubBot
from .base import BaseHandler
from ..events.enums import EventType
from ..events.base import BaseEvent
import logging
from typing import Dict, Any, List
import sys
from pathlib import Path


logger = logging.getLogger(__name__)

class PRHandler(BaseHandler):
    """Handler for GitHub PR events"""

    def __init__(self):
        super().__init__()
        self.github_bot = GitHubBot()

    async def handle(self, event: BaseEvent) -> Dict[str, Any]:
        logger.info(f"Handling GitHub PR event: {event.event_type}")

        if event.event_type == EventType.PR_CREATED:
            return await self._handle_pr_created(event)
        else:
            logger.warning(f"Unsupported PR event type: {event.event_type}")
            return {"success": False, "reason": "Unsupported event type"}

    async def _handle_pr_created(self, event: BaseEvent) -> Dict[str, Any]:
        """Process new pull request and add welcome comment"""
        try:
            repository = event.repository
            pr_number = event.pr_number
            pr_title = event.title
            pr_url = event.url

            logger.info(f"New PR created: {repository}#{pr_number} - {pr_title}")

            comment = (
                f"Thank you @{event.actor_name} for submitting this pull request!\n"
                f"The team has been notified and will review it soon."
            )

            comment_added = await self.github_bot.add_pr_comment(
                repository, pr_number, comment
            )

            if comment_added:
                logger.info(f"Added thank you comment to PR {repository}#{pr_number}")
            else:
                logger.warning(f"Failed to add comment to PR {repository}#{pr_number}")

            return {
                "success": True,
                "action": "pr_processed",
                "comment_added": comment_added,
                "pr": {
                    "repository": repository,
                    "number": pr_number,
                    "title": pr_title,
                    "url": pr_url
                }
            }
        except Exception as e:
            logger.error(f"Error handling PR created event: {str(e)}")
            return {"success": False, "error": str(e)}
