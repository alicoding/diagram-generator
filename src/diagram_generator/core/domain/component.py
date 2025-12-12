from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, constr

# --- Enums ---

class ComponentType(str, Enum):
    system = 'system'
    container = 'container'
    component = 'component'
    person = 'person'
    external_system = 'external_system'
    database = 'database'
    service = 'service'
    web_ui = 'web_ui'
    legacy_system = 'legacy_system'
    generic = 'generic'

# --- Value Objects / Sub-Models ---

class DeploymentDetails(BaseModel):
    cluster: str | None = None
    container_name: str | None = None
    replicas: int | None = None
    namespace: str | None = None

class ApiEndpoint(BaseModel):
    name: str
    endpoint: str
    purpose: str | None = None
    method: Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] | None = None

class TableSchema(BaseModel):
    name: str
    description: str | None = None
    retention: str | None = None
    columns: list[str] | None = None # Simplified for now

class DatabaseDetails(BaseModel):
    name: str
    type: str # e.g. CloudSQL PostgreSQL
    tables: list[TableSchema] = Field(default_factory=list)

class UIComponent(BaseModel):
    name: str
    description: str | None = None
    integration: str | None = None

# --- Base Component ---

class BaseComponent(BaseModel):
    id: constr(pattern=r'^[a-zA-Z0-9-_]+$') = Field( # type: ignore
        ..., description="Unique identifier for the component."
    )
    name: str = Field(..., description='Human-readable name.')
    description: str | None = Field(None, description="Brief description.")
    tags: list[str] = Field(default_factory=list, description='Tags for filtering.')
    metadata: dict[str, Any] = Field(
        default_factory=dict, description='Arbitrary metadata (owner, tier, etc.).'
    )
    link: str | None = None

# --- Specific Component Types ---

class Person(BaseComponent):
    type: Literal[ComponentType.person] = ComponentType.person

class System(BaseComponent):
    """High-level system (e.g., Legacy Systems)."""
    type: Literal[ComponentType.system] = ComponentType.system
    # Systems might have high-level properties, but often contain Containers/Services

class LegacySystem(BaseComponent):
    type: Literal[ComponentType.legacy_system] = ComponentType.legacy_system
    retention: str | None = None

class Service(BaseComponent):
    """A deployable service / API application."""
    type: Literal[ComponentType.service] = ComponentType.service
    layer: str | None = None
    deployment: DeploymentDetails | None = None
    apis_exposed: list[ApiEndpoint] = Field(default_factory=list)
    business_logic: dict[str, Any] | None = Field(None, description="Business rules/logic details")
    technologies: list[str] = Field(default_factory=list)

class Database(BaseComponent):
    """A data store."""
    type: Literal[ComponentType.database] = ComponentType.database
    technology: str | None = None
    details: DatabaseDetails | None = None

class WebUI(BaseComponent):
    """A frontend application."""
    type: Literal[ComponentType.web_ui] = ComponentType.web_ui
    ui_components: list[UIComponent] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)

class Container(BaseComponent):
    """Generic container if Service/WebUI/Database doesn't fit."""
    type: Literal[ComponentType.container] = ComponentType.container
    technologies: list[str] = Field(default_factory=list)

class ExternalSystem(BaseComponent):
    type: Literal[ComponentType.external_system] = ComponentType.external_system

class GenericComponent(BaseComponent):
    """Auto-generated component for 'Quick Draw' mode."""
    type: Literal[ComponentType.generic] = ComponentType.generic

# --- Polymorphic Union ---

Component = (
    Service
    | Database
    | WebUI
    | LegacySystem
    | System
    | Person
    | Container
    | ExternalSystem
    | GenericComponent
)
