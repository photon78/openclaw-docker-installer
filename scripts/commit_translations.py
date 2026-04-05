#!/usr/bin/env python3
import subprocess
import sys
import os

repo = "/home/hummer/.openclaw/workspace-coding/projects/openclaw-docker-installer"
os.chdir(repo)

steps = [
    ["git", "add", "-A"],
    ["git", "commit", "-m", "docs: translate all markdown files to English, update wine link"],
    ["git", "push", "origin", "feature/prototype-docker-check"],
]

for cmd in steps:
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(" ".join(cmd))
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        print(f"ERROR: exit code {result.returncode}")
        sys.exit(result.returncode)

print("Done.")
