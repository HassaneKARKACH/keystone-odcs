#!/usr/bin/env bash
# Show what the keystone command reports on each invalid contract: every one of them fails.
# Run from the root of the repository: bash examples/validate_invalid.sh

for contract in examples/cyclomatic/invalid/*.odcs.yaml; do
  uv run keystone validate "$contract"
done
