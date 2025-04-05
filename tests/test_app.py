from backend.app.api.github import router as github_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

app = FastAPI(
    title="Devr.AI Test",
    description="Test version of API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(github_router)
