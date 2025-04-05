from backend.app.utils.helpers import create_sample_payloads, load_sample_payload
from backend.app.core.events.init_events import initialize_event_system
from backend.app.core.events.event_bus import EventBus
import os
import sys
import pytest
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

@pytest.fixture(scope="session")
def event_bus():
    """Fixture that provides an initialized event bus"""
    return initialize_event_system()

@pytest.fixture(scope="session")
def sample_payloads():
    """Fixture that creates and returns sample payloads"""
    create_sample_payloads()
    return {
        "issue_created": load_sample_payload("issue_created"),
        "pr_created": load_sample_payload("pr_created")
    }
