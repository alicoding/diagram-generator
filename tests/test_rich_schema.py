from pathlib import Path

from pydantic import TypeAdapter
from ruamel.yaml import YAML

from diagram_generator.core.domain.component import Component, Database, Service


def test_rich_component_parsing_from_yaml() -> None:
    """Test parsing of rich metadata components loaded from a YAML file."""
    # Point to the directory containing our test yaml
    test_data_dir = Path(__file__).parent / "data"
    
    # We need to mock the directory structure expectation of the loader 
    # or just use the loader's internal method if accessible, 
    # but strictly the loader expects `components/` subdir.
    # For this test, let's treat the test_data_dir as the root and ensure we have strict control.
    # However, our YAML loader specifically looks for 'components/*.yaml'.
    # So we should probably place our test file in tests/data/components/rich_example.yaml
    # For now, let's just parse the file directly to verify the schema, 
    # mimicking what the loader does internally.
    
    # Used to run locally:
    # yaml = YAML(typ='safe')
    
    yaml = YAML(typ='safe')
    yaml_path = test_data_dir / "components/rich_example.yaml"
    
    with open(yaml_path) as f:
        data = yaml.load(f)
        
    components_data = data['components']
    adapter: TypeAdapter[Component] = TypeAdapter(Component)
    
    components = [adapter.validate_python(item) for item in components_data]
    
    # Verify Service
    risk_service = next(c for c in components if c.id == 'risk-service')
    assert isinstance(risk_service, Service)
    assert risk_service.name == "Risk Assessment Platform"
    assert risk_service.deployment is not None
    assert risk_service.deployment.cluster == "GKE - Services"
    assert risk_service.apis_exposed[0].endpoint == "POST /api/v1/assess"

    # 4. Database (Polymorphic)
    risk_db = next(c for c in components if c.id == 'risk-db')
    assert isinstance(risk_db, Database)
    assert risk_db.technology == "PostgreSQL"
    assert risk_db.details is not None
    assert risk_db.details.tables[0].name == "assessments"
