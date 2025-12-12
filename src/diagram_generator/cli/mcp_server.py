from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from diagram_generator.adapters.input.yaml_loader import YAMLMetadataAdapter

app = typer.Typer()
console = Console()

@app.command()
def start() -> None:
    """Starts the MCP server for LLM integration."""
    try:
        from fastmcp import FastMCP  # noqa: PLC0415
    except ImportError:
        console.print("[red]Error: 'fastmcp' not installed.[/red]")
        console.print("Install it with: [cyan]pip install 'diagram-generator[mcp]'[/cyan] or [cyan]pip install fastmcp[/cyan]") # noqa: E501
        raise typer.Exit(1) from None

    mcp: Any = FastMCP("diagram-generator")

    # Define tools inside `start` or structured better?
    # FastMCP relies on decorators on the `mcp` object.
    # The current structure has top-level `if FastMCP:` which is flawed if FastMCP is missing
    # but the module is imported.
    # We must define the mcp app and tools inside `start` OR
    # only define them if import succeeds, and fail gracefully at `start`.
    
    # Refactoring to define tools inside start is cleaner for this "optional" pattern.
    
    @mcp.tool() # type: ignore
    def list_components(data_dir: str = "./data") -> list[dict[str, Any]]:
        """Lists all components in the system."""
        loader = YAMLMetadataAdapter(data_dir)
        return [c.model_dump() for c in loader.load_components()]

    @mcp.tool() # type: ignore
    def add_service(id: str, name: str, description: str, cluster: str, data_dir: str = "./data") -> str:
        """Adds a new microservice to the system."""
        path = Path(data_dir) / "components" / "services.yaml"
        new_service = f"""
  - id: {id}
    name: {name}
    type: service
    description: {description}
    deployment:
      cluster: {cluster}
"""
        with open(path, "a") as f:
            f.write(new_service)
        return f"Added service {id} to {path}"

    mcp.run()
