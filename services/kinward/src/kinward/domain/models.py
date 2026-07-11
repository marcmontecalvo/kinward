from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

PersonRole = Literal["admin", "adult", "teen", "child"]
AssistantKind = Literal["primary", "specialist", "temporary", "shared-fallback"]
PrivacyLevel = Literal["household", "personal", "sensitive"]
ApprovalState = Literal["pending", "approved", "denied", "expired"]


@dataclass(frozen=True)
class Household:
    id: str
    name: str


@dataclass(frozen=True)
class Person:
    id: str
    household_id: str
    display_name: str
    role: PersonRole
    email: str | None = None


@dataclass(frozen=True)
class Assistant:
    id: str
    household_id: str
    name: str
    kind: AssistantKind
    owner_person_id: str | None
    personality: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    person_id: str
    assistant_id: str
    content: str
    privacy: PrivacyLevel
    source: str
    created_at: datetime
    confidence: float = 1.0


@dataclass(frozen=True)
class Approval:
    id: str
    household_id: str
    requested_by_person_id: str
    action: str
    explanation: str
    state: ApprovalState = "pending"


@dataclass(frozen=True)
class ActivityEntry:
    id: str
    household_id: str
    assistant_id: str | None
    person_id: str | None
    summary: str
    outcome: Literal["completed", "failed", "denied", "pending"]
    occurred_at: datetime
    undo_token: str | None = None
