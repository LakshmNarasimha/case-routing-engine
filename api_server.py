"""
OmniRoute Lightweight Backend Server
Bridges generated datasets directly to the UI, providing real-time routing,
decision traceability, SLA countdown analytics, and data exports.
"""

import http.server
import socketserver
import json
import os
import sys
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from src.engine import calculate_priority, select_best_agent
from src.models import Agent

PORT = 8000
DATA_DIR = "./output"

class OmniRouteHandler(http.server.SimpleHTTPRequestHandler):

    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Serve index.html cleanly on root
        if path in ["/", ""]:
            self.path = "/index.html"
            return super().do_GET()

        # 1. Dashboard Stats
        if path == "/api/stats":
            self._set_headers()
            try:
                tickets = pd.read_csv(os.path.join(DATA_DIR, "tickets.csv"))
                agents = pd.read_csv(os.path.join(DATA_DIR, "agents.csv"))
                sla_events = pd.read_csv(os.path.join(DATA_DIR, "sla_events.csv"))
                gt = pd.read_csv(os.path.join(DATA_DIR, "ground_truth.csv"))

                breached_count = int(sla_events["is_breached"].sum())
                adherence = round((1 - (breached_count / len(sla_events))) * 100, 1)

                stats = {
                    "total_tickets": len(tickets),
                    "total_agents": len(agents),
                    "sla_adherence": adherence,
                    "breached_count": breached_count,
                    "anomaly_count": len(gt),
                }
                self.wfile.write(json.dumps(stats).encode())
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # 2. Live Agent Fleet
        if path == "/api/agents":
            self._set_headers()
            try:
                agents_df = pd.read_csv(os.path.join(DATA_DIR, "agents.csv"))
                agents = agents_df.head(10).to_dict(orient="records")
                for a in agents:
                    a["skills"] = str(a["skills"]).split(";")
                    a["languages"] = str(a["languages"]).split(";")
                    a["channels"] = str(a["channels"]).split(";")
                self.wfile.write(json.dumps(agents).encode())
            except Exception as e:
                self.wfile.write(json.dumps([]).encode())
            return

        # 3. Dynamic SLA Management
        if path == "/api/sla_dashboard":
            self._set_headers()
            try:
                tickets_df = pd.read_csv(os.path.join(DATA_DIR, "tickets.csv")).head(25)
                sla_records = []
                now = datetime.now()

                for _, row in tickets_df.iterrows():
                    deadline = datetime.fromisoformat(str(row["sla_deadline"]))
                    remaining = int((deadline - now).total_seconds() / 60)
                    
                    if remaining < 0:
                        status = "BREACHED"
                    elif remaining < 60:
                        status = "AT_RISK"
                    else:
                        status = "HEALTHY"

                    sla_records.append({
                        "ticket_id": row["ticket_id"],
                        "priority": int(row["priority"]),
                        "channel": row["channel_id"],
                        "deadline": str(row["sla_deadline"]),
                        "remaining_mins": remaining,
                        "status": status
                    })
                self.wfile.write(json.dumps(sla_records).encode())
            except Exception as e:
                self.wfile.write(json.dumps([]).encode())
            return

        # 4. Ground Truth Anomalies
        if path == "/api/anomalies":
            self._set_headers()
            try:
                gt_df = pd.read_csv(os.path.join(DATA_DIR, "ground_truth.csv"))
                self.wfile.write(gt_df.head(15).to_json(orient="records").encode())
            except Exception as e:
                self.wfile.write(json.dumps([]).encode())
            return

        # 5. Full Export
        if path == "/api/export":
            query = parse_qs(parsed.query)
            table = query.get("table", ["tickets"])[0]
            fmt = query.get("format", ["csv"])[0]
            file_path = os.path.join(DATA_DIR, f"{table}.csv")

            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                if fmt == "json":
                    self._set_headers("application/json")
                    self.send_header("Content-Disposition", f'attachment; filename="{table}.json"')
                    self.wfile.write(df.to_json(orient="records", indent=2).encode())
                else:
                    self._set_headers("text/csv")
                    self.send_header("Content-Disposition", f'attachment; filename="{table}.csv"')
                    self.wfile.write(df.to_csv(index=False).encode())
            else:
                self.send_error(404, "File not found")
            return

        # Default static file serving (strip query parameters to avoid 404s/connection resets)
        self.path = parsed.path
        try:
            return super().do_GET()
        except ConnectionAbortedError:
            pass

    def do_POST(self):
        if self.path == "/api/route_case":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                raw_data = self.rfile.read(content_length).decode()
                body = json.loads(raw_data) if raw_data else {}

                tier = body.get("tier", "STANDARD")
                channel = body.get("channel", "EMAIL")
                lang = body.get("lang", "en")
                skill = body.get("skill", "TECHNICAL")
                urgency = body.get("urgency", "MEDIUM")
                anomaly = body.get("anomaly", "NONE")

                safety_override = (anomaly == "PRIORITY_SAFETY_VIOLATION")
                priority = calculate_priority(tier, urgency, safety_override)

                agents_df = pd.read_csv(os.path.join(DATA_DIR, "agents.csv"))
                agent_pool = [
                    Agent(
                        agent_id=str(r["agent_id"]),
                        name=str(r["name"]),
                        skills=str(r["skills"]).split(";"),
                        languages=str(r["languages"]).split(";"),
                        channels=str(r["channels"]).split(";"),
                        max_capacity=int(r["max_capacity"]),
                        current_load=int(r["current_load"])
                    ) for _, r in agents_df.head(20).iterrows()
                ]

                force_capacity = (anomaly == "AGENT_CAPACITY_BREACH")
                chosen_agent = select_best_agent(agent_pool, skill, lang, channel, force_capacity)

                decision_trace = {
                    "ticket_id": f"TKT-2026-{datetime.now().strftime('%M%S%f')[:6]}",
                    "assigned_agent_id": chosen_agent.agent_id if chosen_agent else "UNASSIGNED",
                    "assigned_agent_name": chosen_agent.name if chosen_agent else "None",
                    "priority_assigned": priority,
                    "reasons": [
                        f"Matched required skill: '{skill}' in agent competencies {chosen_agent.skills if chosen_agent else []}",
                        f"Matched language: '{lang}' in agent languages {chosen_agent.languages if chosen_agent else []}",
                        f"Channel support: '{channel}' accepted by agent",
                        f"Capacity check: Current load {chosen_agent.current_load if chosen_agent else 0}/{chosen_agent.max_capacity if chosen_agent else 0} slots",
                        f"Calendar calculation: Priority {priority} mapped to calendar SLA target"
                    ],
                    "anomaly_triggered": anomaly if anomaly != "NONE" else None
                }

                self._set_headers()
                self.wfile.write(json.dumps(decision_trace).encode())
            except Exception as e:
                self._set_headers()
                self.wfile.write(json.dumps({"error": str(e), "reasons": [str(e)]}).encode())

    # Suppress broken socket error spam in console
    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionAbortedError, ConnectionResetError):
            pass

if __name__ == "__main__":
    print(f"--- OmniRoute Live API Server running at http://localhost:{PORT} ---")
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), OmniRouteHandler) as httpd:
        httpd.serve_forever()