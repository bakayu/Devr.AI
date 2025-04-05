import os
import logging
from typing import Dict, Any, List, Optional
from github import Github, GithubException
from github.NamedUser import NamedUser
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GitHubProfileService:
    """Service for tracking GitHub user profiles and contributions"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")

        if not self.token:
            logger.warning("GitHub token not provided. API operations will fail or be rate-limited.")
            self.client = Github()  # Anonymous client, very limited
        else:
            self.client = Github(self.token)

        # FIXME: In-memory cache of contributor data for demo, this would be stored in a database in production
        self.contributors = {}

    async def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get basic profile information for a GitHub user"""
        try:
            user = self.client.get_user(username)

            return {
                "username": user.login,
                "name": user.name,
                "avatar_url": user.avatar_url,
                "bio": user.bio,
                "public_repos": user.public_repos,
                "followers": user.followers,
                "url": user.html_url,
                "company": user.company,
                "location": user.location,
                "blog": user.blog,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        except GithubException as e:
            logger.error(f"Error fetching profile for user {username}: {str(e)}")
            return None

    async def check_first_contribution(self, username: str, repo_name: str) -> bool:
        """Check if this is the user's first contribution to this repo"""
        try:
            cache_key = f"{username}:{repo_name}"

            if cache_key in self.contributors:
                return self.contributors[cache_key]["is_first_contribution"]

            repo = self.client.get_repo(repo_name)

            issues = list(repo.get_issues(creator=username))
            prs = list(repo.get_pulls(creator=username))

            is_first = len(issues) <= 1 and len(prs) <= 1

            self.contributors[cache_key] = {
                "username": username,
                "repo": repo_name,
                "is_first_contribution": is_first,
                "issue_count": len(issues),
                "pr_count": len(prs)
            }

            return is_first
        except GithubException as e:
            logger.error(f"Error checking first contribution for {username} to {repo_name}: {str(e)}")
            return True
