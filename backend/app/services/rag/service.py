import os
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_core.documents import Document
from langchain_community.embeddings import FastEmbedEmbeddings

from ...services.vector_db.service import VectorDBService, EmbeddingItem

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3-8b-8192")
COLLECTION_NAME = "devr-ai-docs"

logger = logging.getLogger(__name__)

class RAGService:
    """RAG service for retrieving documentation and generating answers with Groq"""

    def __init__(self, collection_name: str = COLLECTION_NAME):
        self.collection_name = collection_name
        self.vector_db_service = VectorDBService()

        if not GROQ_API_KEY:
            logger.warning("GROQ_API_KEY not set, RAG features will not work correctly")

        self.embeddings = FastEmbedEmbeddings()

        self.llm = ChatGroq(
            model_name=LLM_MODEL,
            groq_api_key=GROQ_API_KEY,
            temperature=0.3
        )
        logger.info(f"RAG service initialized with model: {LLM_MODEL}")

    async def create_embeddings_from_docs(self, docs_path: str) -> bool:
        """Create embeddings from documents in the specified directory"""
        try:
            loader = DirectoryLoader(
                docs_path,
                glob="**/*.md",
                loader_cls=TextLoader
            )
            documents = loader.load()

            if not documents:
                logger.warning(f"No documents found in {docs_path}")
                return False

            logger.info(f"Loaded {len(documents)} documents")

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100
            )
            chunks = text_splitter.split_documents(documents)

            logger.info(f"Split into {len(chunks)} chunks")

            embedding_items = []
            for chunk in chunks:
                embedding_vector = self.embeddings.embed_query(chunk.page_content)

                item = EmbeddingItem(
                    id=str(uuid.uuid4()),
                    collection=self.collection_name,
                    content=chunk.page_content,
                    metadata=chunk.metadata,
                    embedding=embedding_vector
                )
                embedding_items.append(item)

            batch_size = 20
            for i in range(0, len(embedding_items), batch_size):
                batch = embedding_items[i:i+batch_size]
                result = await self.vector_db_service.add_items(batch)
                if not result:
                    logger.error(f"Failed to add batch {i//batch_size + 1}")

            logger.info(f"Added {len(embedding_items)} embeddings to vector database")
            return True

        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            return False

    async def query(self, query_text: str, limit: int = 5) -> Dict[str, Any]:
        """Query the vector DB with RAG to get an answer"""
        try:
            query_embedding = self.embeddings.embed_query(query_text)

            results = await self.vector_db_service.search(
                query_embedding=query_embedding,
                collection=self.collection_name,
                limit=limit,
                threshold=0.5
            )

            if not results:
                return {
                    "success": False,
                    "answer": "I couldn't find any relevant information to answer your question.",
                    "sources": []
                }

            contexts = [item["content"] for item in results]
            sources = [item.get("metadata", {}).get("source", "Unknown") for item in results]

            formatted_context = "\n\n".join(contexts)

            prompt = f"""You are an AI assistant for the Devr.AI project. Use the following information to answer the question.
            If you don't know the answer based on the context, say that you don't know rather than making up an answer.
            
            CONTEXT:
            {formatted_context}
            
            QUESTION:
            {query_text}
            
            ANSWER:
            """

            response = self.llm.invoke(prompt)

            return {
                "success": True,
                "answer": response.content,
                "sources": sources
            }

        except Exception as e:
            logger.error(f"Error querying RAG system: {str(e)}")
            return {
                "success": False,
                "answer": f"An error occurred: {str(e)}",
                "sources": []
            }

    async def check_connection(self) -> bool:
        """Check connections to dependencies"""
        try:
            vector_db_ok = await self.vector_db_service.check_connection()

            groq_ok = GROQ_API_KEY is not None

            if not vector_db_ok:
                logger.error("Vector database connection failed")

            if not groq_ok:
                logger.error("Groq API key not found")

            return vector_db_ok and groq_ok

        except Exception as e:
            logger.error(f"Connection check failed: {str(e)}")
            return False
