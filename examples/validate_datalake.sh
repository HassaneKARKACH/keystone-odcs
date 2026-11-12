#!/usr/bin/env bash
# Check the contracts of the Cyclomatic data lake with the keystone command.
# Run from the root of the repository: bash examples/validate_datalake.sh

failed=0
for contract in examples/cyclomatic/ingestion/*.odcs.yaml examples/cyclomatic/data-products/*.odcs.yaml; do
  uv run keystone validate "$contract" || failed=1
done
exit $failed
