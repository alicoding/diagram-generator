from typing import Protocol

from diagram_generator.core.domain.component import Component
from diagram_generator.core.domain.flow import Flow
from diagram_generator.core.domain.relationship import Relationship
from diagram_generator.core.domain.view_config import ViewConfig


class DiagramPort(Protocol):
    def render(
        self,
        view_config: ViewConfig,
        components: list[Component],
        relationships: list[Relationship],
        flows: list[Flow] | None = None
    ) -> str:
        """
        Renders a diagram based on the provided configuration and graph data.
        Returns the diagram source code (e.g., Mermaid syntax).
        """
        ...
