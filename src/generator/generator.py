"""
generator.py — Orchestrates config file generation from WizardState.
Calls all individual generators and reports what was written.
"""
from dataclasses import dataclass, field
from pathlib import Path
from rich.console import Console
from rich.table import Table

from wizard.state import WizardState
from generator import env_gen, openclaw_json_gen, exec_approvals_gen, compose_gen, restore_gen, backup_gen, workspace_bootstrap_gen, restore_config_gen

console = Console()


@dataclass
class GenerationResult:
    env_file: Path
    openclaw_json: Path
    exec_approvals: Path
    compose_file: Path = field(default_factory=Path)
    restore_script: Path = field(default_factory=Path)
    restore_config_script: Path = field(default_factory=Path)
    backup_script: Path = field(default_factory=Path)
    workspace_files: list = field(default_factory=list)
    image: str = ""
    success: bool = True


def _print_table(results: list) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    for status, name, _path, desc in results:
        table.add_row(status, f"[bold]{name}[/bold]", f"[dim]{desc}[/dim]")
    console.print(table)
    console.print()


def run(state: WizardState) -> GenerationResult:
    """Generate all config files. Returns GenerationResult."""
    console.print("\n[bold]Generating configuration files...[/bold]\n")

    results = []

    try:
        env_path = env_gen.write(state)
        results.append(("[green]✓[/green]", ".env", str(env_path), "secrets, LLM tiers"))
    except Exception as e:
        console.print(f"[red]✗ .env: {e}[/red]")
        return GenerationResult(Path(), Path(), Path(), success=False)

    try:
        json_path = openclaw_json_gen.write(state)
        results.append(("[green]✓[/green]", "openclaw.json", str(json_path), "gateway + channel config"))
    except Exception as e:
        console.print(f"[red]✗ openclaw.json: {e}[/red]")
        _print_table(results)
        return GenerationResult(env_path, Path(), Path(), success=False)

    try:
        approvals_path = exec_approvals_gen.write(state)
        results.append(("[green]✓[/green]", "exec-approvals.json", str(approvals_path), "security allowlist"))
    except Exception as e:
        console.print(f"[red]✗ exec-approvals.json: {e}[/red]")
        _print_table(results)
        return GenerationResult(env_path, json_path, Path(), success=False)

    # Fetch version + generate docker-compose.yml
    console.print("[dim]Fetching current OpenClaw release...[/dim]")
    image = compose_gen.fetch_latest_version()
    console.print(f"[dim]Pinning image: {image}[/dim]\n")

    try:
        compose_path = compose_gen.write(state, image)
        results.append(("[green]✓[/green]", "docker-compose.yml", str(compose_path), f"image: {image}"))
    except Exception as e:
        console.print(f"[red]✗ docker-compose.yml: {e}[/red]")
        _print_table(results)
        return GenerationResult(env_path, json_path, approvals_path, success=False)

    try:
        restore_path = restore_gen.write(state)
        results.append(("[green]✓[/green]", "restore_exec_approvals.py", str(restore_path), "exec-approvals restore script"))
    except Exception as e:
        console.print(f"[red]✗ restore_exec_approvals.py: {e}[/red]")
        _print_table(results)
        return GenerationResult(env_path, json_path, approvals_path, success=False)

    try:
        restore_config_path = restore_config_gen.write(state)
        results.append(("[green]✓[/green]", "restore_config.py", str(restore_config_path), "openclaw.json restore after update"))
    except Exception as e:
        console.print(f"[red]✗ restore_config.py: {e}[/red]")
        _print_table(results)
        return GenerationResult(env_path, json_path, approvals_path, success=False)

    try:
        backup_path = backup_gen.write(state)
        if backup_path:
            results.append(("[green]✓[/green]", "daily_backup.py", str(backup_path), f"backup → {state.backup_mount_path}"))
        else:
            results.append(("[dim]⏭[/dim]", "daily_backup.py", "", "skipped"))
            backup_path = Path()
    except Exception as e:
        console.print(f"[red]✗ daily_backup.py: {e}[/red]")
        _print_table(results)
        return GenerationResult(env_path, json_path, approvals_path, success=False)

    # Bootstrap workspace directory with template files
    try:
        workspace_paths = workspace_bootstrap_gen.write(state)
        results.append((
            "[green]\u2713[/green]",
            "workspace/",
            str(state.workspace_dir),
            f"{len(workspace_paths)} files (SOUL.md, AGENTS.md, HEARTBEAT.md \u2026)"
        ))
    except Exception as e:
        console.print(f"[red]\u2717 workspace bootstrap: {e}[/red]")
        _print_table(results)
        return GenerationResult(env_path, json_path, approvals_path, success=False)

    _print_table(results)

    return GenerationResult(
        env_file=env_path,
        openclaw_json=json_path,
        exec_approvals=approvals_path,
        compose_file=compose_path,
        restore_script=restore_path,
        restore_config_script=restore_config_path,
        backup_script=backup_path,
        workspace_files=workspace_paths,
        image=image,
        success=True,
    )
