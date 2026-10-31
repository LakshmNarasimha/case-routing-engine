"""Core Business Logic: Skill Routing, SLA Tracking, and Anomaly Injection."""

from datetime import datetime, timedelta
from typing import Optional
from src.models import Agent

SLA_TARGET_MINUTES = {
    1: 60,    # Critical: 1 hour
    2: 240,   # High: 4 hours
    3: 720,   # Medium: 12 hours
    4: 1440,  # Low: 24 hours
}


def calculate_sla_deadline(
    start_time: datetime, priority: int, channel: str, ignore_calendar: bool = False
) -> datetime:
    """Calculates SLA deadline using channel-specific operating calendars."""
    target_mins = SLA_TARGET_MINUTES[priority]

    if ignore_calendar or channel in ["CHAT", "PHONE"]:
        return start_time + timedelta(minutes=target_mins)

    # Business Hours (Email channel): 09:00 - 17:00, weekdays only
    current = start_time
    remaining_mins = target_mins

    while remaining_mins > 0:
        if current.weekday() >= 5:  # Saturday or Sunday
            current = current.replace(hour=9, minute=0, second=0) + timedelta(
                days=(7 - current.weekday())
            )
            continue

        if current.hour < 9:
            current = current.replace(hour=9, minute=0, second=0)
        elif current.hour >= 17:
            current = (current + timedelta(days=1)).replace(
                hour=9, minute=0, second=0
            )
            continue

        end_of_business_day = current.replace(hour=17, minute=0, second=0)
        available_today = int((end_of_business_day - current).total_seconds() / 60)

        if remaining_mins <= available_today:
            current += timedelta(minutes=remaining_mins)
            remaining_mins = 0
        else:
            remaining_mins -= available_today
            current = (current + timedelta(days=1)).replace(
                hour=9, minute=0, second=0
            )

    return current


def calculate_priority(
    tier: str, urgency: str, contradict_safety: bool = False
) -> int:
    """Computes deterministic priority rank 1 (highest) to 4 (lowest)."""
    if contradict_safety:
        return 4  # Edge case: critical anomaly

    if urgency == "CRITICAL" or tier == "VIP":
        return 1
    if urgency == "HIGH" or tier == "PREMIUM":
        return 2
    if urgency == "MEDIUM":
        return 3
    return 4


def select_best_agent(
    agents: list[Agent],
    required_skill: str,
    required_lang: str,
    channel: str,
    force_capacity_breach: bool = False,
) -> Optional[Agent]:
    """Matches agent based on Skill, Language, Channel, and current capacity."""
    qualified = [
        agt
        for agt in agents
        if required_skill in agt.skills
        and required_lang in agt.languages
        and channel in agt.channels
    ]

    if not qualified:
        qualified = [
            agt
            for agt in agents
            if required_skill in agt.skills and channel in agt.channels
        ]

    if force_capacity_breach and qualified:
        overloaded = [a for a in qualified if a.current_load >= a.max_capacity]
        if overloaded:
            return overloaded[0]
        return qualified[0]

    available = [a for a in qualified if a.current_load < a.max_capacity]
    if not available:
        return None

    available.sort(key=lambda a: (a.current_load / a.max_capacity))
    return available[0]