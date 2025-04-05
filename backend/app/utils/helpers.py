import json
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)

def load_sample_payload(event_type: str) -> dict:
    """Load a sample payload from the samples directory"""
    try:
        samples_dir = Path(__file__).parent.parent.parent / "tests" / "samples"
        file_path = samples_dir / f"{event_type}.json"

        if not file_path.exists():
            logger.warning(f"Sample file not found: {file_path}")
            return {}

        with open(file_path, "r") as f:
            return json.load(f)

    except Exception as e:
        logger.error(f"Error loading sample payload: {str(e)}")
        return {}

def create_sample_payloads():
    """Create sample payload files for testing"""
    samples_dir = Path(__file__).parent.parent.parent / "tests" / "samples"
    os.makedirs(samples_dir, exist_ok=True)

    # Sample issue created
    issue_created = {
        "action": "opened",
        "issue": {
            "number": 1,
            "title": "Sample Issue Title",
            "body": "This is a sample issue body for testing",
            "html_url": "https://github.com/sample/repo/issues/1"
        },
        "repository": {
            "full_name": "sample/repo",
            "html_url": "https://github.com/sample/repo"
        },
        "sender": {
            "id": 12345,
            "login": "sample-user"
        }
    }

    # Sample PR created
    pr_created = {
        "action": "opened",
        "pull_request": {
            "number": 2,
            "title": "Sample PR Title",
            "body": "This is a sample PR body for testing",
            "html_url": "https://github.com/sample/repo/pull/2"
        },
        "repository": {
            "full_name": "sample/repo",
            "html_url": "https://github.com/sample/repo"
        },
        "sender": {
            "id": 12345,
            "login": "sample-user"
        }
    }

    with open(samples_dir / "issue_created.json", "w") as f:
        json.dump(issue_created, f, indent=2)

    with open(samples_dir / "pr_created.json", "w") as f:
        json.dump(pr_created, f, indent=2)

    logger.info(f"Created sample payload files in: {samples_dir}")
