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


def validate_profile(contract: dict) -> list[Violation]:
    """Return every Keystone violation of a valid ODCS contract, in the order of the rules."""
    found = []
    # Required fields.
    _contract_fields(contract, found)
    _team(contract, found)
    _one_table(contract, found)
    _table_fields(contract, found)
    _column_fields(contract, found)
    # Allowed values.
    _status(contract, found)
    # Consistency.
    _one_name(contract, found)
    _table_id(contract, found)
    _primary_key(contract, found)
    # Naming.
    _snake_case(contract, found)
    # Forbidden fields.
    _forbidden_fields(contract, found)
    _quality_rule(contract, found)
    return found


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


def _status(contract: dict, found: list[Violation]) -> None:
    # ODCS leaves the status free: each value kept here tells a consumer what to do.
    status = contract.get("status")
    if status is not None and status not in STATUSES:
        found.append(Violation("$.status", f"'{status}': a status is draft, active or deprecated"))


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


def _snake_case(contract: dict, found: list[Violation]) -> None:
    # The contract id and the physical name of the table are the contract name: checked with it.
    names = [("$.name", contract.get("name"))]
    names += [(f"{path}.name", table["name"]) for table, path in _tables(contract)]
    names += [(f"{path}.name", column["name"]) for column, path in _columns(contract)]
    for path, name in names:
        if name is not None and not SNAKE_CASE.fullmatch(name):
            found.append(Violation(path, f"'{name}': names are in snake_case"))


def _forbidden_fields(contract: dict, found: list[Violation]) -> None:
    for field, why in FORBIDDEN_FIELDS.items():
        if field in contract:
            found.append(Violation(f"$.{field}", f"forbidden: {why}"))


def _quality_rule(contract: dict, found: list[Violation]) -> None:
    # ODCS has deprecated rule in a library check: metric, already required, says the same.
    for element, path in [*_tables(contract), *_columns(contract)]:
        for i, check in enumerate(element.get("quality", [])):
            if "rule" in check:
                found.append(Violation(f"{path}.quality[{i}].rule", "forbidden: deprecated by ODCS, use metric"))


def _tables(contract: dict):
    """Every table of the contract, with its path."""
    for i, table in enumerate(contract.get("schema", [])):
        yield table, f"$.schema[{i}]"


def _columns(contract: dict):
    """Every column of every table, with its path. The properties nested in a column are not columns."""
    for table, path in _tables(contract):
        for i, column in enumerate(table.get("properties", [])):
            yield column, f"{path}.properties[{i}]"
