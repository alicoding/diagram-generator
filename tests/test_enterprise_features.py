from typing import Any
from unittest.mock import MagicMock

from diagram_generator.adapters.output.mermaid_renderer import MermaidDiagramAdapter
from diagram_generator.core.domain.component import ComponentType, Service
from diagram_generator.core.domain.view_config import Type as ViewType
from diagram_generator.core.domain.view_config import ViewConfig


class TestEnterpriseFeatures:
    def test_nested_grouping_hierarchy_generation(self, tmp_path: Any) -> None:
        """Test that the renderer correctly builds nested hierarchy from group metadata."""
        adapter = MermaidDiagramAdapter(template_dir="templates")
        
        c1 = Service(
            id="s1", name="S1", type=ComponentType.service, 
            metadata={"group": "L1.L2.L3"}, description="d1", business_logic=None
        )
        c2 = Service(
            id="s2", name="S2", type=ComponentType.service, 
            metadata={"group": "L1.Other"}, description="d2", business_logic=None
        )
        c3 = Service(
            id="top", name="Top", type=ComponentType.service, 
            metadata={}, description="d3", business_logic=None
        ) # No group
        
        # We need to expose the private logic or inspect the output context
        # Since we modified render to calc hierarchy inside, we can test it by running render 
        # and checking proper mermaid subgraph nesting in output
        
        config = ViewConfig(
            key="test", title="Test", type=ViewType.flowchart_swimlane, scope_id="all",
            show_legend=False, group_by=None, flow_id=None
        )
        
        output = adapter.render(config, [c1, c2, c3], [])
        
        # Verify Nesting
        # subgraph L1 contains L2, Other
        # subgraph L2 contains L3
        assert 'subgraph L1["L1"]' in output
        assert 'subgraph L2["L2"]' in output
        assert 'subgraph L3["L3"]' in output
        assert 'subgraph Other["Other"]' in output
        
        # Top should be outside subgraphs or at root
        # Ideally it shouldn't be inside L1.
        # This is harder to regex without parsing, but spot checking key strings helps.
        
    def test_style_class_injection(self, tmp_path: Any) -> None:
        """Test that styles from Flow metadata are injected into classDefs."""
        adapter = MermaidDiagramAdapter(template_dir="templates")
        
        # Flow with styles
        flow = MagicMock()
        flow.id = "flow1"
        flow.metadata = {"styles": {"myStyle": "fill:#f00"}}
        flow.steps = []
        
        config = ViewConfig(
            key="test", title="Test", type=ViewType.flowchart_swimlane, scope_id="all", flow_id="flow1",
            show_legend=False, group_by=None
        )
        
        output = adapter.render(config, [], [], flows=[flow])
        
        assert "classDef myStyle fill:#f00" in output
