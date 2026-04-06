"""
generator.py — Orchestrates config file generation from WizardState.
Calls all individual generators and reports what was written.
"""
from dataclasses import dataclass
from pathlib import Path
from rich.console import Console
from rich.table import Table

from wizard.state import WizardState
from generator import env_gen, openclaw_json_gen, exec_approvals_gen

console = Console()


@dataclass
class GenerationResult:
    env_file: Path
    openclaw_json: Path
    exec_approvals: Path
    success: bool = True


def run(state: WizardState) -> GenerationResult:
    """Generate all config files. Returns GenerationResult."""
    console.print("\n[bold]Generating configuration files...[/bold]\n")

    results = []

    try:
        env_path = env_gen.write(state)
        results.append(("[green]✓[/green]", ".env", str(env_path), "secrets, LLM tiers"))
    except Exception as e:
        results.append(("[red]✗[/red]", ".env", "FAILED", str(e)))
        return GenerationResult(Path(), Path(), Path(), success=False)

    try:
        json_path = openclaw_json_gen.write(state)
        results.append(("[green]✓[/green]", "openclaw.json", str(json_path), "gateway + channel config"))
    except Exception as e:
        results.append(("[red]✗[/red]", "openclaw.json", "FAILED", str(e)))
        return GenerationResult(env_path, Path(), Path(), success=False)

    try:
        approvals_path = exec_approvals_gen.write(state)
        results.append(("[green]✓[/green]", "exec-approvals.json", str(approvals_path), "security allowlist"))
    except Exception as e:
        results.append(("[red]✗[/red]", "exec-approvals.json", "FAILED", str(e)))
        return GenerationResult(env_path, json_path, Path(), success=False)

    # Summary table
    table = Table(show_header=False, box=None, padding=(0, 2))
    for status, name, path, desc in results:
        table.add_row(status, f"[bold]{name}[/bold]", f"[dim]{desc}[/dim]")
    console.print(table)
    console.print()

    return GenerationResult(
        env_file=env_path,
        openclaw_json=json_path,
        exec_approvals=approvals_path,
        success=True,
    )
