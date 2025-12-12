from diagram_generator.core.domain.component import Component, Container, System
from diagram_generator.core.domain.flow import Flow, FlowStep
from diagram_generator.core.services.component_hierarchy import ComponentHierarchy


class FlowAbstractor:
    def abstract_flows(
        self, flows: list[Flow], components: list[Component], level: str
    ) -> tuple[list[Flow], list[Component]]:
        if level not in ['system', 'container']:
            return flows, components
            
        hierarchy = ComponentHierarchy(components)
        abstract_flows = []
        abstract_components_map = {} # ID -> Component
        
        for flow in flows:
            new_steps = []
            last_step = None
            
            for step in flow.steps:
                # 1. Resolve Parents
                src_parent_name = hierarchy.get_parent_id(step.source_id, level)
                tgt_parent_name = hierarchy.get_parent_id(step.target_id, level)
                
                # Sanitize IDs for internal use/linking
                src_parent_id = self._sanitize_id(src_parent_name)
                tgt_parent_id = self._sanitize_id(tgt_parent_name)
                
                # 2. Skip internal steps (same parent interaction)
                if src_parent_id == tgt_parent_id:
                    continue
                    
                # 3. Create Abstract Step
                # We need to register these parents as components if they don't exist
                if src_parent_id not in abstract_components_map:
                   abstract_components_map[src_parent_id] = self._create_synthetic_component(
                       src_parent_id, src_parent_name, level
                   )
                if tgt_parent_id not in abstract_components_map:
                   abstract_components_map[tgt_parent_id] = self._create_synthetic_component(
                       tgt_parent_id, tgt_parent_name, level
                   )

                new_step = FlowStep(
                    source_id=src_parent_id,
                    target_id=tgt_parent_id,
                    description=step.description, # Could be aggregated?
                    metadata=step.metadata.copy()
                )
                
                # 4. Deduplicate (if same as last step)
                if (
                    last_step and 
                    last_step.source_id == new_step.source_id and 
                    last_step.target_id == new_step.target_id
                ):
                    # Append description?
                    continue
                    
                new_steps.append(new_step)
                last_step = new_step
            
            if new_steps:
                new_flow = Flow(
                    id=f"{flow.id}_{level}",
                    description=f"{flow.description} (Abstracted: {level})",
                    steps=new_steps,
                    tags=flow.tags,
                    metadata=flow.metadata
                )
                abstract_flows.append(new_flow)

        # Merge original components if they match parent IDs, otherwise use synthetic
        # Actually we just return the synthetic ones + any original that matched?
        # Let's return just the abstract components that are used.
        return abstract_flows, list(abstract_components_map.values())
        
    def _sanitize_id(self, raw: str) -> str:
        import re  # noqa: PLC0415
        # Convert "System A" -> "System_A", "Mgmt Layer" -> "Mgmt_Layer"
        s = str(raw).strip().replace(" ", "_").replace("&", "_and_")
        return re.sub(r'[^a-zA-Z0-9_\-]', '', s)

    def _create_synthetic_component(self, id: str, name: str, level: str) -> Component:
        # Sanitize ID for validation (alphanumeric only)
        # But we need to use the original ID for linking?
        # The Hierarchy resolver returns names as IDs (e.g. "Payment Platform").
        # We should slugify it. For now, let's just use System/Container types
        # instead of GenericComponent because GenericComponent is strict?
        # Actually base component is strict on ID (pattern).
        # We need to ensure the ID returned by `get_parent_id` is clean.
        
        
        # If ID has spaces, we can't do much if BaseComponent forbids it.
        # We should probably update ComponentHierarchy to slugify IDs.
        
        if level == 'system':
            return System(id=id, name=name, description="Abstracted System")
        else:
            return Container(id=id, name=name, description="Abstracted Container")
