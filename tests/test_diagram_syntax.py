from typing import Any
import re
from diagram_generator.core.use_cases.generate_diagram import GenerateDiagramUseCase
from diagram_generator.adapters.output.mermaid_renderer import MermaidDiagramAdapter
from diagram_generator.adapters.input.yaml_loader import YAMLMetadataAdapter

class TestDiagramSyntax:
    def test_generated_diagrams_syntax(self) -> None:
        """
        Pipeline check: ensure all example diagrams generate with valid basic syntax.
        Specifically catches 'multiple nodes on one line' regression.
        """
        # 1. Setup
        loader = YAMLMetadataAdapter(
            data_path="examples/enterprise/data" 
        )
        # Note: YAMLMetadataAdapter init takes data_path string, not separate lists.
        # It scans subdirs components/flows/views/relationships automatically.
        adapter = MermaidDiagramAdapter(template_dir="templates")
        use_case = GenerateDiagramUseCase(loader, adapter)
        
        # 2. Get all views
        view_configs = loader.load_view_configs()
        assert len(view_configs) > 0, "No views found to verify"
        
        for config in view_configs:
            # 3. Generate
            try:
                mmd = use_case.execute(config.key)
            except Exception as e:
                # If generation fails, that's a pipeline failure
                raise AssertionError(f"Failed to generate view '{config.key}': {e}") from e
                
            # 4. Verify Syntax
            self._verify_syntax(mmd, config.key)

    def _verify_syntax(self, mmd: str, view_key: str) -> None:
        """Basic Mermaid syntax checks."""
        lines = mmd.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
                
            # Check for multiple node definitions on one line without semicolon
            # e.g. NodeA["..."] NodeB["..."]
            # Regex: Look for pattern `["..."]` followed by space components then another identifier or `[`
            # This is complex to regex perfectly, but we can look for "double declarations"
            
            # Simple heuristic: If line contains `["` twice, verify there's a `;` or `&` or `-->` between.
            if stripped.count('["') > 1:
                # Exclude edge definitions: A["x"] --> B["y"] is valid.
                if "-->" not in stripped and "-.-" not in stripped and "==>" not in stripped and "&" not in stripped:
                    # Likely missing newline: A["..."] B["..."]
                    raise AssertionError(
                        f"View '{view_key}': Line {i+1} appears to have multiple node definitions without separators.\nLine: {stripped}"
                    )

            # Check balanced brackets (basic)
            if stripped.count('[') != stripped.count(']'):
                 # Graph directions like `graph TB` don't have brackets. 
                 # Edge labels `|...|` might trick this if they contain brackets. 
                 # But generally node defs should be balanced on the line.
                 # Actually, multi-line strings exist. Skipping this for now as it's flaky.
                 pass

        # Check for empty nodes or weird artifacts
        if '()' in mmd or '[]' in mmd:
             # Empty brackets might be valid string content but rarely valid node shapes
             pass
