"""Data Generation pipeline producing Master, Event, and Ground-Truth records."""

import random
from datetime import datetime, timedelta
from src.models import (
    Customer,
    Agent,
    Ticket,
    Message,
    AssignmentEvent,
    AssignmentEventType,
    SLAEvent,
    Resolution,
    GroundTruthAnomaly,
    AnomalyType,
)
from src.engine import calculate_priority, calculate_sla_deadline, select_best_agent

SKILLS = ["BILLING", "TECHNICAL", "ONBOARDING", "CANCELLATION", "ACCOUNT"]
LANGUAGES = ["en", "es", "fr", "de"]
CHANNELS = ["EMAIL", "CHAT", "PHONE"]
URGENCIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
TIERS = ["STANDARD", "PREMIUM", "VIP"]


class SyntheticDataGenerator:

    def __init__(self, seed: int = 20261022):
        self.seed = seed
        self.rng = random.Random(seed)

        self.customers: list[Customer] = []
        self.agents: list[Agent] = []
        self.tickets: list[Ticket] = []
        self.messages: list[Message] = []
        self.assignments: list[AssignmentEvent] = []
        self.sla_events: list[SLAEvent] = []
        self.resolutions: list[Resolution] = []
        self.anomalies: list[GroundTruthAnomaly] = []

    def generate_masters(self, num_customers: int = 500, num_agents: int = 100):
        for i in range(1, num_customers + 1):
            cust_id = f"CUST-{i:06d}"
            tier = self.rng.choice(TIERS)
            lang = self.rng.choices(LANGUAGES, weights=[0.7, 0.15, 0.1, 0.05])[0]
            self.customers.append(Customer(cust_id, f"Customer_{i}", tier, lang))

        for i in range(1, num_agents + 1):
            agt_id = f"AGT-{i:06d}"
            skills_count = self.rng.choice([1, 2, 3])
            agt_skills = self.rng.sample(SKILLS, k=skills_count)

            agt_langs = ["en"]
            if self.rng.random() < 0.3:
                agt_langs.append(self.rng.choice(["es", "fr", "de"]))

            agt_channels = self.rng.sample(CHANNELS, k=self.rng.choice([1, 2, 3]))
            max_capacity = 1 if "PHONE" in agt_channels else self.rng.choice([3, 4, 5])

            self.agents.append(
                Agent(
                    agt_id,
                    f"Agent_{i}",
                    agt_skills,
                    agt_langs,
                    agt_channels,
                    max_capacity,
                )
            )

    def generate_workload(
        self,
        num_tickets: int = 1000,
        start_date: datetime = datetime(2026, 8, 1, 0, 0),
        days: int = 90,
    ):
        for i in range(1, num_tickets + 1):
            ticket_id = f"TKT-2026-{i:06d}"
            cust = self.rng.choice(self.customers)
            channel = self.rng.choice(CHANNELS)
            intent = f"INT-{self.rng.choice(SKILLS)}"
            required_skill = intent.split("-")[1]

            lang = (
                cust.preferred_language
                if self.rng.random() > 0.1
                else self.rng.choice(LANGUAGES)
            )
            urgency = self.rng.choice(URGENCIES)

            offset_seconds = self.rng.randint(0, days * 86400)
            created_at = start_date + timedelta(seconds=offset_seconds)

            inject_safety_violation = (i % 200 == 0)
            inject_capacity_breach = (i % 250 == 0)
            inject_sla_breach_anomaly = (i % 300 == 0)
            inject_transfer_loop = (i % 350 == 0)
            inject_reopen_lost_history = (i % 400 == 0)

            priority = calculate_priority(
                cust.tier, urgency, inject_safety_violation
            )
            if inject_safety_violation:
                self.anomalies.append(
                    GroundTruthAnomaly(
                        f"ANOM-{len(self.anomalies)+1:05d}",
                        ticket_id,
                        AnomalyType.PRIORITY_SAFETY_VIOLATION.value,
                        "Critical VIP ticket routed with Low priority",
                    )
                )

            sla_deadline = calculate_sla_deadline(
                created_at, priority, channel, inject_sla_breach_anomaly
            )
            if inject_sla_breach_anomaly:
                self.anomalies.append(
                    GroundTruthAnomaly(
                        f"ANOM-{len(self.anomalies)+1:05d}",
                        ticket_id,
                        AnomalyType.SLA_CALENDAR_IGNORED.value,
                        "Email SLA calculated without business hour restrictions",
                    )
                )

            ticket = Ticket(
                ticket_id=ticket_id,
                customer_id=cust.customer_id,
                channel_id=channel,
                intent_id=intent,
                language=lang,
                urgency=urgency,
                priority=priority,
                status="NEW",
                created_at=created_at.isoformat(),
                sla_deadline=sla_deadline.isoformat(),
            )

            msg_id = f"MSG-{ticket_id}-001"
            self.messages.append(
                Message(
                    msg_id,
                    ticket_id,
                    "CUSTOMER",
                    f"Need support with {required_skill}",
                    created_at.isoformat(),
                )
            )

            assigned_agent = select_best_agent(
                self.agents,
                required_skill,
                lang,
                channel,
                inject_capacity_breach,
            )

            if assigned_agent:
                if inject_capacity_breach:
                    # Force agent load over the capacity limit and log ground truth anomaly
                    assigned_agent.current_load = assigned_agent.max_capacity + 1
                    event_type = AssignmentEventType.CAPACITY_BREACH_FORCED.value
                    self.anomalies.append(
                        GroundTruthAnomaly(
                            f"ANOM-{len(self.anomalies)+1:05d}",
                            ticket_id,
                            AnomalyType.AGENT_CAPACITY_BREACH.value,
                            f"Agent {assigned_agent.agent_id} forced assigned beyond capacity limit of {assigned_agent.max_capacity}",
                        )
                    )
                else:
                    event_type = AssignmentEventType.INITIAL_ROUTING.value

                asn_id = f"ASN-{ticket_id}-001"
                assigned_time = created_at + timedelta(
                    minutes=self.rng.randint(1, 15)
                )
                self.assignments.append(
                    AssignmentEvent(
                        asn_id,
                        ticket_id,
                        assigned_agent.agent_id,
                        event_type,
                        assigned_time.isoformat(),
                    )
                )

                if not inject_capacity_breach:
                    assigned_agent.current_load += 1
                ticket.status = "ASSIGNED"

                if inject_transfer_loop and len(self.agents) > 2:
                    agt2 = self.rng.choice(self.agents)
                    self.assignments.append(
                        AssignmentEvent(
                            f"ASN-{ticket_id}-002",
                            ticket_id,
                            agt2.agent_id,
                            AssignmentEventType.TRANSFER.value,
                            (assigned_time + timedelta(minutes=10)).isoformat(),
                        )
                    )
                    self.assignments.append(
                        AssignmentEvent(
                            f"ASN-{ticket_id}-003",
                            ticket_id,
                            assigned_agent.agent_id,
                            AssignmentEventType.TRANSFER.value,
                            (assigned_time + timedelta(minutes=20)).isoformat(),
                        )
                    )
                    self.anomalies.append(
                        GroundTruthAnomaly(
                            f"ANOM-{len(self.anomalies)+1:05d}",
                            ticket_id,
                            AnomalyType.TRANSFER_LOOP.value,
                            "Ticket bounced between identical agents within 20 mins",
                        )
                    )

                resolution_duration = self.rng.randint(20, 2000)
                resolved_at = created_at + timedelta(minutes=resolution_duration)
                is_breached = resolved_at > sla_deadline

                self.sla_events.append(
                    SLAEvent(
                        sla_event_id=f"SLA-{ticket_id}",
                        ticket_id=ticket_id,
                        target_minutes=int(
                            (sla_deadline - created_at).total_seconds() / 60
                        ),
                        actual_minutes=resolution_duration,
                        is_breached=is_breached,
                    )
                )

                if inject_reopen_lost_history:
                    ticket.status = "REOPENED"
                    self.anomalies.append(
                        GroundTruthAnomaly(
                            f"ANOM-{len(self.anomalies)+1:05d}",
                            ticket_id,
                            AnomalyType.REOPEN_LOST_HISTORY.value,
                            "Ticket reopened with wiped audit references",
                        )
                    )
                else:
                    ticket.status = "RESOLVED"
                    self.resolutions.append(
                        Resolution(
                            f"RES-{ticket_id}",
                            ticket_id,
                            resolved_at.isoformat(),
                            csat_score=self.rng.choice([1, 2, 3, 4, 5]),
                        )
                    )

                # Reset or decrement load
                if inject_capacity_breach:
                    assigned_agent.current_load = assigned_agent.max_capacity
                else:
                    assigned_agent.current_load = max(
                        0, assigned_agent.current_load - 1
                    )

            self.tickets.append(ticket)