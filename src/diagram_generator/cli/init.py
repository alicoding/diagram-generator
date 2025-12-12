import json
from pathlib import Path

import typer
from rich.console import Console

from diagram_generator.cli.schema import UnifiedConfig

app = typer.Typer()
console = Console()

@app.command()
def project(
    path: Path = typer.Option(Path("."), help="Directory to initialize the project in."), # noqa: B008
    name: str = typer.Option("My System", help="Name of the system."),
):
    """
    Scaffolds a new diagram-generator project with directories, schema, and sample data.
    """
    console.print(f"[bold green]Initializing diagram-generator project: {name}[/bold green]")
    
    # 1. Create Directories
    data_dir = path / "data"
    dirs = [
        data_dir / "components",
        data_dir / "relationships",
        data_dir / "views",
        data_dir / "flows",
        path / "templates", # Optional customization
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        console.print(f"Created directory: [blue]{d}[/blue]")

    # 2. Generate Schema
    schema_path = path / "schema.json"
    schema = UnifiedConfig.model_json_schema()
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)
    console.print(f"Generated Schema: [blue]{schema_path}[/blue]")

    # 3. Create Sample Data
    
    # components/system.yaml
    system_yaml_content = f"""# yaml-language-server: $schema=../../schema.json
components:
  - id: user
    name: User
    type: person
    description: A user of the system.

  - id: system
    name: {name}
    type: system
    description: The main software system.
"""
    with open(data_dir / "components" / "system.yaml", "w") as f:
        f.write(system_yaml_content)
    console.print("Created sample component: [blue]data/components/system.yaml[/blue]")

    # relationships/wiring.yaml
    wiring_yaml_content = """# yaml-language-server: $schema=../../schema.json
relationships:
  - source_id: user
    target_id: system
    description: Uses
    technology: HTTPS
"""
    with open(data_dir / "relationships" / "wiring.yaml", "w") as f:
        f.write(wiring_yaml_content)
    console.print("Created sample relationship: [blue]data/relationships/wiring.yaml[/blue]")

    # views/context.yaml
    context_yaml_content = """# yaml-language-server: $schema=../../schema.json
views:
  - key: context
    title: System Context
    type: c4_context
    mermaid_config:
      theme: base
"""
    with open(data_dir / "views" / "context.yaml", "w") as f:
        f.write(context_yaml_content)
    console.print("Created sample view: [blue]data/views/context.yaml[/blue]")

    console.print("\n[bold green]✓ Project initialized successfully![/bold green]")
    console.print("\n[dim]Next steps:[/dim]")
    console.print(f"1. [cyan]cd {path}[/cyan]")
    console.print("2. [cyan]diagram-generator generate-all --data-dir ./data --output-dir ./dist[/cyan]")
    console.print("3. Open the YAML files in VS Code to see IntelliSense in action.")
