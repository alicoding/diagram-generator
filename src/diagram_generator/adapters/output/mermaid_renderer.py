
import io
from typing import Any

from jinja2 import Environment, FileSystemLoader

try:
    from ruamel.yaml import YAML
except ImportError:
    YAML = None # type: ignore

from diagram_generator.core.domain.component import Component
from diagram_generator.core.domain.flow import Flow
from diagram_generator.core.domain.relationship import Relationship
from diagram_generator.core.domain.view_config import ViewConfig
from diagram_generator.core.ports.diagram_port import DiagramPort


class MermaidDiagramAdapter(DiagramPort):
    def __init__(self, template_dir: str):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        def to_yaml(value: Any) -> str:
            if YAML is None:
                return ""
            yaml = YAML(typ='safe')
            yaml.default_flow_style = False
            stream = io.StringIO()
            yaml.dump(value, stream)
            return stream.getvalue().strip()
            
        self.env.filters['to_yaml'] = to_yaml

    def render(
        self,
        view_config: ViewConfig,
        components: list[Component],
        relationships: list[Relationship],
        flows: list[Flow] | None = None
    ) -> str:
        template_name = f"{view_config.type.value}.j2"
        try:
            template = self.env.get_template(template_name)
        except Exception as e:
            raise ValueError(f"Template '{template_name}' not found for view type '{view_config.type}'.") from e
        
        # Look for a specific flow if config.flow_id is set
        active_flow = None
        flow_styles = {}
        if view_config.flow_id and flows:
            active_flow = next((f for f in flows if f.id == view_config.flow_id), None)
            if active_flow and active_flow.metadata:
                 flow_styles = active_flow.metadata.get("styles", {})

        # Build Hierarchy for Swimlanes
        # Structure: {'name': 'Root', 'type': 'group', 'children': {...}, 'node_components': [Component]}
        hierarchy: dict[str, Any] = {'name': 'root', 'type': 'root', 'children': {}, 'node_components': []}
        
        for comp in components:
            group_path = comp.metadata.get("group")
            if not group_path:
                hierarchy['node_components'].append(comp)
                continue
            
            # Split by dot or some separator, currently assuming "Parent.Child"
            parts = group_path.split("__SEPARATOR__") 
            # Note: User request implied "Infrastructure Layer.PSOS" so let's try dot, 
            # but usually dot is dangerous in IDs. Let's support explicit dot.
            # If no dot, it's just one group.
            parts = group_path.split('.')
            
            current = hierarchy
            for raw_part in parts:
                part = raw_part.strip()
                if part not in current['children']:
                    current['children'][part] = {
                        'name': part, 
                        'type': 'group', 
                        'children': {}, 
                        'node_components': []
                    }
                current = current['children'][part]
            
            current['node_components'].append(comp)

        return template.render(
            config=view_config,
            components=components,
            relationships=relationships,
            flows=flows,
            flow=active_flow,
            hierarchy=hierarchy,
            styles=flow_styles
        )
