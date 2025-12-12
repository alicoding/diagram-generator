from typing import Protocol

from diagram_generator.core.domain.component import Component
from diagram_generator.core.domain.flow import Flow
from diagram_generator.core.domain.relationship import Relationship
from diagram_generator.core.domain.view_config import ViewConfig


class MetadataPort(Protocol):
    def load_components(self) -> list[Component]:
        ...

    def load_relationships(self) -> list[Relationship]:
        ...
    
    def load_view_configs(self) -> list[ViewConfig]:
        ...

    def load_flows(self) -> list[Flow]:
        ...
