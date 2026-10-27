"""Read a contract file into plain data."""

from pathlib import Path

from ruamel.yaml import YAML, YAMLError


class ContractLoadError(Exception):
    """The contract file cannot be read or is not valid YAML."""


def load_contract(path: Path) -> object:
    """Read a contract file (YAML or JSON)."""
    try:
        return YAML(typ="safe").load(path)
    except OSError as error:
        raise ContractLoadError(f"cannot read {path}: {error.strerror}") from error
    except YAMLError as error:
        raise ContractLoadError(f"{path} is not valid YAML: {error}") from error
