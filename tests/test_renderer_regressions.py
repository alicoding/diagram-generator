
from typing import Any

from diagram_generator.adapters.output.mermaid_renderer import MermaidDiagramAdapter
from diagram_generator.core.domain.flow import Flow, FlowStep
from diagram_generator.core.domain.view_config import Type as ViewType
from diagram_generator.core.domain.view_config import ViewConfig


class TestMermaidRegression:
    def test_special_characters_rendering(self, tmp_path: Any) -> None:
        """
        Verify that special characters like '&' are rendered literally 
        and not HTML-escaped (e.g., '&' -> '&') because Mermaid handles them.
        """
        adapter = MermaidDiagramAdapter(template_dir="templates")
        
        # Mock ViewConfig
        view_config = ViewConfig(
            key="test-view",
            title="Test & Verification", # logical &
            type=ViewType.sequence,
            scope_id="all",
            show_legend=True,
            group_by=None,
            flow_id="test-flow"
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
                    is_dashed=False,
                    protocol=None
                )
            ]
        )
        
        # Render
        output = adapter.render(view_config, [], [], flows=[flow])
        
        # Assertions
        assert "Test & Verification" in output, "Title should preserve '&'"
        assert "This & That" in output, "Description should preserve '&'"
        assert "&amp;" not in output, "Should not contain HTML entities like '&amp;'"

    def test_newline_rendering(self, tmp_path: Any) -> None:
        """
        Ensure that the renderer (or template) doesn't break on newlines 
        if they somehow sneak in, although sanitization usually happens at ingestion.
        This test checks the raw renderer behavior.
        """
        adapter = MermaidDiagramAdapter(template_dir="templates")
        
        config = ViewConfig(
            key="test-view-nl",
            title="Test NL",
            type=ViewType.sequence,
            scope_id="all",
            show_legend=True,
            group_by=None,
            flow_id="test-flow-nl"
        )
        step = FlowStep(
            source_id="a", target_id="b", description="Line 1\nLine 2", protocol=None, is_dashed=False
        )
        flow = Flow(id="test-flow-nl", description="d", steps=[step])

        output = adapter.render(
            config,
            [],
            [],
            flows=[flow]
        )

        # Mermaid expects literal \n for newlines in descriptions if inside quotes,
        # or typical usage might just be keeping it on one line.
        # But mostly we want to ensure physical line breaks didn't break the syntax.

        lines = output.splitlines()
        # Find the relationship line
        rel_line = next((line for line in lines if "a->>b" in line), None)
        assert rel_line is not None
        assert "Line 1<br/>Line 2" in rel_line

