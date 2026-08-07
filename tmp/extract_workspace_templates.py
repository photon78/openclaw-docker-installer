#!/usr/bin/env python3
"""
Extract Markdown templates from workspace_bootstrap_gen.py

Extracts f-string templates from workspace_bootstrap_gen.py and converts them to Jinja2 templates.
"""

import re
from pathlib import Path

# Define the source and destination paths
SOURCE_FILE = Path("/home/hummer/.openclaw/workspace-coding/projects/openclaw-docker-installer/src/generator/workspace_bootstrap_gen.py")
DEST_DIR = Path("/home/hummer/.openclaw/workspace-coding/projects/openclaw-docker-installer/src/installer/templates/workspace/")

# Mapping of function names to output filenames
FUNCTION_TO_FILENAME = {
    "_soul_md": "SOUL.md.j2",
    "_agents_md": "AGENTS.md.j2",
    "_heartbeat_md": "HEARTBEAT.md.j2",
    "_identity_md": "IDENTITY.md.j2",
    "_memory_md": "MEMORY.md.j2",
    "_user_md": "USER.md.j2",
    "_bootstrap_md": "BOOTSTRAP.md.j2",
    "_tools_md": "TOOLS.md.j2",
    "_check_tasks_py": "check_tasks.py.j2",
}


def extract_template(function_name: str, content: str) -> str:
    """Extract the f-string template from a function and convert it to Jinja2."""
    # Find the function definition
    pattern = rf"def {function_name}\(.*?\) -> str:\n    return f\"\"\"(.*?)\"\"\""
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError(f"Could not extract template from {function_name}")
    
    template = match.group(1)
    
    # Convert Python f-string placeholders to Jinja2
    template = re.sub(r"\{state\.(\w+)\}", r"{{\1}}", template)
    template = re.sub(r"\{_PERSONA_DESCRIPTIONS\.get\((.*?)\)\}", r"{{\1}}", template)
    
    return template

def main() -> None:
    """Main function to extract and save templates."""
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Source file not found: {SOURCE_FILE}")
    
    content = SOURCE_FILE.read_text(encoding="utf-8")
    
    # Create the destination directory if it doesn't exist
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    
    extracted_templates = []
    unconvertible_placeholders = []
    
    for function_name, filename in FUNCTION_TO_FILENAME.items():
        try:
            template = extract_template(function_name, content)
            dest_path = DEST_DIR / filename
            dest_path.write_text(template, encoding="utf-8")
            extracted_templates.append(filename)
        except ValueError as e:
            print(f"Error extracting {function_name}: {e}")
        except re.error as e:
            print(f"Regex error in {function_name}: {e}")
            unconvertible_placeholders.append(function_name)
    
    # Print summary
    print("\nExtraction Summary:")
    print(f"Script path: {SOURCE_FILE}")
    print(f"Successfully extracted templates: {', '.join(extracted_templates)}")
    if unconvertible_placeholders:
        print(f"Templates with unconvertible placeholders: {', '.join(unconvertible_placeholders)}")
    else:
        print("All placeholders were successfully converted.")

if __name__ == "__main__":
    main()
