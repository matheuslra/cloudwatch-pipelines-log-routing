#!/usr/bin/env python3
"""Check pipeline.yaml with no AWS account: the documented limits, and that every route tests a field
a parser produces. It then predicts each sample event's route.

The prediction uses a small stand-in for Grok and the `when` syntax, so it only understands what this
sample uses. It checks this config's logic and doesn't replace TestTelemetryPipeline.
"""
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
GROK = {"WORD": r"[A-Za-z0-9_]+", "GREEDYDATA": ".*"}
CONDITION = re.compile(r'^(\w+) (==|!=) "([^"]*)"$')


def grok_regex(pattern):
    def group(match):
        return f"(?P<{match.group(2)}>{GROK[match.group(1)]})"

    return re.compile(re.sub(r"%\{(\w+):(\w+)\}", group, pattern))


def conditions(when):
    parsed = [CONDITION.match(part) for part in when.split(" and ")]
    if not all(parsed):
        raise ValueError(f"unsupported condition: {when}")
    return [match.groups() for match in parsed]


def matches(when, event):
    return all((event.get(field) == value) == (op == "==") for field, op, value in conditions(when))


def route(event, sinks):
    for sink in sinks:
        if "when" in sink and matches(sink["when"], event):
            return sink["log_group"]
    return next(sink["log_group"] for sink in sinks if sink.get("is_default"))


def check(root):
    pipeline = yaml.safe_load((root / "pipeline" / "pipeline.yaml").read_text())["pipeline"]
    processors, sinks = pipeline["processor"], [s["cloudwatch_logs"] for s in pipeline["sink"]]
    errors = []
    if len(processors) > 20:
        errors.append("a pipeline can have at most 20 processors")
    if len(sinks) > 10:
        errors.append("a pipeline can have at most 10 cloudwatch_logs sinks")
    if sum(1 for sink in sinks if sink.get("is_default")) != 1:
        errors.append("exactly one route must set is_default")

    match = next(p["grok"] for p in processors if "grok" in p)["match"]
    source_field, patterns = next(iter(match.items()))
    regex = grok_regex(patterns[0])
    for sink in sinks:
        for field, _, _ in conditions(sink["when"]) if "when" in sink else []:
            if field not in regex.groupindex:
                errors.append(f'{sink["log_group"]} tests {field}, which no parser produces')

    samples = (root / "samples" / "events.jsonl").read_text().splitlines()
    expected = json.loads((root / "samples" / "expected-routes.json").read_text())
    if len(samples) != len(expected):
        errors.append("events.jsonl and expected-routes.json have different lengths")
    for line, want in zip(samples, expected):
        event = json.loads(line)
        found = regex.fullmatch(event[source_field])
        got = route({**event, **(found.groupdict() if found else {})}, sinks)
        print(f"{got:28} {event[source_field]}")
        if got != want:
            errors.append(f"expected {want}, got {got}: {event[source_field]}")
    return errors


if __name__ == "__main__":
    problems = check(ROOT)
    print("\n".join(problems) if problems else "Config OK")
    raise SystemExit(1 if problems else 0)
