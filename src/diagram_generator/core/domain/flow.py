from __future__ import annotations

from pydantic import BaseModel, Field


class FlowStep(BaseModel):
    source_id: str = Field(..., description="ID of the source component.")
    target_id: str = Field(..., description="ID of the target component.")
    description: str = Field(..., description="Description of the interaction.")
    protocol: str | None = Field(None, description="Protocol used (optional).")
    is_dashed: bool = Field(False, description="If true, render as dashed line.")
    metadata: dict = Field(default_factory=dict, description="Rich metadata (data, notes, etc).")

class Flow(BaseModel):
    id: str = Field(..., description="Unique ID for this flow.")
    description: str = Field(..., description="Description of what this flow represents.")
    steps: list[FlowStep] = Field(default_factory=list, description="Ordered steps in the flow.")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering.")
    metadata: dict = Field(default_factory=dict, description="Rich metadata for the flow.")
