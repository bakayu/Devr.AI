from enum import Enum

class PlatformType(str, Enum):
    GITHUB = "github"
    DISCORD = "discord"
    SLACK = "slack"
    DISCOURSE = "discourse"
    SYSTEM = "system"

class EventType(str, Enum):
    # Issue events
    ISSUE_CREATED = "issue.created"
    ISSUE_CLOSED = "issue.closed"
    ISSUE_UPDATED = "issue.updated"
    ISSUE_COMMENTED = "issue.commented"

    # PR events
    PR_CREATED = "pr.created"
    PR_UPDATED = "pr.updated"
    PR_COMMENTED = "pr.commented"
    PR_MERGED = "pr.merged"
    PR_REVIEWED = "pr.reviewed"

    # Message events
    MESSAGE_CREATED = "message.created"
    MESSAGE_UPDATED = "message.updated"
    REACTION_ADDED = "reaction.added"
    USER_JOINED = "user.joined"

    # Onboarding events
    ONBOARDING_STARTED = "onboarding.started"
    ONBOARDING_COMPLETED = "onboarding.completed"

    # Knowledge events
    FAQ_REQUESTED = "faq.requested"
    KNOWLEDGE_UPDATED = "knowledge.updated"

    # RAG query events
    RAG_QUERY = "rag.query"
    RAG_RESPONSE = "rag.response"

    # Analytics events
    ANALYTICS_COLLECTED = "analytics.collected"
