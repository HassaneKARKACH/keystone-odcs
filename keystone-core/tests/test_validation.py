"""The ODCS check: a contract that follows the official schema passes, every breach is listed."""

import hashlib

import pytest

from keystone_core import Violation, validate
from keystone_core.validation import SCHEMA_FILE

# SHA-256 of schema/odcs-json-schema-v3.2.0.json at tag v3.2.0 of bitol-io/open-data-contract-standard.
OFFICIAL_SCHEMA_SHA256 = "edb41f33ec46e84780e99872ab2bd67f074959d2bf3e9c9fc54e61f8982b0d93"


@pytest.fixture
def contract():
    return {"apiVersion": "v3.2.0", "kind": "DataContract", "id": "example", "version": "1.0.0"}


def test_the_schema_is_the_official_one_unchanged():
    assert hashlib.sha256(SCHEMA_FILE.read_bytes()).hexdigest() == OFFICIAL_SCHEMA_SHA256


def test_a_minimal_contract_passes(contract):
    assert validate(contract) == []


def test_a_missing_field_is_named(contract):
    del contract["id"]
    assert validate(contract) == [Violation("$", "'id' is a required property")]


def test_a_wrong_value_points_to_its_field(contract):
    contract["schema"] = [{"name": "a_table", "properties": [{"name": "a_column", "logicalType": "text"}]}]
    [violation] = validate(contract)
    assert violation.path == "$.schema[0].properties[0].logicalType"
    assert violation.message.startswith("'text' is not one of")


def test_a_date_must_be_a_real_date(contract):
    contract["contractCreatedTs"] = "yesterday"
    assert validate(contract) == [Violation("$.contractCreatedTs", "'yesterday' is not a 'date-time'")]
