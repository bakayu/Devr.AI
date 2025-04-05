import os
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from github import Github, GithubException, RateLimitExceededException
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GitHubService:
    """Service for interacting with GitHub API"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")

        if not self.token:
            logger.warning("GitHub token missing. API operations will be limited.")
            self.client = Github()
        else:
            self.client = Github(self.token)

        logger.info("GitHub service initialized")

        # Log current rate limits
        self._log_rate_limit()

    def _log_rate_limit(self):
        """Log current GitHub API rate limit information"""
        try:
            rate_limit = self.client.get_rate_limit()
            core = rate_limit.core
            logger.info(f"GitHub API Rate Limit: {core.remaining}/{core.limit} (Resets at {core.reset})")
        except Exception as e:
            logger.warning(f"Could not check rate limit: {str(e)}")

    def _handle_rate_limit(self, e: RateLimitExceededException) -> bool:
        """Handle rate limit by waiting if reset time is reasonable"""
        reset_timestamp = e.get_reset_time()
        if not reset_timestamp:
            return False

        wait_time = int(reset_timestamp.timestamp() - time.time()) + 5
        if wait_time <= 300:
            logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds for reset...")
            time.sleep(wait_time)
            return True
        else:
            logger.error(f"Rate limit exceeded. Reset time too long: {wait_time} seconds")
            return False

    def get_repository(self, repo_name: str) -> Optional[Repository]:
        """Fetch a GitHub repository by name (owner/repo format)"""
        try:
            return self.client.get_repo(repo_name)
        except RateLimitExceededException as e:
            if self._handle_rate_limit(e):
                return self.get_repository(repo_name)
            return None
        except GithubException as e:
            logger.error(f"Error fetching repository {repo_name}: {str(e)}")
            return None

    async def get_issue(self, repo_name: str, issue_number: int) -> Optional[Issue]:
        """Fetch a GitHub issue by repository and issue number"""
        try:
            repo = self.get_repository(repo_name)
            if not repo:
                return None
            return repo.get_issue(issue_number)
        except RateLimitExceededException as e:
            if self._handle_rate_limit(e):
                return await self.get_issue(repo_name, issue_number)
            return None
        except GithubException as e:
            logger.error(f"Error fetching issue {repo_name}#{issue_number}: {str(e)}")
            return None

    async def add_issue_labels(self, repo_name: str, issue_number: int, labels: List[str]) -> bool:
        """Add labels to a GitHub issue"""
        try:
            issue = await self.get_issue(repo_name, issue_number)
            if not issue:
                return False

            issue.add_to_labels(*labels)
            logger.info(f"Added labels {labels} to {repo_name}#{issue_number}")
            return True
        except GithubException as e:
            logger.error(f"Error adding labels to issue {repo_name}#{issue_number}: {str(e)}")
            return False

    async def add_issue_comment(self, repo_name: str, issue_number: int, comment: str) -> bool:
        """Add a comment to a GitHub issue"""
        try:
            issue = await self.get_issue(repo_name, issue_number)
            if not issue:
                return False

            issue.create_comment(comment)
            logger.info(f"Added comment to {repo_name}#{issue_number}")
            return True
        except RateLimitExceededException as e:
            if self._handle_rate_limit(e):
                return await self.add_issue_comment(repo_name, issue_number, comment)
            return False
        except GithubException as e:
            logger.error(f"Error adding comment to issue {repo_name}#{issue_number}: {str(e)}")
            return False

    async def get_pull_request(self, repo_name: str, pr_number: int) -> Optional[PullRequest]:
        """Fetch a pull request by repository and PR number"""
        try:
            repo = self.get_repository(repo_name)
            if not repo:
                return None
            return repo.get_pull(pr_number)
        except RateLimitExceededException as e:
            if self._handle_rate_limit(e):
                return await self.get_pull_request(repo_name, pr_number)
            return None
        except GithubException as e:
            logger.error(f"Error fetching PR {repo_name}#{pr_number}: {str(e)}")
            return None

    async def add_pr_comment(self, repo_name: str, pr_number: int, comment: str) -> bool:
        """Add a comment to a GitHub pull request"""
        try:
            pr = await self.get_pull_request(repo_name, pr_number)
            if not pr:
                return False

            pr.create_issue_comment(comment)
            logger.info(f"Added comment to PR {repo_name}#{pr_number}")
            return True
        except RateLimitExceededException as e:
            if self._handle_rate_limit(e):
                return await self.add_pr_comment(repo_name, pr_number, comment)
            return False
        except GithubException as e:
            logger.error(f"Error adding comment to PR {repo_name}#{pr_number}: {str(e)}")
            return False

    async def add_pr_review(self, repo_name: str, pr_number: int,
                            body: str, event: str = "COMMENT") -> bool:
        """Add a review to a pull request (APPROVE, REQUEST_CHANGES, or COMMENT)"""
        try:
            pr = await self.get_pull_request(repo_name, pr_number)
            if not pr:
                return False

            pr.create_review(body=body, event=event)
            logger.info(f"Added review to PR {repo_name}#{pr_number}")
            return True
        except GithubException as e:
            logger.error(f"Error adding review to PR {repo_name}#{pr_number}: {str(e)}")
            return False
