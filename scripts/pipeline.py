#!/usr/bin/env python3
"""Validate the sample pipeline config, or test it against the sample events. Both create nothing in your account."""
import argparse
import json
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER_ROLE = "arn:aws:iam::111122223333:role/placeholder"


def body(role_arn):
    return (ROOT / "pipeline" / "pipeline.yaml").read_text().replace("SOURCE_ROLE_ARN", role_arn)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "test"])
    parser.add_argument("--role-arn", default=PLACEHOLDER_ROLE, help="defaults to a placeholder; neither call assumes it")
    args = parser.parse_args()

    client = boto3.client("observabilityadmin")
    config = {"Body": body(args.role_arn)}

    if args.command == "validate":
        errors = client.validate_telemetry_pipeline_configuration(Configuration=config).get("Errors", [])
        print(json.dumps(errors, indent=2) if errors else "Valid")
        raise SystemExit(1 if errors else 0)

    lines = (ROOT / "samples" / "events.jsonl").read_text().splitlines()
    records = [{"Data": line, "Type": "STRING"} for line in lines]
    results = client.test_telemetry_pipeline(Configuration=config, Records=records, SignalType="LOG")["Results"]
    for result in results:
        print(result.get("Error") or result["Record"]["Data"])
    raise SystemExit(1 if any("Error" in result for result in results) else 0)


if __name__ == "__main__":
    main()
