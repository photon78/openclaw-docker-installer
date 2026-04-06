#!/usr/bin/env python3
import sys
print("Python:", sys.executable)
print("Path:", sys.path[:3])
try:
    import questionary
    print("questionary OK:", questionary.__version__)
except ImportError as e:
    print("questionary FAIL:", e)
