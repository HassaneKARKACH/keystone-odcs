"""Keystone check: the rules of the Keystone profile, on top of ODCS.

Every rule reads a contract that has already passed the ODCS check: the id and the names
of tables and columns are there, and every field has its ODCS type.
"""

import re

from keystone_core.validation import Violation

# What each required field tells a reader of the contract.
CONTRACT_FIELDS = {
    "name": "a contract is named after its table",
    "domain": "a contract belongs to a business domain",
    "status": "a contract says whether it can be relied on",
    "team": "a contract names the team that answers for it",
    "schema": "a contract describes its table",
}
TABLE_FIELDS = {
    "physicalName": "a table gives its name in the database",
    "description": "a table says what one row stands for",
}
COLUMN_FIELDS = {
    "logicalType": "a column gives the type of its values",
    "description": "a column says what it holds",
}
STATUSES = ("draft", "active", "deprecated")
# Lower case letters and digits, words joined by a single underscore.
SNAKE_CASE = re.compile(r"[a-z][a-z0-9]*(_[a-z0-9]+)*")
# The contract fields the profile forbids, and why. A deprecated field would break the
# contract the day ODCS removes it.
FORBIDDEN_FIELDS = {
    "dataProduct": "deprecated since ODCS 3.1.0",
    "slaDefaultElement": "deprecated since ODCS 3.1.0, to be removed in 4.0: use element in slaProperties",
    "price": "no rebilling process stands behind a price",
}
LOAD_MODES = ("append", "overwrite", "incremental")
# A watermark is the time of the last change of a row.
WATERMARK_TYPES = ("date", "timestamp")
# What a failed quality check does: warn, or stop the load.
SEVERITIES = ("warning", "error")


def validate_profile(contract: dict) -> list[Violation]:
    """Return every Keystone violation of a valid ODCS contract, in the order of the rules."""
    found = []
    # Axis 1: refine.
    _contract_fields(contract, found)
    _team(contract, found)
    _one_table(contract, found)
    _table_fields(contract, found)
    _column_fields(contract, found)
    _status(contract, found)
    _one_name(contract, found)
    _table_id(contract, found)
    _primary_key(contract, found)
    _snake_case(contract, found)
    # Axis 2: forbid.
    _forbidden_fields(contract, found)
    # Axis 3: data processing.
    _load_mode(contract, found)
    _incremental(contract, found)
    _frequency(contract, found)
    _sla_units(contract, found)
    _latency_element(contract, found)
    # Axis 4: data quality.
    _sql_checks(contract, found)
    _check_names(contract, found)
    _check_severity(contract, found)
    return found


# ======================================================================
# Axis 1: refine. Required fields, allowed values, consistency, naming.
# ======================================================================


# Required fields: what a contract, its table and its columns must say.


def _contract_fields(contract: dict, found: list[Violation]) -> None:
    for field, why in CONTRACT_FIELDS.items():
        if field not in contract:
            found.append(Violation(f"$.{field}", f"missing: {why}"))


def _team(contract: dict, found: list[Violation]) -> None:
    # ODCS has no owner field: a member with the role owner stands for it.
    team = contract.get("team")
    if team is None:
        return
    if isinstance(team, list):
        found.append(Violation("$.team", "a list of members: a team is an object, the list is deprecated"))
        return
    if "name" not in team:
        found.append(Violation("$.team.name", "missing: a team has a name"))
    if not any(member.get("role") == "owner" for member in team.get("members", [])):
        found.append(Violation("$.team.members", "no member with role: owner"))


def _one_table(contract: dict, found: list[Violation]) -> None:
    # ODCS takes a list of tables. The contract id is the name of one table.
    tables = contract.get("schema")
    if tables is not None and len(tables) != 1:
        found.append(Violation("$.schema", f"{len(tables)} tables: a contract describes exactly one"))


def _table_fields(contract: dict, found: list[Violation]) -> None:
    for table, path in _tables(contract):
        for field, why in TABLE_FIELDS.items():
            if field not in table:
                found.append(Violation(f"{path}.{field}", f"missing: {why}"))


def _column_fields(contract: dict, found: list[Violation]) -> None:
    for column, path in _columns(contract):
        for field, why in COLUMN_FIELDS.items():
            if field not in column:
                found.append(Violation(f"{path}.{field}", f"missing: {why}"))


# Allowed values: what ODCS leaves free and the profile closes.


def _status(contract: dict, found: list[Violation]) -> None:
    # ODCS leaves the status free: each value kept here tells a consumer what to do.
    status = contract.get("status")
    if status is not None and status not in STATUSES:
        found.append(Violation("$.status", f"'{status}': a status is draft, active or deprecated"))


# Consistency: fields that must agree with each other.


def _one_name(contract: dict, found: list[Violation]) -> None:
    # A contract is found by the name of its table: its id, its name and the table's
    # physical name are one and the same.
    name = contract.get("name")
    if name is not None and name != contract["id"]:
        found.append(Violation("$.name", f"'{name}': the name of a contract is its id, '{contract['id']}'"))
    for table, path in _tables(contract):
        physical_name = table.get("physicalName")
        if physical_name is not None and physical_name != contract["id"]:
            found.append(
                Violation(
                    f"{path}.physicalName",
                    f"'{physical_name}': the physical name of the table is the contract id, '{contract['id']}'",
                )
            )


def _table_id(contract: dict, found: list[Violation]) -> None:
    # ODCS points at a column either by names or by ids: both then lead to the same place.
    for table, path in _tables(contract):
        if "id" in table and table["id"] != table["name"]:
            found.append(Violation(f"{path}.id", f"'{table['id']}': the id of a table is its name, '{table['name']}'"))


def _primary_key(contract: dict, found: list[Violation]) -> None:
    # ODCS does not tie the two, and required is false by default: a key could be null.
    for column, path in _columns(contract):
        if column.get("primaryKey") and not column.get("required"):
            found.append(Violation(f"{path}.required", f"'{column['name']}' is in the primary key: required: true"))


# Naming: how a contract, its table and its columns are named.


def _snake_case(contract: dict, found: list[Violation]) -> None:
    # The contract id and the physical name of the table are the contract name: checked with it.
    names = [("$.name", contract.get("name"))]
    names += [(f"{path}.name", table["name"]) for table, path in _tables(contract)]
    names += [(f"{path}.name", column["name"]) for column, path in _columns(contract)]
    for path, name in names:
        if name is not None and not SNAKE_CASE.fullmatch(name):
            found.append(Violation(path, f"'{name}': names are in snake_case"))


# ======================================================================
# Axis 2: forbid. The fields a contract must do without.
# ======================================================================


def _forbidden_fields(contract: dict, found: list[Violation]) -> None:
    for field, why in FORBIDDEN_FIELDS.items():
        if field in contract:
            found.append(Violation(f"$.{field}", f"forbidden: {why}"))


# ======================================================================
# Axis 3: data processing. How the table is loaded.
# ======================================================================


def _load_mode(contract: dict, found: list[Violation]) -> None:
    # ODCS has no word for it: how the rows change is what a consumer needs to read the table right.
    for table, path in _tables(contract):
        mode = _keystone(table).get("loadMode")
        if mode is None:
            found.append(Violation(f"{path}.customProperties", "missing: a table says how it is loaded, in loadMode"))
        elif mode not in LOAD_MODES:
            found.append(
                Violation(f"{path}.customProperties", f"'{mode}': loadMode is append, overwrite or incremental")
            )


def _incremental(contract: dict, found: list[Violation]) -> None:
    # An incremental load reads the rows changed since the last load, then merges them on the key.
    for table, path in _tables(contract):
        keystone = _keystone(table)
        if keystone.get("loadMode") != "incremental":
            continue
        columns = table.get("properties", [])
        if not any(column.get("primaryKey") for column in columns):
            found.append(Violation(f"{path}.properties", "no primary key: an incremental load merges rows on it"))
        watermark = keystone.get("watermarkColumn")
        column = next((column for column in columns if column["name"] == watermark), None)
        where = f"{path}.customProperties"
        if watermark is None:
            found.append(Violation(where, "missing: an incremental load names its watermarkColumn"))
        elif column is None:
            found.append(Violation(where, f"'{watermark}': watermarkColumn is a column of the table"))
        elif "logicalType" in column and column["logicalType"] not in WATERMARK_TYPES:
            found.append(Violation(where, f"'{watermark}': a watermark column is a date or a timestamp"))


def _frequency(contract: dict, found: list[Violation]) -> None:
    # Every load has a rhythm: saying it costs nothing and tells a consumer when to come back.
    if not any(item["property"] == "frequency" for item in contract.get("slaProperties", [])):
        found.append(Violation("$.slaProperties", "missing: a contract says how often its table is loaded"))


def _sla_units(contract: dict, found: list[Violation]) -> None:
    # "1" says nothing without a unit, and ODCS does not require one.
    for i, item in enumerate(contract.get("slaProperties", [])):
        if item["property"] in ("frequency", "latency") and "unit" not in item:
            found.append(Violation(f"$.slaProperties[{i}].unit", f"missing: a {item['property']} has a unit"))


def _latency_element(contract: dict, found: list[Violation]) -> None:
    # A delay is measured on a column. With one table, ODCS lets the table name go.
    columns = set()
    for table, _ in _tables(contract):
        for column in table.get("properties", []):
            columns |= {column["name"], f"{table['name']}.{column['name']}"}
    for i, item in enumerate(contract.get("slaProperties", [])):
        if item["property"] != "latency":
            continue
        if "element" not in item:
            found.append(Violation(f"$.slaProperties[{i}].element", "missing: a latency is measured on a column"))
        elif item["element"] not in columns:
            found.append(Violation(f"$.slaProperties[{i}].element", f"'{item['element']}': not a column of the table"))


# ======================================================================
# Axis 4: data quality. Every check is an SQL query, named and graded.
# ======================================================================


def _sql_checks(contract: dict, found: list[Violation]) -> None:
    # The engine that runs the checks reads SQL. ODCS reads a check without a type as library.
    for check, path in _quality_checks(contract):
        if "type" not in check:
            found.append(Violation(f"{path}.type", "missing: a quality check says type: sql"))
        elif check["type"] != "sql":
            found.append(Violation(f"{path}.type", f"'{check['type']}': a quality check is in SQL, type: sql"))


def _check_names(contract: dict, found: list[Violation]) -> None:
    # An alert names the check that failed.
    for check, path in _quality_checks(contract):
        if "name" not in check:
            found.append(Violation(f"{path}.name", "missing: a quality check has a name"))


def _check_severity(contract: dict, found: list[Violation]) -> None:
    # A failed check warns or stops the load: info would do neither.
    for check, path in _quality_checks(contract):
        if "severity" not in check:
            found.append(Violation(f"{path}.severity", "missing: a quality check says if a failure warns or stops"))
        elif check["severity"] not in SEVERITIES:
            found.append(Violation(f"{path}.severity", f"'{check['severity']}': severity is warning or error"))


# ======================================================================
# Tools: walking through the contract.
# ======================================================================


def _tables(contract: dict):
    """Every table of the contract, with its path."""
    for i, table in enumerate(contract.get("schema", [])):
        yield table, f"$.schema[{i}]"


def _columns(contract: dict):
    """Every column of every table, with its path. The properties nested in a column are not columns."""
    for table, path in _tables(contract):
        for i, column in enumerate(table.get("properties", [])):
            yield column, f"{path}.properties[{i}]"


def _quality_checks(contract: dict):
    """Every quality check of the tables and their columns, with its path."""
    for element, path in [*_tables(contract), *_columns(contract)]:
        for i, check in enumerate(element.get("quality", [])):
            yield check, f"{path}.quality[{i}]"


def _keystone(element: dict) -> dict:
    """The custom properties of an element that Keystone signs, by name."""
    # One vendor per platform, as db-keystone or kafka-keystone.
    return {
        custom["property"]: custom["value"]
        for custom in element.get("customProperties", [])
        if custom.get("vendor", "").endswith("-keystone")
    }
