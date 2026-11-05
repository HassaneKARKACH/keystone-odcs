"""The keystone command, run as a user would."""

import pytest
from typer.testing import CliRunner

from keystone_cli import app

CONTRACT = """\
apiVersion: v3.2.0
kind: DataContract
id: a_table
name: a_table
version: 1.0.0
domain: example
status: active
team:
  name: a_team
  members:
    - username: a_user
      role: owner
slaProperties:
  - property: frequency
    value: 1
    unit: d
schema:
  - name: a_table
    physicalName: a_table
    description: One row per example.
    customProperties:
      - property: loadMode
        vendor: db-keystone
        value: overwrite
    properties:
      - name: a_column
        logicalType: string
        description: The key of an example.
"""
runner = CliRunner()


def keystone(*words):
    return runner.invoke(app, [str(word) for word in words])


@pytest.fixture
def path(tmp_path):
    path = tmp_path / "example.odcs.yaml"
    path.write_text(CONTRACT, encoding="utf-8")
    return path


def test_validate_says_the_contract_is_validated(path):
    result = keystone("validate", path)
    assert result.exit_code == 0
    assert result.output == f"Contract validated: {path}\n"


def test_validate_lists_the_odcs_violations_and_exits_1(path):
    path.write_text(CONTRACT.replace("id: a_table\n", ""), encoding="utf-8")
    result = keystone("validate", path)
    assert result.exit_code == 1
    assert result.output == f"Contract is not valid ODCS: {path}\n  $: 'id' is a required property\n"


def test_validate_lists_the_keystone_violations_and_exits_1(path):
    path.write_text(CONTRACT.replace("status: active\n", "status: proposed\n"), encoding="utf-8")
    result = keystone("validate", path)
    assert result.exit_code == 1
    assert result.output == (
        f"Contract breaks the Keystone profile: {path}\n"
        "  $.status: 'proposed': a status is draft, active or deprecated\n"
    )


def test_validate_exits_2_when_the_file_cannot_be_read(tmp_path):
    result = keystone("validate", tmp_path / "missing.odcs.yaml")
    assert result.exit_code == 2
    assert "cannot read" in result.stderr
