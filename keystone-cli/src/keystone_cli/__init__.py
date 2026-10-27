"""The keystone command: check data contracts against ODCS."""

from pathlib import Path

import typer

from keystone_core import ContractLoadError, load_contract, validate

app = typer.Typer(help="Check data contracts against ODCS v3.2.0.", no_args_is_help=True)


# With a single command, Typer would run it without its name: this keeps "keystone validate".
@app.callback()
def keystone() -> None:
    pass


@app.command("validate", help="Check a data contract against ODCS v3.2.0.")
def validate_contract(contract: Path) -> None:
    try:
        violations = validate(load_contract(contract))
    except ContractLoadError as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(2)

    if not violations:
        typer.echo(f"Contract validated: {contract}")
        return
    typer.echo(f"Contract has errors: {contract}")
    for violation in violations:
        typer.echo(f"  {violation.path}: {violation.message}")
    raise typer.Exit(1)
