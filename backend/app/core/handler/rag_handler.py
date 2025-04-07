import logging
from typing import Dict, Any
from ..events.base import BaseEvent
from ..events.enums import EventType
from .base import BaseHandler
from ...services.rag.service import RAGService

logger = logging.getLogger(__name__)

class RAGHandler(BaseHandler):
    """Handler for RAG query events"""

    def __init__(self):
        super().__init__()
        self.rag_service = RAGService()

    async def handle(self, event: BaseEvent) -> Dict[str, Any]:
        logger.info(f"Handling RAG event: {event.event_type}")

        if event.event_type == EventType.RAG_QUERY:
            return await self._handle_rag_query(event)
        else:
            logger.warning(f"Unsupported RAG event type: {event.event_type}")
            return {"success": False, "reason": "Unsupported event type"}

    async def _handle_rag_query(self, event: BaseEvent) -> Dict[str, Any]:
        """Handle RAG query event"""
        try:
            query = event.metadata.get("query", "")
            if not query:
                return {
                    "success": False,
                    "reason": "No query provided",
                    "answer": "I couldn't process your query because it was empty."
                }

            result = await self.rag_service.query(query)

            return {
                "success": result.get("success", False),
                "action": "rag_query_processed",
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "query": query
            }
        except Exception as e:
            logger.error(f"Error handling RAG query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "answer": "I encountered an error while processing your query."
            }
