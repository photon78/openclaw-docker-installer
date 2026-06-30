#!/usr/bin/env python3
"""
safe_exec_check.py — Pre-flight check for OpenClaw exec tool commands.

SCRIPT-META:
  agent: shared
  type: utility
  risk: low
  description: "Pre-flight exec safety check — blocks pipes, chaining, redirects, subshells, globs"

Blocks shell constructs that are forbidden by workspace policy:
- pipes (|)
- command chaining (&&, ||, ;)
- redirections (>, >>, <, 2>&1, etc.)
- subshells and command substitution ($(), backticks, ${...})
- globs/wildcards (*, ?) unless in an allowlisted full command
- process substitution (<(), >())
- backgrounding (&)
- newlines and command terminators

Usage:
    python3 safe_exec_check.py "ls -la /tmp"
    python3 safe_exec_check.py --allowlist ~/.openclaw/workspace/skills/safe-exec/examples/allowlist.txt "cat /etc/passwd"
    echo "ls -la" | python3 safe_exec_check.py

Exit codes:
    0  command passes safety checks
    1  command is unsafe or arguments are invalid
    2  configuration/IO error
"""

import argparse
import re
import shlex
import sys
from pathlib import Path


DEFAULT_ALLOWED_COMMANDS: set[str] = {
    "cat",
    "cd",
    "cp",
    "echo",
    "git",
    "grep",
    "head",
    "id",
    "ls",
    "mkdir",
    "mv",
    "openclaw",
    "pgrep",
    "pwd",
    "python3",
    "read",
    "rm",
    "sed",
    "ssh",
    "tail",
    "tar",
    "test",
    "touch",
    "tr",
    "trash",
    "wc",
    "which",
}

# Shell builtins we allow as base commands even though they are not in $PATH.
ALLOWED_BUILTINS: set[str] = {"cd", "source", "."}

# Commands that must be allowed explicitly; they are dangerous enough that a
# generic structural check is not enough.
REQUIRES_EXPLICIT_ALLOW: set[str] = {"rm", "ssh", "mv"}


# Patterns that always make a command unsafe.
DANGEROUS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Command chaining / sequencing
    (re.compile(r"[;&]"), "command chaining/sequencing (; or &)"),
    (re.compile(r"\|\|"), "logical OR chaining (||)"),
    (re.compile(r"&&"), "logical AND chaining (&&)"),
    # Pipe (but not || which is handled above)
    (re.compile(r"(?<!\|)\|(?!\|)"), "pipe (|)"),
    # Redirections
    (re.compile(r"\d?\s*>\s*"), "output redirection (>)"),
    (re.compile(r"\d?\s*<\s*"), "input redirection (<)"),
    (re.compile(r"\d+\s*>&\s*\d+"), "file descriptor redirect (2>&1)"),
    # Process substitution
    (re.compile(r"[<>]\("), "process substitution (<() or >())"),
    # Command substitution
    (re.compile(r"\$\("), "command substitution ($(...))"),
    (re.compile(r"`"), "command substitution (backtick)"),
    # Expansion/globbing
    (re.compile(r"(?<!\\)\*"), "glob wildcard (*)"),
    (re.compile(r"(?<!\\)\?"), "glob wildcard (?)"),
    (re.compile(r"\$\{"), "parameter expansion (${...})"),
    (re.compile(r"\$\("), "arithmetic/command expansion ($((...)))"),
    # Common one-shot code execution vectors
    (re.compile(r"\bpython3?\s+-c\b"), "inline Python code (-c)"),
    (re.compile(r"\bbash\s+-c\b"), "inline Bash code (bash -c)"),
    (re.compile(r"\bsh\s+-c\b"), "inline shell code (sh -c)"),
    # Backgrounding
    (re.compile(r"(?<!&)\&(?!&)"), "backgrounding (&)"),
]


def load_list(path: Path | None) -> set[str]:
    """Load a newline-separated list from a file."""
    items: set[str] = set()
    if path is None or not path.exists():
        return items
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    items.add(line)
    except OSError as exc:
        print(f"ERROR: cannot read list file {path}: {exc}", file=sys.stderr)
        sys.exit(2)
    return items


def _tokenize(command: str) -> list[str]:
    """Tokenize a command string using shell rules."""
    try:
        return shlex.split(command, comments=False)
    except ValueError as exc:
        raise ValueError(f"Malformed command (unbalanced quotes?): {exc}") from exc


def _check_dangerous_tokens(command: str) -> list[str]:
    """Return list of reasons why the command is dangerous."""
    reasons: list[str] = []

    # Very common mistake: agents type "run <cmd>" because they confuse the
    # OpenClaw instruction with a shell command.
    if command.lstrip().startswith(("run ", "run\t")):
        reasons.append(
            "'run' is not a shell command — pass only the command, "
            'e.g. python3 safe_exec_check.py "ls -la"'
        )

    # Newlines are command separators too.
    if "\n" in command or "\r" in command:
        reasons.append("newline/CR in command (multiple commands)")

    # Tokenize conservatively; if we cannot tokenize, we cannot validate.
    try:
        tokens = _tokenize(command)
    except ValueError as exc:
        reasons.append(str(exc))
        return reasons

    if not tokens:
        reasons.append("empty command")
        return reasons

    # Check the raw command string for dangerous patterns.  We do this on the
    # raw string so we can catch constructs that shlex may have normalized.
    for pattern, description in DANGEROUS_PATTERNS:
        if pattern.search(command):
            reasons.append(description)

    return reasons


def _check_base_command_exists(command: str) -> str | None:
    """Return a warning if the base command does not exist or is not allowed."""
    import shutil

    tokens = _tokenize(command)
    if not tokens:
        return None

    base = Path(tokens[0]).name

    # Shell builtins that do not exist as binaries are fine.
    if base in ALLOWED_BUILTINS:
        return None

    # If the command is an absolute or relative path, require that it exists.
    if "/" in tokens[0]:
        if not Path(tokens[0]).exists():
            return f"command path does not exist: {tokens[0]}"
        return None

    # Otherwise it must be resolvable via PATH.
    if shutil.which(base) is None:
        return f"command not found in PATH: {base}"
    return None


def _command_in_allowlist(command: str, allowlist: set[str]) -> bool:
    """Return True if the exact full command is in the allowlist."""
    normalized = command.strip()
    return normalized in allowlist


def _matches_blocklist(command: str, blocklist: set[str]) -> str | None:
    """Return first matching blocklist reason, or None."""
    for entry in blocklist:
        if entry in command:
            return entry
    return None


def _extract_base_command(command: str) -> str:
    """Return the base command name (first token)."""
    tokens = _tokenize(command)
    if not tokens:
        return ""
    return Path(tokens[0]).name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check whether an OpenClaw exec command is safe to run."
    )
    parser.add_argument(
        "command",
        nargs="?",
        help="Command string to check. If omitted, read from stdin.",
    )
    parser.add_argument(
        "--allowlist",
        type=Path,
        metavar="FILE",
        help="Path to a file containing fully allowed command strings (one per line).",
    )
    parser.add_argument(
        "--blocklist",
        type=Path,
        metavar="FILE",
        help="Path to a file containing forbidden substrings (one per line).",
    )
    parser.add_argument(
        "--require-allowlist",
        action="store_true",
        help="Reject any command whose base command is not in the allowlist.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed OK/ERROR messages.",
    )

    args = parser.parse_args(argv)

    # Read command
    if args.command is None:
        try:
            command = sys.stdin.read()
        except OSError as exc:
            print(f"ERROR: cannot read stdin: {exc}", file=sys.stderr)
            return 2
    else:
        command = args.command

    command = command.strip()

    # Load lists
    allowlist = load_list(args.allowlist)
    blocklist = load_list(args.blocklist)

    # Exact allowlist match bypasses everything else.
    if _command_in_allowlist(command, allowlist):
        if args.verbose:
            print("OK: command is in allowlist")
        return 0

    # Structural safety checks
    reasons = _check_dangerous_tokens(command)

    # Base command existence check — catches typos and "run <cmd>" confusion
    # before an approval is requested.
    base_reason = _check_base_command_exists(command)
    if base_reason:
        reasons.append(base_reason)

    # Blocklist checks
    block_match = _matches_blocklist(command, blocklist)
    if block_match:
        reasons.append(f"matches blocklist entry: {block_match!r}")

    # Optional strict mode: base command must appear as the first token in at
    # least one allowlisted command.
    if args.require_allowlist:
        base = _extract_base_command(command)
        allowed_bases = set()
        for allowed in allowlist:
            try:
                allowed_tokens = _tokenize(allowed)
                if allowed_tokens:
                    allowed_bases.add(Path(allowed_tokens[0]).name)
            except ValueError:
                # Malformed allowlist entry; ignore.
                continue
        if base not in allowed_bases:
            reasons.append(f"base command '{base}' is not in allowlist")

    if reasons:
        print("ERROR: unsafe command:", file=sys.stderr)
        for reason in reasons:
            print(f"  - {reason}", file=sys.stderr)
        print("\nPolicy: use single, simple commands. No pipes, chaining, redirects, subshells, globs or backgrounding.", file=sys.stderr)
        return 1

    if args.verbose:
        print("OK: command passes safety checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
