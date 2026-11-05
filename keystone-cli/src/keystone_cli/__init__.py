"""The keystone command: check data contracts against ODCS and the Keystone profile."""

from pathlib import Path
from typing import NoReturn

import typer

from keystone_core import ContractLoadError, Violation, load_contract, validate_odcs, validate_profile

app = typer.Typer(help="Check data contracts against ODCS v3.2.0 and the Keystone profile.", no_args_is_help=True)


# With a single command, Typer would run it without its name: this keeps "keystone validate".
@app.callback()
def keystone() -> None:
    pass


@app.command("validate", help="Check a data contract against ODCS v3.2.0, then the Keystone profile.")
def validate_contract(contract: Path) -> None:
    try:
        data = load_contract(contract)
    except ContractLoadError as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(2)

    violations = validate_odcs(data)
    if violations:
        fail(f"Contract is not valid ODCS: {contract}", violations)
    # The profile rules assume a valid ODCS contract: they only run once ODCS passes.
    violations = validate_profile(data)
    if violations:
        fail(f"Contract breaks the Keystone profile: {contract}", violations)
    typer.echo(f"Contract validated: {contract}")


def fail(title: str, violations: list[Violation]) -> NoReturn:
    typer.echo(title)
    for violation in violations:
        typer.echo(f"  {violation.path}: {violation.message}")
    raise typer.Exit(1)
