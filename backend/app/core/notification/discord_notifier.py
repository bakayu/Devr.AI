import logging
import os
import json
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from ..events.base import BaseEvent
from ..events.enums import EventType

logger = logging.getLogger(__name__)

class DiscordNotifier:
    """Discord notification service for GitHub events"""

    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url
        logger.info("Discord notifier initialized (logging mode)")

    async def notify(self, event: BaseEvent, result: Dict[str, Any] = None):
        """Queue event information for Discord notification"""
        event_type = event.event_type.value

        if event.event_type.value.startswith("issue"):
            logger.info(f"[DISCORD NOTIFICATION] Issue event: {event_type}")
            logger.info(f"  Repository: {event.repository}")
            logger.info(f"  Issue #{event.issue_number}: {event.title}")
            logger.info(f"  URL: {event.url}")

            await self.add_notification_to_queue("issue_created", {
                "title": event.title,
                "body": event.body,
                "user": {"login": event.actor_name},
                "html_url": event.url,
                "repository": event.repository,
                "issue_number": event.issue_number
            })

        elif event.event_type.value.startswith("pr"):
            logger.info(f"[DISCORD NOTIFICATION] PR event: {event_type}")
            logger.info(f"  Repository: {event.repository}")
            logger.info(f"  PR #{event.pr_number}: {event.title}")
            logger.info(f"  URL: {event.url}")

            await self.add_notification_to_queue("pr_created", {
                "title": event.title,
                "body": event.body,
                "user": {"login": event.actor_name},
                "html_url": event.url,
                "repository": event.repository,
                "pr_number": event.pr_number
            })

        elif event.event_type.value.startswith("rag"):
            logger.info(f"[DISCORD NOTIFICATION] RAG event: {event_type}")
            logger.info(f"  Query: {event.metadata.get('query', 'No query')}")
            if result:
                logger.info(f"  Answer: {result.get('answer', 'No answer')[:100]}...")

    async def add_notification_to_queue(self, event_type: str, data: dict) -> bool:
        """Add a notification to the pending notifications file"""
        try:
            notifications_file = os.path.join(
                Path(__file__).parent.parent.parent.parent,
                "bots", "discord_bot", "pending_notifications.json"
            )

            notifications = {"pending": []}
            if os.path.exists(notifications_file):
                try:
                    with open(notifications_file, 'r') as f:
                        notifications = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in notifications file, creating new file")

            notifications["pending"].append({
                "type": event_type,
                "data": data,
                "timestamp": str(datetime.now())
            })

            with open(notifications_file, 'w') as f:
                json.dump(notifications, f, indent=4)

            logger.info(f"Added notification to queue: {event_type}")
            return True
        except Exception as e:
            logger.error(f"Error adding notification to queue: {str(e)}")
            return False
