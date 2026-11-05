"""The Keystone check: a contract that follows the profile passes, every breach is listed."""

import pytest

from keystone_core import Violation, validate_odcs, validate_profile
from keystone_core.profile import COLUMN_FIELDS, CONTRACT_FIELDS, FORBIDDEN_FIELDS, TABLE_FIELDS


@pytest.fixture
def contract():
    return {
        "apiVersion": "v3.2.0",
        "kind": "DataContract",
        "id": "a_table",
        "name": "a_table",
        "version": "1.0.0",
        "domain": "example",
        "status": "active",
        "team": {"name": "a_team", "members": [{"username": "a_user", "role": "owner"}]},
        "schema": [
            {
                "name": "a_table",
                "physicalName": "a_table",
                "description": "One row per example.",
                "properties": [
                    {
                        "name": "a_column",
                        "logicalType": "string",
                        "description": "The key of an example.",
                        "primaryKey": True,
                        "required": True,
                    }
                ],
            }
        ],
    }


@pytest.fixture
def table(contract):
    return contract["schema"][0]


@pytest.fixture
def column(table):
    return table["properties"][0]


def test_a_contract_that_follows_the_profile_passes(contract):
    assert validate_odcs(contract) == []
    assert validate_profile(contract) == []


@pytest.mark.parametrize("field", CONTRACT_FIELDS)
def test_a_contract_field_is_required(contract, field):
    del contract[field]
    assert validate_profile(contract) == [Violation(f"$.{field}", f"missing: {CONTRACT_FIELDS[field]}")]


@pytest.mark.parametrize("field", TABLE_FIELDS)
def test_a_table_field_is_required(contract, table, field):
    del table[field]
    assert validate_profile(contract) == [Violation(f"$.schema[0].{field}", f"missing: {TABLE_FIELDS[field]}")]


@pytest.mark.parametrize("field", COLUMN_FIELDS)
def test_a_column_field_is_required(contract, column, field):
    del column[field]
    assert validate_profile(contract) == [
        Violation(f"$.schema[0].properties[0].{field}", f"missing: {COLUMN_FIELDS[field]}")
    ]


def test_the_team_is_an_object(contract):
    contract["team"] = [{"username": "a_user", "role": "owner"}]
    assert validate_profile(contract) == [
        Violation("$.team", "a list of members: a team is an object, the list is deprecated")
    ]


def test_the_team_has_a_name(contract):
    del contract["team"]["name"]
    assert validate_profile(contract) == [Violation("$.team.name", "missing: a team has a name")]


def test_the_team_has_an_owner(contract):
    contract["team"]["members"][0]["role"] = "data steward"
    assert validate_profile(contract) == [Violation("$.team.members", "no member with role: owner")]


def test_a_contract_describes_one_table_only(contract, table):
    contract["schema"].append(dict(table, name="another_table"))
    assert validate_profile(contract) == [Violation("$.schema", "2 tables: a contract describes exactly one")]


def test_the_status_is_draft_active_or_deprecated(contract):
    contract["status"] = "proposed"
    assert validate_profile(contract) == [Violation("$.status", "'proposed': a status is draft, active or deprecated")]


def test_the_contract_name_is_its_id(contract):
    contract["name"] = "another_table"
    assert validate_profile(contract) == [
        Violation("$.name", "'another_table': the name of a contract is its id, 'a_table'")
    ]


def test_the_physical_name_is_the_contract_id(contract, table):
    table["physicalName"] = "another_table"
    assert validate_profile(contract) == [
        Violation(
            "$.schema[0].physicalName", "'another_table': the physical name of the table is the contract id, 'a_table'"
        )
    ]


def test_a_table_id_is_its_name(contract, table):
    table["id"] = "another_id"
    assert validate_profile(contract) == [
        Violation("$.schema[0].id", "'another_id': the id of a table is its name, 'a_table'")
    ]


@pytest.mark.parametrize("required", [None, False])
def test_a_primary_key_is_required(contract, column, required):
    column["required"] = required
    assert validate_profile(contract) == [
        Violation("$.schema[0].properties[0].required", "'a_column' is in the primary key: required: true")
    ]


def test_the_contract_name_is_in_snake_case(contract, table):
    contract["id"] = contract["name"] = table["physicalName"] = "A_table"
    assert validate_profile(contract) == [Violation("$.name", "'A_table': names are in snake_case")]


def test_a_table_name_is_in_snake_case(contract, table):
    table["name"] = "a__table"
    assert validate_profile(contract) == [Violation("$.schema[0].name", "'a__table': names are in snake_case")]


def test_a_column_name_is_in_snake_case(contract, column):
    column["name"] = "aColumn"
    assert validate_profile(contract) == [
        Violation("$.schema[0].properties[0].name", "'aColumn': names are in snake_case")
    ]


@pytest.mark.parametrize(("field", "value"), [("dataProduct", "a_product"), ("slaDefaultElement", "a_table.a_column")])
def test_a_deprecated_field_is_forbidden(contract, field, value):
    contract[field] = value
    assert validate_profile(contract) == [Violation(f"$.{field}", f"forbidden: {FORBIDDEN_FIELDS[field]}")]


def test_a_quality_check_uses_metric_not_rule(contract, column):
    column["quality"] = [{"type": "library", "metric": "nullValues", "rule": "nullCheck", "mustBe": 0}]
    assert validate_profile(contract) == [
        Violation("$.schema[0].properties[0].quality[0].rule", "forbidden: deprecated by ODCS, use metric")
    ]


def test_a_contract_has_no_price(contract):
    contract["price"] = {"priceAmount": 1, "priceCurrency": "EUR", "priceUnit": "megabyte"}
    assert validate_profile(contract) == [Violation("$.price", "forbidden: no rebilling process stands behind a price")]
