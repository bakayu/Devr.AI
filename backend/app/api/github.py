import logging
import uuid
import hmac
import hashlib
import os
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from typing import Optional
from pydantic import BaseModel

from ..core.events.github_event import GitHubEvent
from ..core.events.enums import EventType, PlatformType
from ..core.events.init_events import initialize_event_system
from ..services.github_service import GitHubService

logger = logging.getLogger(__name__)

event_bus = initialize_event_system()

github_service = GitHubService()

router = APIRouter(prefix="/github", tags=["github"])

class GitHubPayload(BaseModel):
    """GitHub webhook payload validation schema"""
    action: Optional[str] = None
    sender: Optional[dict] = None

async def verify_signature(request: Request, x_hub_signature_256: Optional[str] = Header(None)) -> bool:
    """Verify webhook signature using GitHub secret"""
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")

    if not webhook_secret:
        logger.warning("GitHub webhook secret not configured, signature verification skipped")
        return True

    if not x_hub_signature_256:
        logger.warning("No signature header provided in request")
        return False

    try:
        body = await request.body()

        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()

        expected_signature = f"sha256={signature}"
        return hmac.compare_digest(expected_signature, x_hub_signature_256)
    except Exception as e:
        logger.error(f"Error verifying signature: {str(e)}")
        return False

@router.post("/webhook")
async def github_webhook(request: Request, verified: bool = Depends(verify_signature)):
    """Handle GitHub webhook events (issues and pull requests)"""
    if not verified:
        raise HTTPException(status_code=401, detail="Invalid signature")

    event_header = request.headers.get("X-GitHub-Event")
    if not event_header:
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Event header")

    delivery_id = request.headers.get("X-GitHub-Delivery", str(uuid.uuid4()))
    payload = await request.json()

    logger.info(f"Received GitHub event: {event_header} with action: {payload.get('action')}")

    event_type = None

    # Currently only handling issue and PR creation for demo purposes
    if event_header == "issues" and payload.get("action") == "opened":
        event_type = EventType.ISSUE_CREATED
    elif event_header == "pull_request" and payload.get("action") == "opened":
        event_type = EventType.PR_CREATED

    if event_type:
        try:
            # Extract repository information
            repo_name = payload.get("repository", {}).get("full_name", "unknown")
            organization = repo_name.split("/")[0] if "/" in repo_name else None

            # Create appropriate event object
            if event_type == EventType.ISSUE_CREATED:
                event = GitHubEvent(
                    id=delivery_id,
                    platform=PlatformType.GITHUB,
                    event_type=event_type,
                    actor_id=str(payload.get("sender", {}).get("id", "unknown")),
                    actor_name=payload.get("sender", {}).get("login"),
                    repository=repo_name,
                    organization=organization,
                    issue_number=payload.get("issue", {}).get("number"),
                    title=payload.get("issue", {}).get("title"),
                    body=payload.get("issue", {}).get("body"),
                    url=payload.get("issue", {}).get("html_url"),
                    raw_data=payload
                )
            elif event_type == EventType.PR_CREATED:
                event = GitHubEvent(
                    id=delivery_id,
                    platform=PlatformType.GITHUB,
                    event_type=event_type,
                    actor_id=str(payload.get("sender", {}).get("id", "unknown")),
                    actor_name=payload.get("sender", {}).get("login"),
                    repository=repo_name,
                    organization=organization,
                    pr_number=payload.get("pull_request", {}).get("number"),
                    title=payload.get("pull_request", {}).get("title"),
                    body=payload.get("pull_request", {}).get("body"),
                    url=payload.get("pull_request", {}).get("html_url"),
                    raw_data=payload
                )

            result = await event_bus.dispatch(event)

            return {
                "status": "success",
                "message": f"Event {event_type} processed successfully",
                "result": result,
                "event_id": delivery_id
            }

        except Exception as e:
            logger.error(f"Error processing GitHub event: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing event: {str(e)}")

    else:
        # Unsupported event type
        logger.info(f"Unsupported GitHub event: {event_header} with action: {payload.get('action')}")
        return {
            "status": "ignored",
            "message": f"Event {event_header} with action {payload.get('action')} is not supported"
        }
