from typing import Dict, Type, List, Optional
from ..events.base import BaseEvent
from ..events.enums import EventType, PlatformType
from .base import BaseHandler

class HandlerRegistry:
    """Registry managing event handlers and their mappings to event types"""

    def __init__(self):
        self.handlers: Dict[str, Type[BaseHandler]] = {}
        self.instances: Dict[str, BaseHandler] = {}

    def register(self, event_types: List[EventType], handler_class: Type[BaseHandler],
                 platform: Optional[PlatformType] = None):
        """Register a handler class for specific event types and platform"""
        for event_type in event_types:
            key = f"{platform.value}:{event_type.value}" if platform else event_type.value
            self.handlers[key] = handler_class

    def get_handler(self, event: BaseEvent) -> BaseHandler:
        """Find and retrieve the appropriate handler for an event"""
        key = f"{event.platform.value}:{event.event_type.value}"
        handler_class = self.handlers.get(key)

        if not handler_class:
            key = event.event_type.value
            handler_class = self.handlers.get(key)

        if not handler_class:
            raise ValueError(f"No handler registered for event type {event.event_type} on platform {event.platform}")

        if key not in self.instances:
            self.instances[key] = handler_class()

        return self.instances[key]
