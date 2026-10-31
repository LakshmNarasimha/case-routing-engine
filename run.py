"""Execution runner: Generates datasets, verifies checksums, and dumps outputs."""

import os
import argparse
import hashlib
import pandas as pd
from src.generator import SyntheticDataGenerator


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def run_pipeline(
    scale: str = "starter", output_dir: str = "./output", seed: int = 20261022
):
    os.makedirs(output_dir, exist_ok=True)

    if scale == "full":
        ticket_count = 30000
        agent_count = 100
        customer_count = 5000
    else:
        ticket_count = 1000
        agent_count = 50
        customer_count = 300

    print(
        f"--- Starting Generator [Scale: {scale.upper()} | Seed: {seed} | Tickets: {ticket_count}] ---"
    )

    gen = SyntheticDataGenerator(seed=seed)
    gen.generate_masters(num_customers=customer_count, num_agents=agent_count)
    gen.generate_workload(num_tickets=ticket_count)

    datasets = {
        "customers": pd.DataFrame([vars(x) for x in gen.customers]),
        "agents": pd.DataFrame(
            [
                {
                    **vars(x),
                    "skills": ";".join(x.skills),
                    "languages": ";".join(x.languages),
                    "channels": ";".join(x.channels),
                }
                for x in gen.agents
            ]
        ),
        "tickets": pd.DataFrame([vars(x) for x in gen.tickets]),
        "messages": pd.DataFrame([vars(x) for x in gen.messages]),
        "assignments": pd.DataFrame([vars(x) for x in gen.assignments]),
        "sla_events": pd.DataFrame([vars(x) for x in gen.sla_events]),
        "resolutions": pd.DataFrame([vars(x) for x in gen.resolutions]),
        "ground_truth": pd.DataFrame([vars(x) for x in gen.anomalies]),
    }

    manifest = {}
    for name, df in datasets.items():
        file_path = os.path.join(output_dir, f"{name}.csv")
        df.to_csv(file_path, index=False)
        manifest[name] = {
            "rows": len(df),
            "sha256": compute_sha256(file_path),
        }
        print(f"Exported {name}.csv -> {len(df)} rows")

    print("\n--- Generation Completed Successfully ---")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Omnichannel Engine Data Generator"
    )
    parser.add_argument(
        "--scale",
        choices=["starter", "full"],
        default="starter",
        help="Volume scale: starter (1k) or full (30k)",
    )
    parser.add_argument(
        "--output", default="./output", help="Destination folder"
    )
    parser.add_argument(
        "--seed", type=int, default=20261022, help="Deterministic PRNG seed"
    )
    args = parser.parse_args()

    run_pipeline(scale=args.scale, output_dir=args.output, seed=args.seed)