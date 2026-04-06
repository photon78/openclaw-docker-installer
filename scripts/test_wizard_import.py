#!/usr/bin/env python3
import sys
import os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, "src")
from wizard.wizard import run_wizard
from wizard.state import WizardState
print("Import OK")
s = WizardState()
print(f"username: {s.username}")
print(f"openclaw_dir: {s.openclaw_dir}")
print(f"workspace_dir: {s.workspace_dir}")
