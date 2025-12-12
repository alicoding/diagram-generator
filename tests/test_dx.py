import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from diagram_generator.cli.main import app
from diagram_generator.core.domain.component import ComponentType, Service
from diagram_generator.core.domain.relationship import Relationship
from diagram_generator.core.domain.view_config import Type as DiagramType
from diagram_generator.core.domain.view_config import ViewConfig
from diagram_generator.core.use_cases.generate_diagram import GenerateDiagramUseCase

runner = CliRunner()

def test_schema_generation():
    result = runner.invoke(app, ["schema", "generate"])
    assert result.exit_code == 0
    schema = json.loads(result.stdout)
    assert "UnifiedConfig" in schema["title"]
    assert "components" in schema["properties"]
    assert "views" in schema["properties"]

def test_init_command(tmp_path):
    with patch("diagram_generator.cli.init.Path", side_effect=lambda *args: tmp_path / args[0] if args else tmp_path):
        # We need to run inside tmp_path so the relative path logic works or just pass absolute path
        # Let's pass the path explicitly to the command
        result = runner.invoke(app, ["init", "project", "--path", str(tmp_path), "--name", "TestProject"])
        
    assert result.exit_code == 0
    assert (tmp_path / "data" / "components" / "system.yaml").exists()
    assert (tmp_path / "data" / "views" / "context.yaml").exists()
    assert (tmp_path / "schema.json").exists()
    
    # Verify content
    with open(tmp_path / "data" / "components" / "system.yaml") as f:
        content = f.read()
        assert "TestProject" in content
        assert "$schema=../../schema.json" in content


def test_quick_draw_auto_discovery():
    """Test that missing components are auto-created as 'generic'."""
    # Mock ports
    mock_metadata = MagicMock()
    mock_diagram = MagicMock()
    
    real_comp = Service(id="real", name="Real", type=ComponentType.service)
    # Relationship refers to 'ghost' which doesn't exist
    rel = Relationship(source_id="real", target_id="ghost", description="Who you gonna call?")
    
    mock_metadata.load_components.return_value = [real_comp]
    mock_metadata.load_relationships.return_value = [rel]
    mock_metadata.load_view_configs.return_value = [
        ViewConfig(key="context", title="Ctx", type=DiagramType.c4_context)
    ]
    mock_metadata.load_flows.return_value = []
    
    use_case = GenerateDiagramUseCase(mock_metadata, mock_diagram)
    
    use_case.execute("context")
    
    # Check what was passed to render
    call_args = mock_diagram.render.call_args
    assert call_args is not None
    _, components, _, _ = call_args[0]
    
    # Should now have 2 components: 'real' and 'ghost'
    assert len(components) == 2 # noqa: PLR2004
    ghost = next(c for c in components if c.id == "ghost")
    assert ghost.type == ComponentType.generic
    assert ghost.name == "ghost"

def test_serve_command_mock(tmp_path):
    """Test that serve command attempts to start observer and server."""
    # We patch watchdog classes where they are defined, because they are lazy imported in serve.py
    with patch("watchdog.observers.Observer"), \
         patch("subprocess.run"), \
         patch("diagram_generator.cli.serve.socketserver.TCPServer"), \
         patch("watchdog.events.FileSystemEventHandler"):
        
        # Create dummy data dir
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Invoke with a very short timeout or just interrupt it?
        # Actually server runs forever, tricky to test via runner.invoke without killing it.
        # We can mock TCPServer to raise KeyboardInterrupt immediately?
        
        mock_server_instance = MagicMock()
        mock_server_instance.__enter__.return_value.serve_forever.side_effect = KeyboardInterrupt
        
        with patch("diagram_generator.cli.serve.socketserver.TCPServer", return_value=mock_server_instance):
             result = runner.invoke(app, ["serve", "start", "--data-dir", str(data_dir)])
        
        assert result.exit_code == 0
        assert "Serving live preview" in result.stdout
