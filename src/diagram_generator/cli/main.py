from pathlib import Path

import typer
from rich.console import Console

from diagram_generator.adapters.input.yaml_loader import YAMLMetadataAdapter
from diagram_generator.adapters.output.mermaid_renderer import MermaidDiagramAdapter
from diagram_generator.cli import docs, init, mcp_server, schema, serve, verify
from diagram_generator.core.use_cases.generate_diagram import GenerateDiagramUseCase

app = typer.Typer()
app.add_typer(docs.app, name="docs", help="Documentation generation tools.")
app.add_typer(schema.app, name="schema", help="JSON Schema generation tools.")
app.add_typer(init.app, name="init", help="Project initialization tools.")
app.add_typer(serve.app, name="serve", help="Live preview server.")
app.add_typer(mcp_server.app, name="mcp", help="Model Context Protocol server.")
app.add_typer(verify.app, name="verify", help="Verification tools.")
console = Console()

@app.command()
def version() -> None:
    """Prints the current version."""
    console.print("diagram-generator v0.1.0")

@app.command()
def generate(
    view: str = typer.Option(..., help="The key of the view configuration to generate."),
    data_dir: str = typer.Option(
        "./data",
        help="Directory containing the metadata (components, relationships, views)."
    ),
    template_dir: str = typer.Option("./templates", help="Directory containing the Jinja2 templates."),
    output: str | None = typer.Option(None, help="Output file path. If not provided, prints to stdout.")
) -> None:
    """
    Generates a Mermaid diagram based on the specified view configuration.
    """
    try:
        # 1. Initialize Adapters
        metadata_adapter = YAMLMetadataAdapter(data_dir)
        diagram_adapter = MermaidDiagramAdapter(template_dir)

        # 2. Initialize Use Case
        use_case = GenerateDiagramUseCase(metadata_adapter, diagram_adapter)

        # 3. Execute
        result = use_case.execute(view)

        # 4. Output
        if output:
            with open(output, 'w') as f:
                f.write(result)
            console.print(f"[green]Successfully generated diagram to {output}[/green]")
        else:
            print(result)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1) from None

@app.command()
def validate(
    data_dir: str = typer.Option("./data", help="Directory containing the metadata.")
) -> None:
    """
    Validates the metadata against the schema.
    (Stub for future implementation)
    """

    console.print(f"[yellow]Validating metadata in {data_dir}... (Not implemented)[/yellow]")

@app.command()
def generate_all(
    data_dir: str = typer.Option("./data", help="Directory containing the metadata."),
    output_dir: str = typer.Option("./dist", help="Directory to save generated diagrams."),
    template_dir: str = typer.Option("./templates", help="Directory containing templates.")
) -> None:
    """
    Generates diagrams for ALL view configurations found in the data directory.
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. Initialize
        metadata_adapter = YAMLMetadataAdapter(data_dir)
        diagram_adapter = MermaidDiagramAdapter(template_dir)
        use_case = GenerateDiagramUseCase(metadata_adapter, diagram_adapter)

        # 2. Get all views
        views = metadata_adapter.load_view_configs()
        console.print(f"Found {len(views)} views. Generating...")

        # 3. Generate each
        for view in views:
            try:
                result = use_case.execute(view.key)
                file_name = f"{view.key}.mmd"
                with open(output_path / file_name, 'w') as f:
                    f.write(result)
                console.print(f"[green]✓ Generated {file_name}[/green]")
            except Exception as e:
                console.print(f"[red]✗ Failed to generate {view.key}: {e}[/red]")

    except Exception as e:
        console.print(f"[red]Fatal Error: {e}[/red]")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    app()
