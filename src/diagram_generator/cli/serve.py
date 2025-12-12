import http.server
import socketserver
import subprocess
import time
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def start(
    data_dir: Path = typer.Option(Path("./data"), help="Directory containing the metadata."), # noqa: B008
    output_dir: Path = typer.Option(Path("./dist"), help="Output directory."), # noqa: B008
    port: int = typer.Option(8000, help="Port to serve on."),
):
    """
    Starts a live preview server.
    """
    try:
        from watchdog.events import FileSystemEventHandler  # noqa: PLC0415
        from watchdog.observers import Observer  # noqa: PLC0415
    except ImportError:
        console.print("[red]Error: 'watchdog' package not installed.[/red]")
        console.print("Install it with: [cyan]pip install 'diagram-generator[server]'[/cyan] or [cyan]pip install watchdog[/cyan]") # noqa: E501
        raise typer.Exit(1) from None

    class ReloadHandler(FileSystemEventHandler):
        def __init__(self, data_dir: Path, output_dir: Path):
            self.data_dir = data_dir
            self.output_dir = output_dir
            self.last_reload = 0

        def on_any_event(self, event):
            if event.is_directory:
                return
            if not event.src_path.endswith('.yaml'):
                return

            # Debounce
            if time.time() - self.last_reload < 1:
                return
            
            self.last_reload = time.time()
            console.print(f"[yellow]Change detected in {event.src_path}. Regenerating...[/yellow]")
            try:
                # We call the main module to regenerate
                # Using subprocess to avoid complex re-import logic for now
                subprocess.run([
                    "python3", "-m", "diagram_generator.cli.main", "generate-all",
                    "--data-dir", str(self.data_dir),
                    "--output-dir", str(self.output_dir)
                ], check=False)
                console.print("[green]Regenerated![/green]")
            except Exception as e:
                console.print(f"[red]Error regenerating: {e}[/red]")

    if not data_dir.exists():
        console.print(f"[red]Data directory {data_dir} does not exist.[/red]")
        raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Initial generation
    console.print("[bold]Performing initial generation...[/bold]")
    subprocess.run([
        "python3", "-m", "diagram_generator.cli.main", "generate-all",
        "--data-dir", str(data_dir),
        "--output-dir", str(output_dir)
    ], check=False)

    # Start Watcher
    event_handler = ReloadHandler(data_dir, output_dir)
    observer = Observer()
    observer.schedule(event_handler, str(data_dir), recursive=True)
    observer.start()

    # Start HTTP Server
    # We serve the output directory
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(output_dir), **kwargs)

    console.print(f"[green]Serving live preview at http://localhost:{port}[/green]")
    console.print("[dim]Press Ctrl+C to stop.[/dim]")

    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        observer.stop()
        console.print("\n[yellow]Stopping server...[/yellow]")
    
    observer.join()
