"""Domain definitions, enums, and schemas for Omnichannel Routing."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ChannelEnum(str, Enum):
    EMAIL = "EMAIL"
    CHAT = "CHAT"
    PHONE = "PHONE"


class UrgencyEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TicketStatus(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class AssignmentEventType(str, Enum):
    INITIAL_ROUTING = "INITIAL_ROUTING"
    TRANSFER = "TRANSFER"
    ESCALATION = "ESCALATION"
    CAPACITY_BREACH_FORCED = "CAPACITY_BREACH_FORCED"


class AnomalyType(str, Enum):
    NONE = "NONE"
    AGENT_CAPACITY_BREACH = "AGENT_CAPACITY_BREACH"
    SLA_CALENDAR_IGNORED = "SLA_CALENDAR_IGNORED"
    REOPEN_LOST_HISTORY = "REOPEN_LOST_HISTORY"
    TRANSFER_LOOP = "TRANSFER_LOOP"
    PRIORITY_SAFETY_VIOLATION = "PRIORITY_SAFETY_VIOLATION"


@dataclass
class Agent:
    agent_id: str
    name: str
    skills: list[str]
    languages: list[str]
    channels: list[str]
    max_capacity: int
    current_load: int = 0


@dataclass
class Customer:
    customer_id: str
    name: str
    tier: str
    preferred_language: str


@dataclass
class Ticket:
    ticket_id: str
    customer_id: str
    channel_id: str
    intent_id: str
    language: str
    urgency: str
    priority: int
    status: str
    created_at: str
    sla_deadline: str


@dataclass
class Message:
    message_id: str
    ticket_id: str
    sender_type: str
    content: str
    created_at: str


@dataclass
class AssignmentEvent:
    assignment_id: str
    ticket_id: str
    agent_id: str
    event_type: str
    assigned_at: str
    released_at: Optional[str] = None


@dataclass
class SLAEvent:
    sla_event_id: str
    ticket_id: str
    target_minutes: int
    actual_minutes: Optional[int]
    is_breached: bool


@dataclass
class Resolution:
    resolution_id: str
    ticket_id: str
    resolved_at: str
    csat_score: Optional[int]


@dataclass
class GroundTruthAnomaly:
    anomaly_id: str
    entity_id: str
    anomaly_type: str
    description: str