import typer
from pydantic import BaseModel
from rich.console import Console

from diagram_generator.core.domain.component import Container, Database, ExternalSystem, Person, Service
from diagram_generator.core.domain.flow import Flow
from diagram_generator.core.domain.relationship import Relationship
from diagram_generator.core.domain.view_config import ViewConfig

console = Console()
app = typer.Typer()

def model_to_markdown(model: type[BaseModel], title: str) -> str:
    """
    Generates a Markdown table for a Pydantic model's fields.
    """
    lines = [f"## {title}", ""]
    lines.append(f"_{model.__doc__ or 'No description available.'}_")
    lines.append("")
    lines.append("| Field | Type | Required | Description |")
    lines.append("| :--- | :--- | :--- | :--- |")

    schema = model.model_json_schema()
    props = schema.get("properties", {})
    required = set(schema.get("required", []))

    for name, prop in props.items():
        # Resolve type ref if present
        ref = prop.get("$ref") or prop.get("anyOf", [{}])[0].get("$ref")
        type_name = "Any"
        if "type" in prop:
            type_name = prop["type"]
        elif ref:
            type_name = ref.split("/")[-1]
        elif "anyOf" in prop:
             # Simplified handling for Optional/Union
             type_name = " | ".join([p.get("type", "Ref") for p in prop["anyOf"] if p.get("type") != "null"])

        is_req = "✅" if name in required else "❌"
        desc = prop.get("description", "").replace("\n", " ")
        
        lines.append(f"| `{name}` | `{type_name}` | {is_req} | {desc} |")
    
    lines.append("")
    return "\n".join(lines)

@app.command()
def generate(
    output: str = typer.Option("FEATURES.md", help="Output Markdown file.")
) -> None:
    """
    Generates a FEATURES.md reference manual from the code definitions.
    """
    console.print(f"[yellow]Generating documentation to {output}...[/yellow]")
    
    sections = [
        "# Diagram Generator Features Reference",
        "",
        "> **Auto-Generated**: This document is generated directly from the Pydantic models in the code.",
        "",
        "## Table of Contents",
        "- [Components](#components)",
        "- [Relationships](#relationships)",
        "- [Views](#views)",
        "- [Flows](#flows)",
        "",
        "# Components",
        "All components share common fields, but specific types have extra properties.",
        ""
    ]
    
    # We can't easily iterate the Union 'Component' directly via model_fields in the same way 
    # as a flat model, so we'll document the specific types.
    sections.append(model_to_markdown(Service, "Service"))
    sections.append(model_to_markdown(Database, "Database"))
    sections.append(model_to_markdown(Container, "Container"))
    sections.append(model_to_markdown(Person, "Person"))
    sections.append(model_to_markdown(ExternalSystem, "External System"))

    sections.append("# Relationships")
    sections.append(model_to_markdown(Relationship, "Relationship Object"))

    sections.append("# Views")
    sections.append(model_to_markdown(ViewConfig, "View Configuration"))

    sections.append("# Flows")
    sections.append(model_to_markdown(Flow, "Flow Object"))

    with open(output, "w") as f:
        f.write("\n".join(sections))

    console.print(f"[green]✓ Documentation generated at {output}[/green]")
