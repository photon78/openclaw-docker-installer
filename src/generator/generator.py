"""
generator.py — Orchestrates config file generation from WizardState.
Calls all individual generators and reports what was written.
"""
from dataclasses import dataclass, field
from pathlib import Path
from rich.console import Console
from rich.table import Table

from wizard.state import WizardState
from generator import env_gen, openclaw_json_gen, exec_approvals_gen, compose_gen, restore_gen, backup_gen

console = Console()


@dataclass
class GenerationResult:
    env_file: Path
    openclaw_json: Path
    exec_approvals: Path
    compose_file: Path = field(default_factory=Path)
    restore_script: Path = field(default_factory=Path)
    backup_script: Path = field(default_factory=Path)
    image: str = ""
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

    # Fetch version + generate docker-compose.yml
    console.print("[dim]Fetching current OpenClaw release...[/dim]")
    image = compose_gen.fetch_latest_version()
    console.print(f"[dim]Pinning image: {image}[/dim]\n")

    try:
        compose_path = compose_gen.write(state, image)
        results.append(("[green]✓[/green]", "docker-compose.yml", str(compose_path), f"image: {image}"))
    except Exception as e:
        results.append(("[red]✗[/red]", "docker-compose.yml", "FAILED", str(e)))
        return GenerationResult(env_path, json_path, approvals_path, success=False)

    # Summary table
    table = Table(show_header=False, box=None, padding=(0, 2))
    for status, name, path, desc in results:
        table.add_row(status, f"[bold]{name}[/bold]", f"[dim]{desc}[/dim]")
    console.print(table)
    console.print()

    # Generate restore_exec_approvals.py
    try:
        restore_path = restore_gen.write(state)
        results.append(("[green]✓[/green]", "restore_exec_approvals.py", str(restore_path), "exec-approvals restore script"))
    except Exception as e:
        results.append(("[red]✗[/red]", "restore_exec_approvals.py", "FAILED", str(e)))
        return GenerationResult(env_path, json_path, approvals_path, success=False)

    # Generate daily_backup.py
    try:
        backup_path = backup_gen.write(state)
        results.append(("[green]✓[/green]", "daily_backup.py", str(backup_path), f"backup → {state.backup_mount_path or '/mnt/backup'}"))
    except Exception as e:
        results.append(("[red]✗[/red]", "daily_backup.py", "FAILED", str(e)))
        return GenerationResult(env_path, json_path, approvals_path, success=False)

    return GenerationResult(
        env_file=env_path,
        openclaw_json=json_path,
        exec_approvals=approvals_path,
        compose_file=compose_path,
        restore_script=restore_path,
        backup_script=backup_path,
        image=image,
        success=True,
    )
