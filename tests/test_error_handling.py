from typing import Any

from diagram_generator.adapters.input.yaml_loader import YAMLMetadataAdapter


def test_load_components_with_errors(tmp_path: Any) -> None:
    # Create bad yaml
    bad_data = tmp_path / "components"
    bad_data.mkdir()
    (bad_data / "bad.yaml").write_text("""
components:
  - id: good-comp
    name: Good
    type: service  
  - id: bad-comp
    name: Bad
    type: invalid_type
    """)
    
    loader = YAMLMetadataAdapter(str(tmp_path))
    # Should not raise, but print errors (captured if we used capsys, but here we check return)
    components = loader.load_components()
    
    assert len(components) == 1
    assert components[0].id == "good-comp"
