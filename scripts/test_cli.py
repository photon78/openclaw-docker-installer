#!/usr/bin/env python3
import sys
sys.path.insert(0, "src")
from typer.testing import CliRunner
from main import app

runner = CliRunner()

print("=== --help ===")
result = runner.invoke(app, ["--help"])
print(result.output)

print("=== status ===")
result = runner.invoke(app, ["status"])
print(result.output)
