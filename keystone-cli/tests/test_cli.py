"""The keystone command, run as a user would."""

import pytest
from typer.testing import CliRunner

from keystone_cli import app

CONTRACT = "apiVersion: v3.2.0\nkind: DataContract\nid: example\nversion: 1.0.0\n"
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


def test_validate_lists_the_violations_and_exits_1(path):
    path.write_text(CONTRACT.replace("id: example\n", ""), encoding="utf-8")
    result = keystone("validate", path)
    assert result.exit_code == 1
    assert result.output == f"Contract has errors: {path}\n  $: 'id' is a required property\n"


def test_validate_exits_2_when_the_file_cannot_be_read(tmp_path):
    result = keystone("validate", tmp_path / "missing.odcs.yaml")
    assert result.exit_code == 2
    assert "cannot read" in result.stderr
