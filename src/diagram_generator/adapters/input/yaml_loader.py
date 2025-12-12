from pathlib import Path
from typing import Any

from pydantic import TypeAdapter
from rich.console import Console
from rich.table import Table
from ruamel.yaml import YAML

from diagram_generator.adapters.input.dsl_loader import DSLLoader
from diagram_generator.core.domain.component import Component
from diagram_generator.core.domain.flow import Flow
from diagram_generator.core.domain.relationship import Relationship
from diagram_generator.core.domain.view_config import ViewConfig
from diagram_generator.core.ports.metadata_port import MetadataPort


class YAMLMetadataAdapter(MetadataPort):
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.yaml = YAML(typ='safe')
        self.dsl_loader = DSLLoader(self.data_path)
        self._dsl_cache: tuple[list[Component], list[Relationship], list[Flow]] | None = None

    def _load_files(self, directory: str) -> list[dict[str, Any]]:
        results = []
        path = self.data_path / directory
        if not path.exists():
            print(f"DEBUG: Path does not exist: {path}")
            return []
        
        print(f"DEBUG: Scanning {path}")
        files = list(path.glob("*.yaml"))
        print(f"DEBUG: Found files: {files}")
        
        for file_path in files:
            with open(file_path) as f:
                for data in self.yaml.load_all(f):
                    if isinstance(data, list):
                        results.extend(data)
                    elif data:
                        results.append(data)
        return results

    def _load_yaml(self, file_path: Path) -> dict[str, Any]:
        """Helper to load a single YAML file."""
        with open(file_path) as f:
            # Explicitly cast or assert dict
            data = self.yaml.load(f)
            if not isinstance(data, dict):
                return {}
            return data

    def _unwrap_data(self, raw_data: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
        """Helper to unwrap data if it's nested under a root key."""
        unwrapped = []
        for item in raw_data:
            if key in item and isinstance(item[key], list):
                unwrapped.extend(item[key])
            else:
                unwrapped.append(item)
        return unwrapped

    def _load_dsl(self) -> tuple[list[Component], list[Relationship], list[Flow]]:
        if self._dsl_cache is None:
            self._dsl_cache = self.dsl_loader.load_debug()
        return self._dsl_cache

    def load_components(self) -> list[Component]:
        raw_data = self._load_files("components")
        data = self._unwrap_data(raw_data, "components")
        adapter: TypeAdapter[Component] = TypeAdapter(Component)
        
        valid_components = []
        errors = []
        
        console = Console()

        for index, item in enumerate(data):
            try:
                valid_components.append(adapter.validate_python(item))
            except Exception as e:
                item_id = item.get("id", f"Index {index}")
                errors.append({"id": item_id, "error": str(e)})

        if errors:
            table = Table(title="[bold red]Validation Errors in Components[/bold red]")
            table.add_column("Component ID", style="cyan")
            table.add_column("Error", style="red")
            
            for err in errors:
                msg = err["error"].split("\n")[0]
                if "Input should be" in err["error"]:
                     msg = err["error"]
                table.add_row(str(err["id"]), msg)
            
            console.print(table)
            console.print("[yellow]Warning: Skipping invalid components.[/yellow]")

        # Merge DSL Components
        dsl_comps, _, _ = self._load_dsl()
        print(f"DEBUG: DSL Components: {[(c.id, c.type) for c in dsl_comps]}")
        
        # Merge Strategy: 
        # 1. Index YAML components by ID
        comp_map = {c.id: c for c in valid_components}
        
        # 2. Update or Append DSL components
        for dsl_c in dsl_comps:
            if dsl_c.id in comp_map:
                # Merge metadata (DSL takes precedence for keys like 'group')
                # But keep YAML name/desc if DSL is generic
                base_c = comp_map[dsl_c.id]
                base_c.metadata.update(dsl_c.metadata)
                # If DSL has detailed properties, usage them? 
                # Usually DSL just adds 'group' here.
            else:
                comp_map[dsl_c.id] = dsl_c
        
        return list(comp_map.values())

    def load_relationships(self) -> list[Relationship]:
        raw_data = self._load_files("relationships")
        data = self._unwrap_data(raw_data, "relationships")
        yaml_rels = [Relationship(**item) for item in data]
        
        # Merge DSL Relationships
        _, dsl_rels, _ = self._load_dsl()
        return yaml_rels + dsl_rels

    def load_view_configs(self) -> list[ViewConfig]:
        raw_data = self._load_files("views")
        data = self._unwrap_data(raw_data, "views")
        return [ViewConfig(**item) for item in data]

    def load_flows(self) -> list[Flow]:
        raw_data = self._load_files("flows")
        data = self._unwrap_data(raw_data, "flows")
        adapter = TypeAdapter(Flow)
        
        valid_flows = []
        for item in data:
            try:
                valid_flows.append(adapter.validate_python(item))
            except Exception as e:
                print(f"Warning: Failed to load flow item: {e}")

        # Merge DSL Flows
        _, _, dsl_flows = self._load_dsl()
        print(f"DEBUG: YAML Flows: {[f.id for f in valid_flows]}")
        print(f"DEBUG: DSL Flows: {[f.id for f in dsl_flows]}")
        all_flows = valid_flows + dsl_flows
        return all_flows
