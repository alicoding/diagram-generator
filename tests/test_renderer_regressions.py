
import pytest
from diagram_generator.adapters.output.mermaid_renderer import MermaidDiagramAdapter
from diagram_generator.core.domain.view_config import ViewConfig, Type as ViewType
from diagram_generator.core.domain.flow import Flow, FlowStep

class TestMermaidRegression:
    def test_special_characters_rendering(self, tmp_path):
        """
        Verify that special characters like '&' are rendered literally 
        and not HTML-escaped (e.g., '&' -> '&') because Mermaid handles them.
        """
        adapter = MermaidDiagramAdapter(template_dir="templates")
        
        # Mock ViewConfig
        view_config = ViewConfig(
            key="test-view",
            title="Test & Verification", # logical &
            type=ViewType.sequence
        )
        
        # Mock Flow with special chars
        flow = Flow(
            id="test-flow",
            description="Flow & Test",
            steps=[
                FlowStep(
                    source_id="a",
                    target_id="b",
                    description="This & That", # Should remain "This & That"
                    is_dashed=False
                )
            ]
        )
        
        # Render
        output = adapter.render(view_config, [], [], flows=[flow], active_flow=flow)
        
        # Assertions
        assert "Test & Verification" in output, "Title should preserve '&'"
        assert "This & That" in output, "Description should preserve '&'"
        assert "&amp;" not in output, "Should not contain HTML entities like '&amp;'"

    def test_newline_rendering(self, tmp_path):
        """
        Ensure that the renderer (or template) doesn't break on newlines 
        if they somehow sneak in, although sanitization usually happens at ingestion.
        This test checks the raw renderer behavior.
        """
        adapter = MermaidDiagramAdapter(template_dir="templates")
        
        view_config = ViewConfig(
            key="test-view-nl",
            title="Test NL",
            type=ViewType.sequence
        )
        
        flow = Flow(
            id="test-flow-nl",
            description="Newline Test",
            steps=[
                FlowStep(
                    source_id="a",
                    target_id="b",
                    description="Line 1\\nLine 2", # Escaped newline for Mermaid
                    is_dashed=False
                )
            ]
        )
        
        output = adapter.render(view_config, [], [], flows=[flow], active_flow=flow)
        
        # Mermaid expects literal \n for newlines in descriptions if inside quotes, 
        # or typical usage might just be keeping it on one line.
        # But mostly we want to ensure physical line breaks didn't break the syntax.
        
        lines = output.splitlines()
        # Find the relationship line
        rel_line = next((l for l in lines if "a->>b" in l), None)
        assert rel_line is not None
        assert "Line 1\\nLine 2" in rel_line
