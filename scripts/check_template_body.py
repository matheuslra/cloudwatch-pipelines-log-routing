#!/usr/bin/env python3
"""Fail if the pipeline body in the CloudFormation template drifts from pipeline/pipeline.yaml.

CloudFormation can't read a file, so the template carries its own copy of the config.
The CDK app and the Terraform read pipeline/pipeline.yaml directly.
"""
import difflib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDENT = 10


def config_lines(text):
    return [line.rstrip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def main():
    template = (ROOT / "cloudformation" / "template.yaml").read_text()
    match = re.search(r"Body: !Sub \|\n((?: {%d}.*\n)+)" % INDENT, template)
    if not match:
        raise SystemExit("No pipeline body found in cloudformation/template.yaml")
    inline = "\n".join(line[INDENT:] for line in match.group(1).splitlines())

    expected = (ROOT / "pipeline" / "pipeline.yaml").read_text().replace("SOURCE_ROLE_ARN", "${PipelineRole.Arn}")

    diff = list(difflib.unified_diff(config_lines(expected), config_lines(inline),
                                     "pipeline/pipeline.yaml", "cloudformation/template.yaml", lineterm=""))
    print("\n".join(diff) if diff else "The template's pipeline body matches pipeline/pipeline.yaml")
    raise SystemExit(1 if diff else 0)


if __name__ == "__main__":
    main()
