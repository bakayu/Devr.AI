import asyncio
import logging
from typing import Dict, List, Union, Optional, Callable
from .base import BaseEvent
from .enums import EventType, PlatformType
from ..handler.handler_registry import HandlerRegistry

logger = logging.getLogger(__name__)

class EventBus:
    """Central event bus for dispatching events to registered handlers"""

    def __init__(self, handler_registry: HandlerRegistry):
        self.handler_registry = handler_registry
        self.handlers: Dict[EventType, List[Callable]] = {}
        self.global_handlers: List[Callable] = []

    def register_handler(self, event_type: Union[EventType, List[EventType]], handler_func: Callable,
                         platform: Optional[PlatformType] = None):
        """Register a handler function for a specific event type and optionally platform"""
        if isinstance(event_type, list):
            for et in event_type:
                self._add_handler(et, handler_func)
        else:
            self._add_handler(event_type, handler_func)

        logger.info(f"Handler registered for event type {event_type}")

    def _add_handler(self, event_type: EventType, handler_func: Callable):
        if event_type not in self.handlers:
            self.handlers[event_type] = []

        self.handlers[event_type].append(handler_func)

    def register_global_handler(self, handler_func: Callable):
        """Register a handler that will receive all events"""
        self.global_handlers.append(handler_func)
        logger.info(f"Global handler registered")

    async def dispatch(self, event: BaseEvent):
        """Dispatch an event to all registered handlers"""
        logger.info(f"Dispatching event {event.id} of type {event.event_type}")

        try:
            handler = self.handler_registry.get_handler(event)
            result = await handler.process(event)
            logger.info(f"Event {event.id} processed with result: {result.get('success', False)}")

            for global_handler in self.global_handlers:
                asyncio.create_task(global_handler(event))

            if event.event_type in self.handlers:
                for handler_func in self.handlers[event.event_type]:
                    asyncio.create_task(handler_func(event))

            return result
        except ValueError as e:
            logger.warning(f"No handler found for event {event.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error dispatching event {event.id}: {str(e)}")
