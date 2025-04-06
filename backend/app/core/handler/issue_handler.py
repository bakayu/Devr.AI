from backend.bots.github_bot import GitHubBot
from .base import BaseHandler
from ..events.enums import EventType
from ..events.base import BaseEvent
import logging
from typing import Dict, Any, List
import sys
from pathlib import Path


logger = logging.getLogger(__name__)

class IssueHandler(BaseHandler):
    """Handler for GitHub issue created events"""

    def __init__(self):
        super().__init__()
        self.github_bot = GitHubBot()

    async def handle(self, event: BaseEvent) -> Dict[str, Any]:
        logger.info(f"Handling GitHub issue event: {event.event_type}")

        if event.event_type == EventType.ISSUE_CREATED:
            return await self._handle_issue_created(event)
        else:
            logger.warning(f"Unsupported issue event type: {event.event_type}")
            return {"success": False, "reason": "Unsupported event type"}

    async def _handle_issue_created(self, event: BaseEvent) -> Dict[str, Any]:
        """Process new issue creation and add welcome comment"""
        try:
            repository = event.repository
            issue_number = event.issue_number
            issue_title = event.title
            issue_url = event.url

            logger.info(f"New issue created: {repository}#{issue_number} - {issue_title}")

            # Add a thank you comment
            comment = (
                f"Thank you @{event.actor_name} for raising this issue!\n"
                f"The team has been notified and will follow up soon."
            )

            comment_added = await self.github_bot.add_issue_comment(
                repository, issue_number, comment
            )

            if comment_added:
                logger.info(f"Added thank you comment to issue {repository}#{issue_number}")
            else:
                logger.warning(f"Failed to add comment to issue {repository}#{issue_number}")

            return {
                "success": True,
                "action": "issue_processed",
                "comment_added": comment_added,
                "issue": {
                    "repository": repository,
                    "number": issue_number,
                    "title": issue_title,
                    "url": issue_url
                }
            }
        except Exception as e:
            logger.error(f"Error handling issue created event: {str(e)}")
            return {"success": False, "error": str(e)}

    def _determine_labels(self, event: BaseEvent) -> List[str]:
        """Analyze issue content to suggest appropriate labels"""
        title_lower = event.title.lower()
        body_lower = event.body.lower() if event.body else ""

        labels = []

        # Check for bug reports
        if any(kw in title_lower or kw in body_lower for kw in
               ["bug", "error", "issue", "problem", "fail", "crash"]):
            labels.append("bug")

        # Check for feature requests
        if any(kw in title_lower or kw in body_lower for kw in
               ["feature", "request", "enhancement", "add", "new"]):
            labels.append("enhancement")

        # Check for questions
        if any(kw in title_lower or "?" in title_lower or kw in body_lower for kw in
               ["how", "what", "why", "question", "help"]):
            labels.append("question")

        # Check for documentation issues
        if any(kw in title_lower or kw in body_lower for kw in
               ["doc", "documentation", "readme", "guide", "example"]):
            labels.append("documentation")

        return labels

    def _is_first_time_contributor(self, event: BaseEvent) -> bool:
        """Check if user is a first-time contributor to the repository"""
        # TODO: This is a placeholder for future implementation
        return True
