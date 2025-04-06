import logging
from .event_bus import EventBus
from .enums import EventType, PlatformType
from .discord_events import DiscordEventHandler
from ..handler.handler_registry import HandlerRegistry
from ..handler.issue_handler import IssueHandler
from ..handler.pr_handler import PRHandler

logger = logging.getLogger(__name__)

def initialize_event_system() -> EventBus:
    """Set up the event system with handlers for GitHub events"""
    logger.info("Initializing event system...")

    handler_registry = HandlerRegistry()

    # Register only issue and PR creation handlers for demo purpose.
    handler_registry.register(
        event_types=[EventType.ISSUE_CREATED],
        handler_class=IssueHandler,
        platform=PlatformType.GITHUB
    )

    handler_registry.register(
        event_types=[EventType.PR_CREATED],
        handler_class=PRHandler,
        platform=PlatformType.GITHUB
    )

    event_bus = EventBus(handler_registry)

    # Set up Discord event handler for notifications
    discord_handler = DiscordEventHandler()
    event_bus.register_global_handler(discord_handler.notify)

    logger.info("Event system initialized successfully")
    return event_bus
