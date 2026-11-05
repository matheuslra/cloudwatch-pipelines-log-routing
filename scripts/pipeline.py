#!/usr/bin/env python3
"""Validate, test or create the sample pipeline. Validate and test create nothing in your account."""
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
    parser.add_argument("command", choices=["validate", "test", "create"])
    parser.add_argument("--role-arn", help="the stack's PipelineRoleArn output; required for create")
    args = parser.parse_args()
    if args.command == "create" and not args.role_arn:
        parser.error("create needs --role-arn")

    client = boto3.client("observabilityadmin")
    config = {"Body": body(args.role_arn or PLACEHOLDER_ROLE)}

    if args.command == "validate":
        errors = client.validate_telemetry_pipeline_configuration(Configuration=config).get("Errors", [])
        print(json.dumps(errors, indent=2) if errors else "Valid")
        raise SystemExit(1 if errors else 0)

    if args.command == "test":
        lines = (ROOT / "samples" / "events.jsonl").read_text().splitlines()
        records = [{"Data": line, "Type": "STRING"} for line in lines]
        results = client.test_telemetry_pipeline(Configuration=config, Records=records, SignalType="LOG")["Results"]
        for result in results:
            print(result.get("Error") or result["Record"]["Data"])
        raise SystemExit(1 if any("Error" in result for result in results) else 0)

    arn = client.create_telemetry_pipeline(Name="sample-checkout-routing", Configuration=config)["Arn"]
    print(f"Created {arn}")


if __name__ == "__main__":
    main()
