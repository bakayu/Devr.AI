import pytest
import asyncio
import uuid
from backend.app.core.events.github_event import GitHubEvent
from backend.app.core.events.enums import EventType, PlatformType

class TestGitHubEvents:
    """Test class for GitHub event handling"""

    @pytest.mark.asyncio
    async def test_issue_created_event(self, event_bus, sample_payloads):
        """Test that issue created events are properly handled"""
        payload = sample_payloads["issue_created"]
        assert payload, "Sample payload should be loaded"

        test_event = GitHubEvent(
            id=str(uuid.uuid4()),
            platform=PlatformType.GITHUB,
            event_type=EventType.ISSUE_CREATED,
            actor_id=str(payload.get("sender", {}).get("id", "12345")),
            actor_name=payload.get("sender", {}).get("login", "test-user"),
            repository=payload.get("repository", {}).get("full_name", "sample/repo"),
            issue_number=payload.get("issue", {}).get("number", 1),
            title=payload.get("issue", {}).get("title", "Sample Issue"),
            body=payload.get("issue", {}).get("body", "Sample body"),
            url=payload.get("issue", {}).get("html_url", "https://github.com/sample/repo/issues/1"),
            raw_data=payload
        )

        result = await event_bus.dispatch(test_event)

        assert result is not None
        assert result.get("success") is True
        assert result.get("action") == "issue_processed"
        assert "issue" in result

    @pytest.mark.asyncio
    async def test_pr_created_event(self, event_bus, sample_payloads):
        """Test that PR created events are properly handled"""
        payload = sample_payloads["pr_created"]
        assert payload, "Sample payload should be loaded"

        test_event = GitHubEvent(
            id=str(uuid.uuid4()),
            platform=PlatformType.GITHUB,
            event_type=EventType.PR_CREATED,
            actor_id=str(payload.get("sender", {}).get("id", "12345")),
            actor_name=payload.get("sender", {}).get("login", "test-user"),
            repository=payload.get("repository", {}).get("full_name", "sample/repo"),
            pr_number=payload.get("pull_request", {}).get("number", 2),
            title=payload.get("pull_request", {}).get("title", "Sample PR"),
            body=payload.get("pull_request", {}).get("body", "Sample body"),
            url=payload.get("pull_request", {}).get("html_url", "https://github.com/sample/repo/pull/2"),
            raw_data=payload
        )

        result = await event_bus.dispatch(test_event)

        assert result is not None
        assert result.get("success") is True
        assert result.get("action") == "pr_processed"
        assert "pr" in result
