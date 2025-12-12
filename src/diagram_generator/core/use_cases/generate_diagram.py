from diagram_generator.core.domain.component import Component, ComponentType, GenericComponent
from diagram_generator.core.domain.view_config import ViewConfig
from diagram_generator.core.ports.diagram_port import DiagramPort
from diagram_generator.core.ports.metadata_port import MetadataPort


class GenerateDiagramUseCase:
    def __init__(self, metadata_port: MetadataPort, diagram_port: DiagramPort):
        self._metadata_port = metadata_port
        self._diagram_port = diagram_port

    def execute(self, view_key: str) -> str:
        # 1. Load all metadata
        # (In a real scenario, we might optimize this to only load what's needed,
        # but for V1 we load all and filter in memory)
        all_components = self._metadata_port.load_components()
        all_relationships = self._metadata_port.load_relationships()
        all_view_configs = self._metadata_port.load_view_configs()
        all_flows = self._metadata_port.load_flows()

        # 2. Find the requested ViewConfig
        view_config = next((vc for vc in all_view_configs if vc.key == view_key), None)
        if not view_config:
            raise ValueError(f"View configuration with key '{view_key}' not found.")

        # 2.5 Auto-Discover Missing Components (Quick Draw)
        known_ids = {c.id for c in all_components}
        missing_ids = set()
        for r in all_relationships:
            if r.source_id not in known_ids:
                missing_ids.add(r.source_id)
            if r.target_id not in known_ids:
                missing_ids.add(r.target_id)
        
        if missing_ids:
            for mid in missing_ids:
                # Create a generic "Box" component
                new_comp = GenericComponent(
                    id=mid,
                    name=mid, # Use ID as name
                    description="Auto-discovered component",
                    type=ComponentType.generic
                )
                all_components.append(new_comp)

        # 3. Filter Graph based on ViewConfig
        # (Simple implementation: include all for now, or filter by tags if present)
        filtered_components = self._filter_components(all_components, view_config)
        
        # Filter relationships: only include if both source and target are in filtered_components
        filtered_component_ids = {c.id for c in filtered_components}
        filtered_relationships = [
            r for r in all_relationships
            if r.source_id in filtered_component_ids and r.target_id in filtered_component_ids
        ]

        # 4. Render
        return self._diagram_port.render(view_config, filtered_components, filtered_relationships, all_flows)

    def _filter_components(self, components: list[Component], config: ViewConfig) -> list[Component]:
        if not config.filters or not config.filters.tags:
            return components
        
        required_tags = set(config.filters.tags)
        return [
            c for c in components
            if c.tags and set(c.tags).intersection(required_tags)
        ]
