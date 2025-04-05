import pytest
import os
import uuid
from dotenv import load_dotenv
from backend.app.services.github_service import GitHubService

# Load environment variables
load_dotenv()

@pytest.fixture
def github_service():
    """Create a GitHub service for testing"""
    return GitHubService()

@pytest.fixture
def test_repo_name():
    """Get a test repository name from environment or use a default"""
    return os.getenv("TEST_GITHUB_REPO", "octocat/Hello-World")

class TestGitHubAPI:
    """Test GitHub API functionality"""

    @pytest.mark.asyncio
    async def test_github_service_initialization(self, github_service):
        """Test that the GitHub service initializes correctly"""
        assert github_service is not None
        assert hasattr(github_service, 'client')

        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            assert github_service.token == github_token

    @pytest.mark.asyncio
    async def test_get_repository(self, github_service, test_repo_name):
        """Test fetching a repository"""
        repo = github_service.get_repository(test_repo_name)

        assert repo is not None
        assert repo.full_name == test_repo_name

    @pytest.mark.asyncio
    async def test_issue_operations(self, github_service, test_repo_name):
        """Test issue-related operations"""
        if not github_service.token:
            pytest.skip("GitHub token not provided, skipping issue operations test")

        repo = github_service.get_repository(test_repo_name)
        issues = list(repo.get_issues()[:1])

        if not issues:
            pytest.skip(f"No issues found in {test_repo_name}")

        test_issue = issues[0]
        issue_number = test_issue.number

        issue = await github_service.get_issue(test_repo_name, issue_number)
        assert issue is not None
        assert issue.number == issue_number

    @pytest.mark.asyncio
    async def test_api_rate_limit(self, github_service):
        """Test that rate limit information can be fetched"""
        try:
            github_service._log_rate_limit()
            assert True
        except Exception as e:
            pytest.fail(f"Rate limit check failed: {str(e)}")

    @pytest.mark.parametrize("repo_name", [
        "this-repo-definitely-does-not-exist/seriously",
        "invalid/repo/format",
        ""
    ])
    @pytest.mark.asyncio
    async def test_invalid_repository(self, github_service, repo_name):
        """Test behavior with invalid repository names"""
        repo = github_service.get_repository(repo_name)
        assert repo is None
