from diagram_generator.core.domain.component import Component


class ComponentHierarchy:
    """Resolves abstraction parents for components based on metadata."""

    def __init__(self, components: list[Component]):
        self.comp_map = {c.id: c for c in components}
        
    def get_parent_id(self, component_id: str, level: str) -> str:
        """
        Resolves the parent ID for a given level.
        system (Level 0) -> Root Group
        container (Level 1) -> Root.Child Group
        """
        comp = self.comp_map.get(component_id)
        if not comp:
            return component_id # Unknown, return self
            
        group_path = comp.metadata.get("group")
        if not group_path:
            return component_id # No group, return self
            
        parts = group_path.split('.')
        # Sanitization: Clean up spaces and forbidden chars
        parts = [p.strip().replace(' ', '_') for p in parts]
        
        if level == "system":
            return parts[0]
            
        if level == "container":
            if len(parts) >= 2: # noqa: PLR2004
                # Replace dot with underscore for valid ID
                return f"{parts[0]}_{parts[1]}"
            return parts[0] # Fallback to root
            
        return component_id
        
    def get_parent_component(self, component_id: str, level: str) -> Component | None:
        """Typesafe wrapper to return component object if it exists, else synthetic."""
        # For now, we reuse existing components if they match parent ID?
        # Actually creating synthetic components for Groups is safer for rendering.
        pass
