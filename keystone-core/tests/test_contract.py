"""Reading a contract file: plain data back, or a clear error."""

import pytest

from keystone_core import ContractLoadError, load_contract


def test_a_contract_file_gives_plain_data(tmp_path):
    path = tmp_path / "example.odcs.yaml"
    path.write_text("id: example\nversion: 1.0.0\n", encoding="utf-8")
    assert load_contract(path) == {"id": "example", "version": "1.0.0"}


def test_a_file_that_is_not_yaml_is_refused(tmp_path):
    path = tmp_path / "example.odcs.yaml"
    path.write_text("id: [unclosed\n", encoding="utf-8")
    with pytest.raises(ContractLoadError, match="not valid YAML"):
        load_contract(path)


def test_a_file_not_in_utf8_is_refused(tmp_path):
    path = tmp_path / "example.odcs.yaml"
    path.write_bytes("description: café\n".encode("latin-1"))
    with pytest.raises(ContractLoadError, match="not valid YAML"):
        load_contract(path)


def test_a_missing_file_is_refused(tmp_path):
    with pytest.raises(ContractLoadError, match="cannot read"):
        load_contract(tmp_path / "missing.odcs.yaml")
