import os
import logging
from github import Github, GithubException, Auth
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GitHubBot:
    """GitHub bot implementation for Devr.AI"""

    def __init__(self):
        """Initialize the GitHub bot"""
        self.app_id = os.getenv("GITHUB_APP_ID")
        self.private_key_path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
        self.installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize GitHub API client"""
        try:
            if self.app_id and self.private_key_path and self.installation_id:
                private_key_path = os.path.abspath(self.private_key_path)
                logger.info(f"Loading private key from: {private_key_path}")

                if not os.path.exists(private_key_path):
                    logger.error(f"Private key file not found at: {private_key_path}")
                    raise FileNotFoundError(f"Private key file not found at: {private_key_path}")

                with open(private_key_path, 'r') as key_file:
                    private_key = key_file.read()

                from github import GithubIntegration
                self.integration = GithubIntegration(self.app_id, private_key)

                access_token = self.integration.get_access_token(self.installation_id)
                self.client = Github(auth=Auth.Token(access_token.token))

                logger.info(f"GitHub bot initialized using App installation {self.installation_id}")
            else:
                logger.error("GitHub App credentials not provided")
                raise ValueError("GitHub App credentials not provided")
        except Exception as e:
            logger.error(f"Error initializing GitHub bot: {str(e)}")
            raise

    def _get_repository(self, repo_name):
        """Get a GitHub repository"""
        try:
            return self.client.get_repo(repo_name)
        except GithubException as e:
            logger.error(f"Error getting repository {repo_name}: {str(e)}")
            return None

    async def add_issue_comment(self, repo_name, issue_number, comment):
        """Add a comment to a GitHub issue"""
        try:
            repo = self._get_repository(repo_name)
            if not repo:
                logger.error(f"Repository not found: {repo_name}")
                return False

            issue = repo.get_issue(issue_number)
            issue.create_comment(comment)

            logger.info(f"Added comment to issue {repo_name}#{issue_number}")
            return True
        except Exception as e:
            logger.error(f"Error adding comment to issue {repo_name}#{issue_number}: {str(e)}")
            return False

    async def add_pr_comment(self, repo_name, pr_number, comment):
        """Add a comment to a GitHub pull request"""
        try:
            repo = self._get_repository(repo_name)
            if not repo:
                logger.error(f"Repository not found: {repo_name}")
                return False

            pr = repo.get_pull(pr_number)
            pr.create_issue_comment(comment)

            logger.info(f"Added comment to PR {repo_name}#{pr_number}")
            return True
        except Exception as e:
            logger.error(f"Error adding comment to PR {repo_name}#{pr_number}: {str(e)}")
            return False

    async def add_pr_review(self, repo_name, pr_number, body, event="COMMENT"):
        """Add a review to a pull request"""
        try:
            repo = self._get_repository(repo_name)
            if not repo:
                logger.error(f"Repository not found: {repo_name}")
                return False

            pr = repo.get_pull(pr_number)
            pr.create_review(body=body, event=event)

            logger.info(f"Added review to PR {repo_name}#{pr_number} with event {event}")
            return True
        except Exception as e:
            logger.error(f"Error adding review to PR {repo_name}#{pr_number}: {str(e)}")
            return False
