from backend.bots.discord_bot import DevrAIDiscordBot
from .base import BaseEvent
import logging
import os
from typing import Dict, Any
import sys
from pathlib import Path


logger = logging.getLogger(__name__)

class DiscordEventHandler:
    """Discord event handler for sending notifications to Discord channels"""

    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url
        self.discord_bot = None
        logger.info("Discord event handler initialized")

    def _init_bot(self):
        """Initialize Discord bot if needed"""
        if not self.discord_bot:
            try:
                self.discord_bot = DevrAIDiscordBot()
                logger.info("Discord bot initialized for notifications")
            except Exception as e:
                logger.error(f"Failed to initialize Discord bot: {str(e)}")

    async def notify(self, event: BaseEvent, result: Dict[str, Any] = None):
        """Process event and send notifications to Discord"""
        event_type = event.event_type.value

        if event.event_type.value.startswith("issue"):
            logger.info(f"[DISCORD NOTIFICATION] Issue event: {event_type}")
            logger.info(f"  Repository: {event.repository}")
            logger.info(f"  Issue #{event.issue_number}: {event.title}")
            logger.info(f"  URL: {event.url}")

            message = self._format_issue_message(event)
            await self._send_discord_message(message)

        elif event.event_type.value.startswith("pr"):
            logger.info(f"[DISCORD NOTIFICATION] PR event: {event_type}")
            logger.info(f"  Repository: {event.repository}")
            logger.info(f"  PR #{event.pr_number}: {event.title}")
            logger.info(f"  URL: {event.url}")

            message = self._format_pr_message(event)
            await self._send_discord_message(message)

    def _format_issue_message(self, event: BaseEvent) -> str:
        """Format an issue event message for Discord"""
        return (
            f"**New Issue Created**\n"
            f"Repository: {event.repository}\n"
            f"Issue #{event.issue_number}: {event.title}\n"
            f"Created by: {event.actor_name}\n"
            f"URL: {event.url}"
        )

    def _format_pr_message(self, event: BaseEvent) -> str:
        """Format a PR event message for Discord"""
        return (
            f"**New Pull Request Created**\n"
            f"Repository: {event.repository}\n"
            f"PR #{event.pr_number}: {event.title}\n"
            f"Created by: {event.actor_name}\n"
            f"URL: {event.url}"
        )

    async def _send_discord_message(self, message: str):
        """Send a message to Discord"""
        # FIXME: For now just log the message. In the future, this should send to Discord.
        logger.info(f"Would send to Discord: {message}")
