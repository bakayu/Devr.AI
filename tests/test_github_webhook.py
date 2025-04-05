from backend.app.core.events.enums import EventType, PlatformType
from tests.test_app import app
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

client = TestClient(app)

@pytest.fixture
def issue_payload():
    """Load a sample issue created payload"""
    with open("backend/tests/samples/issue_created.json", "r") as f:
        return json.load(f)

@pytest.fixture
def pr_payload():
    """Load a sample PR created payload"""
    with open("backend/tests/samples/pr_created.json", "r") as f:
        return json.load(f)

class TestGitHubWebhook:
    """Test GitHub webhook endpoint"""

    @patch("backend.app.api.github.event_bus")
    def test_issue_created_webhook(self, mock_event_bus, issue_payload):
        """Test handling of issue created webhook"""
        mock_event_bus.dispatch.return_value = {
            "success": True,
            "action": "issue_processed",
            "issue": {
                "repository": "sample/repo",
                "number": 1
            }
        }

        headers = {
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "test-delivery-id",
            "Content-Type": "application/json"
        }

        issue_payload["action"] = "opened"

        response = client.post(
            "/github/webhook",
            headers=headers,
            json=issue_payload
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

        mock_event_bus.dispatch.assert_called_once()

        call_args = mock_event_bus.dispatch.call_args[0][0]
        assert call_args.platform == PlatformType.GITHUB
        assert call_args.event_type == EventType.ISSUE_CREATED

    @patch("backend.app.api.github.event_bus")
    def test_pr_created_webhook(self, mock_event_bus, pr_payload):
        """Test handling of PR created webhook"""
        mock_event_bus.dispatch.return_value = {
            "success": True,
            "action": "pr_processed",
            "pr": {
                "repository": "sample/repo",
                "number": 2
            }
        }

        headers = {
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-id",
            "Content-Type": "application/json"
        }

        pr_payload["action"] = "opened"

        response = client.post(
            "/github/webhook",
            headers=headers,
            json=pr_payload
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

        mock_event_bus.dispatch.assert_called_once()

        call_args = mock_event_bus.dispatch.call_args[0][0]
        assert call_args.platform == PlatformType.GITHUB
        assert call_args.event_type == EventType.PR_CREATED

    def test_unsupported_event(self):
        """Test handling of unsupported event types"""
        headers = {
            "X-GitHub-Event": "star",
            "X-GitHub-Delivery": "test-delivery-id",
            "Content-Type": "application/json"
        }

        response = client.post(
            "/github/webhook",
            headers=headers,
            json={"action": "created"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

    def test_missing_header(self):
        """Test handling of requests with missing GitHub event header"""
        headers = {
            "X-GitHub-Delivery": "test-delivery-id",
            "Content-Type": "application/json"
        }

        response = client.post(
            "/github/webhook",
            headers=headers,
            json={"action": "opened"}
        )

        assert response.status_code == 400
