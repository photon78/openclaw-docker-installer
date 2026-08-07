"""Shared security policy definitions for exec approvals and safe-exec checks.

This module exists so that the generator producing exec-approvals.json and the
safe-exec pre-flight check agree on what is forbidden by default. Keeping the
list in one place prevents the two security layers from drifting apart.
"""
from __future__ import annotations

# Basenames of binaries that must never appear in an exec-approvals allowlist
# because they are full interpreters, shell injection vectors, or generic
# network/data-exfiltration tools. The allowlist model only works when the
# agent cannot invoke an arbitrary interpreter or raw network tool.
FORBIDDEN_ALLOWLIST_BASES: frozenset[str] = frozenset({
    # Interpreters / execution vectors
    "python",
    "python3",
    "perl",
    "ruby",
    "node",
    "nodejs",
    "sh",
    "bash",
    "zsh",
    "dash",
    "ksh",
    "csh",
    "tcsh",
    "fish",
    "awk",
    "gawk",
    "nawk",
    "mawk",
    "env",
    "xargs",
    "find",
    "make",
    "cmake",
    # Network tools (generic exfiltration / remote execution)
    "curl",
    "wget",
    "nc",
    "netcat",
    "ssh",
    "scp",
    "sftp",
    "rsync",
    "ftp",
    "telnet",
    # File-system / privilege escalation helpers
    "ln",
    "chmod",
    "chown",
    "dd",
    "sudo",
    "su",
    "docker",
    "podman",
    "doas",
})


# Commands that safe_exec_check considers dangerous enough that they must not
# pass structural checks alone; they require explicit allowlisting. This set
# mirrors the spirit of FORBIDDEN_ALLOWLIST_BASES for the *inside* of an
# already-allowlisted invocation.
REQUIRES_EXPLICIT_ALLOW_BASES: frozenset[str] = frozenset({
    "rm",
    "ssh",
    "mv",
    "cp",
    "curl",
    "wget",
    "nc",
    "netcat",
    "rsync",
    "scp",
    "sftp",
    "python",
    "python3",
    "bash",
    "sh",
    "chmod",
    "chown",
    "dd",
    "sudo",
    "docker",
})


def is_forbidden_allowlist_pattern(pattern: str) -> tuple[bool, str | None]:
    """Return (True, reason) if *pattern* matches a forbidden allowlist entry.

    The match uses basename comparison and also catches /usr/bin/python3,
    /bin/bash, /usr/local/bin/curl, etc.
    """
    from pathlib import Path

    basename = Path(pattern).name
    if basename in FORBIDDEN_ALLOWLIST_BASES:
        return True, f"{basename!r} is forbidden in allowlists"
    return False, None
