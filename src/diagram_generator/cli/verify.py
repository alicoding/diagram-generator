
import typer
from pathlib import Path
from rich.console import Console

from diagram_generator.adapters.input.yaml_loader import YAMLMetadataAdapter
from diagram_generator.core.verification.mermaid_verifier import MermaidVerifier

app = typer.Typer()
console = Console()

@app.command()
def view(
    view_key: str = typer.Argument(..., help="The key of the view to verify."),
    data_dir: str = typer.Option("./data", help="Directory containing the metadata."),
    dist_dir: str = typer.Option("./dist", help="Directory containing generated diagrams.")
) -> None:
    """
    Verifies that a generated diagram matches its source of truth.
    """
    try:
        # Load Metadata
        adapter = YAMLMetadataAdapter(data_dir)
        view_configs = adapter.load_view_configs()
        flows = adapter.load_flows()
        
        # Find View
        view = next((v for v in view_configs if v.key == view_key), None)
        if not view:
            console.print(f"[red]View '{view_key}' not found in metadata.[/red]")
            raise typer.Exit(code=1)
            
        if not view.flow_id:
            console.print(f"[yellow]View '{view_key}' is not linked to a flow. Verification only supports Flows currently.[/yellow]")
            return

        flow = next((f for f in flows if f.id == view.flow_id), None)
        if not flow:
            console.print(f"[red]Flow '{view.flow_id}' not found.[/red]")
            raise typer.Exit(code=1)

        # Load Generated File
        mmd_path = Path(dist_dir) / f"{view.key}.mmd"
        if not mmd_path.exists():
            console.print(f"[red]Generated file {mmd_path} does not exist. Run generate-all first.[/red]")
            raise typer.Exit(code=1)

        # Verify
        console.print(f"Verifying [bold]{view.key}[/bold] against flow [bold]{flow.id}[/bold]...")
        verifier = MermaidVerifier()
        result = verifier.verify_flow(flow, mmd_path.read_text())

        if result.success:
            console.print(f"[green]✓ Verification Passed[/green]")
        else:
            console.print(f"[red]✗ Verification Failed[/red]")
            for err in result.errors:
                console.print(f"  - {err}")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
