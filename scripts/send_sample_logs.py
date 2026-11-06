#!/usr/bin/env python3
"""Write the sample events to the pipeline's source log group, and print where each one should land."""
import json
import time
import uuid
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parent.parent
SOURCE_LOG_GROUP = "/sample/checkout/source"


def main():
    lines = (ROOT / "samples" / "events.jsonl").read_text().splitlines()
    routes = json.loads((ROOT / "samples" / "expected-routes.json").read_text())

    client = boto3.client("logs")
    stream = f"demo-{uuid.uuid4().hex[:8]}"
    client.create_log_stream(logGroupName=SOURCE_LOG_GROUP, logStreamName=stream)
    now = int(time.time() * 1000)
    client.put_log_events(
        logGroupName=SOURCE_LOG_GROUP,
        logStreamName=stream,
        logEvents=[{"timestamp": now, "message": line} for line in lines],
    )

    print(f"Sent {len(lines)} events to {SOURCE_LOG_GROUP} in stream {stream}. Each should land in:")
    for line, route in zip(lines, routes):
        print(f"  {route:<24} {json.loads(line)['log']}")


if __name__ == "__main__":
    main()
