"""ODCS check: does a contract match the official ODCS v3.2.0 schema."""

import json
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft201909Validator

SCHEMA_FILE = Path(__file__).with_name("schemas") / "odcs-json-schema-v3.2.0.json"
SCHEMA = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
# Formats (dates, URIs) are checked too, as the official ODCS validation does.
VALIDATOR = Draft201909Validator(SCHEMA, format_checker=Draft201909Validator.FORMAT_CHECKER)


@dataclass(frozen=True, order=True)
class Violation:
    """One place where a contract breaks the ODCS schema."""

    path: str
    message: str


def validate(contract: object) -> list[Violation]:
    """Return every ODCS violation of a contract, sorted by path."""
    # Several branches of the schema can raise the same error: list it once.
    violations = {Violation(error.json_path, error.message) for error in VALIDATOR.iter_errors(contract)}
    return sorted(violations)
