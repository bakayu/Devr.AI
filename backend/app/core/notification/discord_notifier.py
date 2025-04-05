import logging
from typing import Dict, Any
from ..events.base import BaseEvent

logger = logging.getLogger(__name__)

class DiscordNotifier:
    """Discord notification service for GitHub events"""

    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url
        logger.info("Discord notifier initialized (logging mode)")

    async def notify(self, event: BaseEvent, result: Dict[str, Any] = None):
        """Log event information for future Discord integration"""
        event_type = event.event_type.value

        if event.event_type.value.startswith("issue"):
            logger.info(f"[DISCORD NOTIFICATION] Issue event: {event_type}")
            logger.info(f"  Repository: {event.repository}")
            logger.info(f"  Issue #{event.issue_number}: {event.title}")
            logger.info(f"  URL: {event.url}")

        elif event.event_type.value.startswith("pr"):
            logger.info(f"[DISCORD NOTIFICATION] PR event: {event_type}")
            logger.info(f"  Repository: {event.repository}")
            logger.info(f"  PR #{event.pr_number}: {event.title}")
            logger.info(f"  URL: {event.url}")
