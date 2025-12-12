
import re
from typing import List, Dict, Tuple
from diagram_generator.core.domain.flow import Flow, FlowStep

class VerificationResult:
    def __init__(self, success: bool, errors: List[str]):
        self.success = success
        self.errors = errors

class MermaidVerifier:
    def __init__(self):
        # Regex to capture Source, Arrow, Target, Description
        # Supports ->>, -->>, ->, -->
        self.flow_regex = re.compile(r"^\s*([a-zA-Z0-9_-]+)\s*(-{1,2}(?:>>|>))\s*([a-zA-Z0-9_-]+)\s*:\s*(.+)$")

    def parse_mermaid(self, content: str) -> List[Dict[str, str]]:
        """
        Parses Mermaid sequence diagram content into a list of steps.
        """
        steps = []
        for line in content.splitlines():
            match = self.flow_regex.match(line)
            if match:
                src, arrow, tgt, desc = match.groups()
                steps.append({
                    "source": src,
                    "target": tgt,
                    "arrow": arrow,
                    "description": desc.strip()
                })
        return steps

    def verify_flow(self, flow: Flow, mmd_content: str) -> VerificationResult:
        """
        Verifies that all steps in the Flow model are present in the mermaid content
        in the correct order.
        """
        parsed_steps = self.parse_mermaid(mmd_content)
        errors = []
        
        # We need to find the flow steps within the parsed steps.
        # Since the diagram might contain other things (autonumber, title), parsing filters those out.
        # But if the view contains extraneous relationships, we just want to ensure our flow exists.
        
        # Strategy: Iterate through flow.steps and ensure they appear in parsed_steps sequences.
        
        parsed_idx = 0
        for step_idx, flow_step in enumerate(flow.steps):
            found = False
            # Search forward from current position
            while parsed_idx < len(parsed_steps):
                p_step = parsed_steps[parsed_idx]
                
                # Check match
                # 1. Source/Target match identifiers
                src_match = p_step["source"] == flow_step.source_id
                tgt_match = p_step["target"] == flow_step.target_id
                
                # 2. Description match (fuzzy or exact?)
                # We sanitized newlines to spaces, so we should compare similarly.
                expected_desc = flow_step.description.replace("\n", " ").strip()
                # Also mermaid descriptions might have <br/> or \n literal.
                # The parsed description captured from MMD text should essentially match.
                
                # Let's try exact match first
                desc_match = expected_desc in p_step["description"] # Partial match allows for [metadata] parts
                
                if src_match and tgt_match and desc_match:
                    found = True
                    parsed_idx += 1 # Advance
                    break
                
                parsed_idx += 1
            
            if not found:
                errors.append(f"Missing or out-of-order step {step_idx + 1}: {flow_step.source_id} -> {flow_step.target_id} : {flow_step.description}")
        
        return VerificationResult(len(errors) == 0, errors)
