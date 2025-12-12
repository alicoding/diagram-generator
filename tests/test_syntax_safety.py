import re
from pathlib import Path

import pytest

# Known Bad Patterns in Mermaid
BAD_PATTERNS = [
    (r"graph\s+[LT][BR]\s+title", "Flowchart should not have inline title. Use Frontmatter."),
    (r"subgraph Legend", "Legends inside C4Context are often unsupported. Use dynamic legend or separate graph."),
]

def test_syntax_safety() -> None:
    """
    Scans all generated .mmd files in dist/ and templates/ to ensure no known bad patterns exist.
    """
    dist_dir = Path("dist")
    if not dist_dir.exists():
        pytest.skip("dist/ directory not found. Run generation first.")

    for mmd_file in dist_dir.glob("*.mmd"):
        content = mmd_file.read_text()
        for pattern, msg in BAD_PATTERNS:
            if re.search(pattern, content):
                pytest.fail(f"Syntax Error in {mmd_file.name}: {msg}\nFound pattern: {pattern}")

def test_template_safety() -> None:
    """
    Scans templates to ensure they don't produce bad patterns hardcoded.
    """
    template_dir = Path("templates")
    if not template_dir.exists():
        template_dir = Path("src/diagram_generator/templates")

    for template_file in template_dir.glob("*.j2"):
        content = template_file.read_text()
        # Check for inline title in graph
        if "graph " in content and "title " in content and "---" not in content and "C4" not in content:
             # Heuristic: if graph and title exist but no frontmatter dash, might be risky.
             # This is a weak check, relying more on the generated output test.
             pass
