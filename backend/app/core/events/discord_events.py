import logging
import os
import json
from datetime import datetime
from pathlib import Path
from .base import BaseEvent
from .enums import EventType

# !!TODO: We are using config.json and pending_notification.json files to store config data and the queue system.
# This is for demo purposes only, in actual implementation there will be a more solid queue system and config data to be stored in Supabase.

logger = logging.getLogger(__name__)

class DiscordEventHandler:
    def __init__(self):
        self.config = None
        logger.info("Discord event handler initialized")
        self._load_config()

    def _load_config(self):
        """Load the Discord bot configuration directly from file"""
        try:
            config_file = os.path.join(
                Path(__file__).parent.parent.parent.parent,
                "bots", "discord_bot", "config.json"
            )
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Discord event handler loaded config: {self.config}")
            else:
                logger.warning(f"Discord bot config file not found at {config_file}")
                self.config = {"notification_channel_id": None, "webhook_url": None, "maintainers": []}
        except Exception as e:
            logger.error(f"Error loading Discord bot config: {str(e)}")
            self.config = {"notification_channel_id": None, "webhook_url": None, "maintainers": []}

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

    async def notify(self, event: BaseEvent):
        """Process an event notification by adding it to the queue for the bot to process"""
        self._load_config()

        try:
            if event.event_type == EventType.ISSUE_CREATED:
                await self.add_notification_to_queue("issue_created", {
                    "title": event.title,
                    "body": event.body,
                    "user": {"login": event.actor_name},
                    "html_url": event.url,
                    "repository": event.repository,
                    "issue_number": event.issue_number
                })
                logger.info(f"Queued issue notification for issue #{event.issue_number}")
                return True

            elif event.event_type == EventType.PR_CREATED:
                await self.add_notification_to_queue("pr_created", {
                    "title": event.title,
                    "body": event.body,
                    "user": {"login": event.actor_name},
                    "html_url": event.url,
                    "repository": event.repository,
                    "pr_number": event.pr_number
                })
                logger.info(f"Queued PR notification for PR #{event.pr_number}")
                return True

            else:
                logger.warning(f"Unknown event type for Discord notification: {event.event_type}")
                return False

        except Exception as e:
            logger.error(f"Error queueing notification: {str(e)}")
            return False
