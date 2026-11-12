"""Simulate a data catalog that uses keystone-core to vet the contracts of the Cyclomatic data lake.

The catalog registers a contract only when it passes ODCS and the Keystone profile. It then reads
the domain, the status and the owner without checking them: the profile guarantees them.

Run from the root of the repository: uv run python examples/simulate.py
"""

from pathlib import Path

from keystone_core import load_contract, validate_odcs, validate_profile

CONTRACTS = Path(__file__).with_name("cyclomatic")
FOLDERS = ("ingestion", "data-products", "invalid")


def check(contract: object) -> list[str]:
    """The reasons to refuse a contract: its ODCS errors, or else its Keystone errors."""
    # The profile rules assume a valid ODCS contract.
    errors = [f"ODCS {violation.path}: {violation.message}" for violation in validate_odcs(contract)]
    return errors or [f"Keystone {violation.path}: {violation.message}" for violation in validate_profile(contract)]


def owner(contract: dict) -> str:
    return next(member["username"] for member in contract["team"]["members"] if member.get("role") == "owner")


catalog = []
for folder in FOLDERS:
    for path in sorted((CONTRACTS / folder).glob("*.odcs.yaml")):
        contract = load_contract(path)
        errors = check(contract)
        print(f"{'rejected' if errors else 'accepted'}  {folder}/{path.name}")
        for error in errors:
            print(f"    {error}")
        if not errors:
            catalog.append((folder, contract))

print(f"\nCatalog: {len(catalog)} contracts")
for folder, contract in catalog:
    print(f"  {folder:<14} {contract['id']:<20} {contract['domain']:<10} {contract['status']:<11} {owner(contract)}")
