from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Optional
import logging
from ..events.base import BaseEvent
from ..events.enums import EventType, PlatformType

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """Base class for all event handlers"""

    def __init__(self):
        self.name = self.__class__.__name__

    async def pre_handle(self, event: BaseEvent) -> BaseEvent:
        """Prepare and validate an event before main processing"""
        logger.debug(f"Pre-handling event {event.id} with {self.name}")
        return event

    @abstractmethod
    async def handle(self, event: BaseEvent) -> Dict[str, Any]:
        """Core processing logic for an event"""
        pass

    async def post_handle(self, event: BaseEvent, result: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up and finalize processing after event handling"""
        logger.debug(f"Post-handling event {event.id} with {self.name}")
        return result

    async def process(self, event: BaseEvent) -> Dict[str, Any]:
        """Execute the complete event handling pipeline"""
        try:
            processed_event = await self.pre_handle(event)
            result = await self.handle(processed_event)
            return await self.post_handle(processed_event, result)
        except Exception as e:
            logger.error(f"Error processing event {event.id} with handler {self.name}: {str(e)}")
            return {"success": False, "error": str(e)}
