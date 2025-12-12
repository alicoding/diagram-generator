import json

import typer
from pydantic import BaseModel, Field
from rich.console import Console

from diagram_generator.core.domain.component import Component
from diagram_generator.core.domain.flow import Flow
from diagram_generator.core.domain.relationship import Relationship
from diagram_generator.core.domain.view_config import ViewConfig

console = Console()
app = typer.Typer()

class UnifiedConfig(BaseModel):
    """
    Root schema for validating any diagram-generator YAML file.
    VS Code will match the top-level keys.
    """
    components: list[Component] | None = Field(None, description="List of system components.")
    relationships: list[Relationship] | None = Field(None, description="List of relationships between components.")
    views: list[ViewConfig] | None = Field(None, description="List of diagram view configurations.")
    flows: list[Flow] | None = Field(None, description="List of sequence flows.")

@app.command()
def generate(
    output: str | None = typer.Option(None, help="Output JSON file path. Defaults to stdout."),
) -> None:
    """
    Generates a JSON Schema for IDE validation (VS Code, JetBrains).
    """
    schema = UnifiedConfig.model_json_schema()
    
    schema_str = json.dumps(schema, indent=2)
    
    if output:
        with open(output, "w") as f:
            f.write(schema_str)
        console.print(f"[green]✓ Schema generated at {output}[/green]")
        console.print("[dim]Add this line to your YAML files to enable validation:[/dim]")
        console.print(f"[blue]# yaml-language-server: $schema={output}[/blue]")
    else:
        print(schema_str)
