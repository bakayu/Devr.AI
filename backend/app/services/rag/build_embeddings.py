#!/usr/bin/env python3
import os
import sys
import logging
import asyncio
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

project_root = str(Path(__file__).parent.parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app.services.vector_db.service import VectorDBService, EmbeddingItem  # noqa
from langchain_community.embeddings import FastEmbedEmbeddings  # noqa
from langchain_text_splitters import MarkdownTextSplitter  # noqa

# TODO: Right now we are using *.md files stored in a local `docs` directory to create embeddings. In actual implementation we will have a more solid system to generate embeddings.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

COLLECTION_NAME = "devr-ai-docs"
DOCS_PATH = Path(project_root) / "docs"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

async def find_markdown_files(base_path: Path = DOCS_PATH) -> List[Path]:
    """Find all markdown files in the given directory and subdirectories"""
    if not base_path.exists():
        logger.error(f"Docs path {base_path} does not exist")
        return []

    md_files = list(base_path.glob("**/*.md"))
    logger.info(f"Found {len(md_files)} markdown files in {base_path}")
    return md_files

async def process_markdown_file(file_path: Path, embeddings_model) -> List[EmbeddingItem]:
    """Process a markdown file and generate embedding items"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        relative_path = file_path.relative_to(Path(project_root))

        splitter = MarkdownTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        chunks = splitter.split_text(content)

        metadata = {
            "source": str(relative_path),
            "filename": file_path.name,
            "filetype": "markdown"
        }

        embedding_items = []
        for i, chunk in enumerate(chunks):
            embedding = embeddings_model.embed_query(chunk)

            item_id = str(uuid.uuid4())
            item = EmbeddingItem(
                id=item_id,
                collection=COLLECTION_NAME,
                content=chunk,
                metadata={
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                },
                embedding=embedding
            )
            embedding_items.append(item)

        logger.info(f"Processed {file_path.name} into {len(chunks)} chunks")
        return embedding_items

    except Exception as e:
        logger.error(f"Error processing markdown file {file_path}: {str(e)}")
        return []

async def build_embeddings() -> bool:
    """Build embeddings for all markdown files and store them in the vector database"""
    try:
        vector_db = VectorDBService()

        connection_ok = await vector_db.check_connection()
        if not connection_ok:
            logger.error("Failed to connect to vector database")
            return False

        embeddings_model = FastEmbedEmbeddings()

        md_files = await find_markdown_files()
        if not md_files:
            logger.warning("No markdown files found")
            return False

        total_chunks = 0
        for file_path in md_files:
            logger.info(f"Processing {file_path.name}...")
            embedding_items = await process_markdown_file(file_path, embeddings_model)

            if embedding_items:
                for i in range(0, len(embedding_items), 10):
                    batch = embedding_items[i:i+10]
                    result = await vector_db.add_items(batch)
                    if not result:
                        logger.error(f"Failed to store batch of embeddings for {file_path.name}")

                total_chunks += len(embedding_items)

        logger.info(f"Successfully processed {len(md_files)} files with {total_chunks} total chunks")
        return True

    except Exception as e:
        logger.error(f"Error building embeddings: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(build_embeddings())
