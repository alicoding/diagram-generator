from pathlib import Path
from typing import Any

import pytest
from pydantic import TypeAdapter
from ruamel.yaml import YAML

from diagram_generator.adapters.output.mermaid_renderer import MermaidDiagramAdapter
from diagram_generator.core.domain.component import Component
from diagram_generator.core.domain.flow import Flow
from diagram_generator.core.domain.relationship import Relationship
from diagram_generator.core.domain.view_config import ViewConfig


def load_yaml(path: Path) -> Any:
    yaml = YAML(typ='safe')
    with open(path) as f:
        return yaml.load(f)

@pytest.fixture
def rich_data() -> tuple[list[Component], list[Flow], list[ViewConfig]]:
    base_dir = Path(__file__).parent / "data"
    
    # Load Components
    comp_data = load_yaml(base_dir / "components/rich_example.yaml")['components']
    comp_adapter: TypeAdapter[Component] = TypeAdapter(Component)
    components = [comp_adapter.validate_python(c) for c in comp_data]
    
    # Load Flows
    flow_data = load_yaml(base_dir / "flows/flows.yaml")['flows']
    flow_adapter = TypeAdapter(Flow)
    flows = [flow_adapter.validate_python(f) for f in flow_data]
    
    # Load Views
    view_data = load_yaml(base_dir / "views/views.yaml")['views']
    view_adapter = TypeAdapter(ViewConfig)
    views = [view_adapter.validate_python(v) for v in view_data]
    
    return components, flows, views

def test_production_readiness(rich_data: tuple[list[Component], list[Flow], list[ViewConfig]]) -> None:
    components, flows, views = rich_data
    
    # Setup Renderer
    template_dir = Path(__file__).parents[1] / "src/diagram_generator/templates"
    if not template_dir.exists():
        # Fallback for when running from root
        template_dir = Path("templates")
        
    renderer = MermaidDiagramAdapter(str(template_dir.absolute()))
    
    relationships: list[Relationship] = [] # No static relationships in this test data, relying on flows or implicitly
    
    # 1. Test C4 Context
    ctx_view = next(v for v in views if v.key == 'context-view')
    mmd_ctx = renderer.render(ctx_view, components, relationships, flows)
    assert "C4Context" in mmd_ctx
    assert "themeVariables" in mmd_ctx # Theme check
    assert "primaryColor" in mmd_ctx
    assert "#00aa00" in mmd_ctx # Generic green
    
    # 2. Test Container View
    cnt_view = next(v for v in views if v.key == 'container-view')
    mmd_cnt = renderer.render(cnt_view, components, relationships, flows)
    assert "C4Container" in mmd_cnt
    assert "ContainerDb" in mmd_cnt 

    # 3. Test Sequence Diagram (Flows)
    seq_view = next(v for v in views if v.key == 'sequence-view')
    mmd_seq = renderer.render(seq_view, components, relationships, flows)
    assert "sequenceDiagram" in mmd_seq
    assert "autonumber" in mmd_seq # Feature: Autonumber
    assert "Fetch profile history" in mmd_seq 
    assert "risk-db" in mmd_seq 
    assert "-->>" in mmd_seq # Feature: Dashed line (is_dashed: true)
    assert "actorBkg" in mmd_seq # Feature: Specific theme variable

    # 4. Test Swimlane/Flowchart (Grouping)
    swim_view = next(v for v in views if v.key == 'swimlane-view')
    mmd_swim = renderer.render(swim_view, components, relationships, flows)
    assert "graph LR" in mmd_swim # Feature: Layout Direction
    assert "subgraph Compliance_Team" in mmd_swim 
