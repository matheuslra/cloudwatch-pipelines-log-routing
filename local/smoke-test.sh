#!/usr/bin/env bash
# Runs the offline check, and proves it fails on a broken config. Needs local/requirements.txt.
set -euo pipefail

python local/check_config.py

broken="$(mktemp -d)"
trap 'rm -rf "$broken"' EXIT
cp -r pipeline samples "$broken"
sed -i 's/component == "auth"/team == "auth"/' "$broken/pipeline/pipeline.yaml"
if python local/check_config.py "$broken"; then
  echo "FAIL: the check accepted a route on a field no parser produces"
  exit 1
fi
echo "Smoke test passed"
