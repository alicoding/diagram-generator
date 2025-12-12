
from jinja2 import Environment, FileSystemLoader, select_autoescape

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
        
        from ruamel.yaml import YAML
        import io
        
        def to_yaml(value):
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
        if view_config.flow_id and flows:
            active_flow = next((f for f in flows if f.id == view_config.flow_id), None)

        return template.render(
            config=view_config,
            components=components,
            relationships=relationships,
            flows=flows,
            flow=active_flow
        )
