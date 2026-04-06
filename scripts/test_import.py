#!/usr/bin/env python3
import sys
sys.path.insert(0, "src")
import main
print("Import OK")
print("Commands:", [c.name for c in main.app.registered_commands])
