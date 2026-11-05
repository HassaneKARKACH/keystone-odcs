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
        "slaProperties": [{"property": "frequency", "value": 1, "unit": "d"}],
        "schema": [
            {
                "name": "a_table",
                "physicalName": "a_table",
                "description": "One row per example.",
                "customProperties": [{"property": "loadMode", "vendor": "db-keystone", "value": "overwrite"}],
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


@pytest.fixture
def check(table):
    table["quality"] = [
        {
            "name": "a_table_is_not_empty",
            "severity": "error",
            "type": "sql",
            "query": "SELECT COUNT(*) FROM a_table",
            "mustBeGreaterThan": 0,
        }
    ]
    return table["quality"][0]


@pytest.fixture
def incremental(table):
    table["customProperties"] = [
        {"property": "loadMode", "vendor": "db-keystone", "value": "incremental"},
        {"property": "watermarkColumn", "vendor": "db-keystone", "value": "updated_at"},
    ]
    table["properties"].append({"name": "updated_at", "logicalType": "timestamp", "description": "Last change."})
    return table


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


def test_a_contract_has_no_price(contract):
    contract["price"] = {"priceAmount": 1, "priceCurrency": "EUR", "priceUnit": "megabyte"}
    assert validate_profile(contract) == [Violation("$.price", "forbidden: no rebilling process stands behind a price")]


def test_a_table_says_how_it_is_loaded(contract, table):
    del table["customProperties"]
    assert validate_profile(contract) == [
        Violation("$.schema[0].customProperties", "missing: a table says how it is loaded, in loadMode")
    ]


@pytest.mark.parametrize("vendor", ["db-keystone", "kafka-keystone"])
def test_a_load_mode_is_read_on_every_keystone_platform(contract, table, vendor):
    table["customProperties"][0]["vendor"] = vendor
    assert validate_profile(contract) == []


@pytest.mark.parametrize("vendor", ["another-tool", "keystone"])
def test_a_load_mode_signed_by_another_vendor_is_not_read(contract, table, vendor):
    table["customProperties"][0]["vendor"] = vendor
    assert validate_profile(contract) == [
        Violation("$.schema[0].customProperties", "missing: a table says how it is loaded, in loadMode")
    ]


def test_the_load_mode_is_append_overwrite_or_incremental(contract, table):
    table["customProperties"][0]["value"] = "merge"
    assert validate_profile(contract) == [
        Violation("$.schema[0].customProperties", "'merge': loadMode is append, overwrite or incremental")
    ]


def test_an_incremental_table_passes(contract, incremental):
    assert validate_odcs(contract) == []
    assert validate_profile(contract) == []


def test_an_incremental_table_has_a_primary_key(contract, incremental, column):
    column["primaryKey"] = False
    assert validate_profile(contract) == [
        Violation("$.schema[0].properties", "no primary key: an incremental load merges rows on it")
    ]


def test_an_incremental_table_names_its_watermark(contract, incremental):
    incremental["customProperties"].pop()
    assert validate_profile(contract) == [
        Violation("$.schema[0].customProperties", "missing: an incremental load names its watermarkColumn")
    ]


def test_the_watermark_is_a_column_of_the_table(contract, incremental):
    incremental["customProperties"][1]["value"] = "another_column"
    assert validate_profile(contract) == [
        Violation("$.schema[0].customProperties", "'another_column': watermarkColumn is a column of the table")
    ]


def test_the_watermark_is_a_date_or_a_timestamp(contract, incremental):
    incremental["properties"][1]["logicalType"] = "string"
    assert validate_profile(contract) == [
        Violation("$.schema[0].customProperties", "'updated_at': a watermark column is a date or a timestamp")
    ]


def test_a_contract_says_how_often_its_table_is_loaded(contract):
    del contract["slaProperties"]
    assert validate_profile(contract) == [
        Violation("$.slaProperties", "missing: a contract says how often its table is loaded")
    ]


def test_a_frequency_has_a_unit(contract):
    del contract["slaProperties"][0]["unit"]
    assert validate_profile(contract) == [Violation("$.slaProperties[0].unit", "missing: a frequency has a unit")]


@pytest.mark.parametrize("element", ["a_column", "a_table.a_column"])
def test_a_latency_is_measured_on_a_column_of_the_table(contract, element):
    contract["slaProperties"].append({"property": "latency", "value": 4, "unit": "h", "element": element})
    assert validate_profile(contract) == []


def test_a_latency_names_its_column(contract):
    contract["slaProperties"].append({"property": "latency", "value": 4, "unit": "h"})
    assert validate_profile(contract) == [
        Violation("$.slaProperties[1].element", "missing: a latency is measured on a column")
    ]


def test_a_latency_column_exists(contract):
    contract["slaProperties"].append({"property": "latency", "value": 4, "unit": "h", "element": "another_column"})
    assert validate_profile(contract) == [
        Violation("$.slaProperties[1].element", "'another_column': not a column of the table")
    ]


def test_an_sql_check_passes(contract, check):
    assert validate_odcs(contract) == []
    assert validate_profile(contract) == []


def test_a_quality_check_says_type_sql(contract, table):
    # Without a type, ODCS reads a check as library.
    table["quality"] = [{"name": "a_check", "severity": "error", "metric": "rowCount", "mustBeGreaterThan": 0}]
    assert validate_profile(contract) == [
        Violation("$.schema[0].quality[0].type", "missing: a quality check says type: sql")
    ]


@pytest.mark.parametrize(
    "written",
    [
        {"type": "library", "metric": "rowCount", "mustBeGreaterThan": 0},
        {"type": "text", "description": "The table is never empty."},
        {"type": "custom", "engine": "soda", "implementation": "row_count > 0"},
    ],
)
def test_a_quality_check_is_in_sql(contract, table, written):
    table["quality"] = [{"name": "a_check", "severity": "error", **written}]
    assert validate_odcs(contract) == []
    assert validate_profile(contract) == [
        Violation("$.schema[0].quality[0].type", f"'{written['type']}': a quality check is in SQL, type: sql")
    ]


def test_a_quality_check_has_a_name(contract, check):
    del check["name"]
    assert validate_profile(contract) == [
        Violation("$.schema[0].quality[0].name", "missing: a quality check has a name")
    ]


def test_a_column_check_follows_the_same_rules(contract, table, column, check):
    column["quality"] = table.pop("quality")
    del check["name"]
    assert validate_profile(contract) == [
        Violation("$.schema[0].properties[0].quality[0].name", "missing: a quality check has a name")
    ]


def test_a_quality_check_says_if_a_failure_warns_or_stops(contract, check):
    del check["severity"]
    assert validate_profile(contract) == [
        Violation("$.schema[0].quality[0].severity", "missing: a quality check says if a failure warns or stops")
    ]


def test_the_severity_is_warning_or_error(contract, check):
    check["severity"] = "info"
    assert validate_profile(contract) == [
        Violation("$.schema[0].quality[0].severity", "'info': severity is warning or error")
    ]
