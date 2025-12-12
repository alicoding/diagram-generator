import logging
import re
from pathlib import Path
from typing import Any

from glom import Coalesce, glom
from ruamel.yaml import YAML

from diagram_generator.core.domain.component import (
    Component,
    ComponentType,
    Database,
    ExternalSystem,
    GenericComponent,
    Service,
    System,
)
from diagram_generator.core.domain.flow import Flow, FlowStep
from diagram_generator.core.domain.relationship import Relationship

# Configure logging
logger = logging.getLogger(__name__)

class SeedIngester:
    """
    Enterprise-grade Data Ingestion Service.
    Transforms raw seed data into SSOT domain objects using declarative glom specs.
    """
    
    def __init__(self, config_path: str, data_dir: str):
        self.yaml = YAML(typ='safe')
        self.yaml.preserve_quotes = True
        self.yaml.allow_duplicate_keys = True
        self.config = self._load_yaml(config_path)
        self.data_dir = Path(data_dir)
        self.name_map = {} # Maps Name -> ID for relationship resolution

    def ingest(self) -> dict[str, list[Any]]:
        """
        Main ingestion entry point.
        """
        results = {"components": [], "flows": [], "relationships": []}
        
        sources = self.config.get("sources", [])
        for source in sources:
            file_path = self.data_dir / source["file"]
            raw_data = self._load_source(file_path, source.get("format"))
            
            if not raw_data:
                continue

            # Process Components Mappings
            for mapping in self.config.get("mappings", {}).get("components", []):
                items = self._process_mapping(raw_data, mapping)
                for item_data in items:
                    # Validate and Create
                    if item_data.get("id"):
                        comp = self._create_component(item_data, mapping.get("item_model"))
                        if comp:
                            results["components"].append(comp)

            # Process Flows Mappings
            for mapping in self.config.get("mappings", {}).get("flows", []):
                items = self._process_mapping(raw_data, mapping)
                for item_data in items:
                    flow = self._create_flow(item_data)
                    if flow:
                        results["flows"].append(flow)

            # Process Relationships Mappings
            for mapping in self.config.get("mappings", {}).get("relationships", []):
                items = self._process_mapping(raw_data, mapping)
                for item_data in items:
                    rels = self._create_relationships(item_data)
                    results["relationships"].extend(rels)
                
        return results

    def _process_mapping(self, source_data: dict[str, Any], mapping_config: dict) -> list[dict]:
        """
        Uses glom to extract and transform data based on the spec.
        """
        source_path = mapping_config.get("source_path")
        raw_spec = mapping_config.get("spec")
        
        # Build safe spec with defaults
        spec = self._build_safe_spec(raw_spec)
        
        # 1. Extract the list of items
        try:
            raw_items = glom(source_data, source_path, default=[])
        except Exception as e:
            logger.warning(f"Could not extract path {source_path}: {e}")
            return []
            
        if not isinstance(raw_items, list):
             logger.warning(f"Expected list at {source_path}, got {type(raw_items)}")
             return []

        # 2. Transform each item using the spec
        transformed_items = []
        for item in raw_items:
            try:
                # glom transformation
                transformed = glom(item, spec)
                transformed_items.append(transformed)
            except Exception as e:
                logger.warning(f"Transformation failed for item in {source_path}: {e}")
                
        return transformed_items

    def _build_safe_spec(self, spec: Any) -> Any:
        """
        Recursively wraps string paths in Coalesce(path, default=None) 
        to ensure missing keys don't break ingestion.
        """
        if isinstance(spec, dict):
            return {k: self._build_safe_spec(v) for k, v in spec.items()}
        elif isinstance(spec, str):
            # Special indicator for literals? Assuming purely paths for now.
            # If start with T. leave as is?
            if spec.startswith("T."):
                return spec[2:] # Remove T. prefix, assume T object usage if needed, or just let glom handle
            return Coalesce(spec, default=None)
        return spec

    def _create_component(self, data: dict[str, Any], model_type: str) -> Component | None: # noqa: PLR0911
        """
        Factory method to convert dict to Pydantic Component.
        """
        # Sanitize ID
        raw_id = data.get("id")
        if not raw_id:
            return None
            
        clean_id = self._sanitize_id(str(raw_id))
        data["id"] = clean_id
        
        # Register Name -> ID mapping
        if "name" in data:
            self.name_map[data["name"]] = clean_id
            # Also map the ID to itself for safety (in case relationships use ID)
            self.name_map[clean_id] = clean_id
        
        # Defaults
        if "description" not in data or not data["description"]:
             data["description"] = f"Imported {model_type}"

        try:
            # Dispatch based on configured model type
            if model_type == "Service":
                data["type"] = ComponentType.service
                return Service(**data)
            elif model_type == "Database":
                data["type"] = ComponentType.database
                return Database(**data)
            elif model_type == "System":
                data["type"] = ComponentType.system
                return System(**data)
            elif model_type == "ExternalSystem":
                data["type"] = ComponentType.external_system
                return ExternalSystem(**data)
            else:
                data["type"] = ComponentType.generic
                return GenericComponent(**data)
        except Exception as e:
            logger.warning(f"Validation error for component {clean_id}: {e}")
            return None

    def _create_flow(self, data: dict[str, Any]) -> Flow | None:
        """
        Creates a Flow object, attempting to parse text-based directions into steps.
        "App -> Middleware -> Vendor" -> Steps
        """
        if not data.get("id"):
            return None

        clean_id = self._sanitize_id(data["id"])
        description = data.get("description") or clean_id
        metadata = data.get("metadata", {})
        
        steps = []
        
        raw_direction = metadata.get("direction")
        if raw_direction:
            # Parse "A → B → C"
            parts = [p.strip() for p in raw_direction.replace("->", "→").split("→")]
            if len(parts) >= 2: # noqa: PLR2004
                for i in range(len(parts) - 1):
                    src = self._sanitize_id(parts[i])
                    tgt = self._sanitize_id(parts[i+1])
                    steps.append(FlowStep(
                        source_id=src,
                        target_id=tgt,
                        description=f"Step {i+1}"
                    ))
        
        return Flow(id=clean_id, description=description, steps=steps, metadata=metadata)

    def _create_relationships(self, data: dict[str, Any]) -> list[Relationship]:
        """
        Creates Relationship objects from:
        1. source_id -> [targets] list
        2. direction string "A -> B -> C"
        """
        rels = []
        rel_type = data.get("type", "dependency")
        
        # Case 1: Direction String (A -> B -> C)
        direction = data.get("direction")
        if direction:
            parts = [s.strip() for s in direction.split('→') if s.strip()]
            if len(parts) < 2: # noqa: PLR2004
                # Try -> arrow
                parts = [s.strip() for s in direction.split('->') if s.strip()]
                
            for i in range(len(parts) - 1):
                src_name = parts[i]
                tgt_name = parts[i+1]
                
                # Resolve IDs via Name Map
                source = self.name_map.get(src_name, self._sanitize_id(src_name))
                target = self.name_map.get(tgt_name, self._sanitize_id(tgt_name))
                
                rels.append(Relationship(
                    source_id=source,
                    target_id=target,
                    description="flow step",
                    metadata={"type": rel_type}
                ))
            return rels

        # Case 2: Source -> Targets List
        source_id = data.get("source_id")
        targets = data.get("targets")
        
        if not source_id or not targets:
            return []
            
        # Resolve Source ID from Name Map if available
        if source_id in self.name_map:
            source_id = self.name_map[source_id]
            
        clean_source = self._sanitize_id(source_id)
        
        # Ensure targets is a list
        if isinstance(targets, str):
            targets = [targets]
            
        for target in targets:
            if not target:
                continue
                
            # Resolve Target ID from Name Map if available
            resolved_target = target
            if resolved_target in self.name_map:
                resolved_target = self.name_map[resolved_target]
                
            clean_target = self._sanitize_id(resolved_target)
            rels.append(Relationship(
                source_id=clean_source,
                target_id=clean_target,
                description="depends on",
                metadata={"type": rel_type}
            ))
            
        return rels

    def _sanitize_id(self, raw_id: str) -> str:
        # Replace simple separators first
        s = str(raw_id).strip().replace(" ", "_").replace(".", "_")
        # Remove any other characters (e.g., parens)
        return re.sub(r'[^a-zA-Z0-9_\-]', '', s)

    def _load_yaml(self, path: str) -> dict[str, Any]:
        """Loads YAML safely."""
        try:
            with open(path) as f:
                return self.yaml.load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config {path}: {e}")
            raise

    def _load_source(self, path: Path, fmt: str) -> dict[str, Any]:
        """Loads source data with messy YAML handling."""
        if not path.exists():
            print(f"Warning: Source file {path} not found.")
            return {}
            
        with open(path) as f:
            content = f.read()
            
        if fmt == "yaml":
            try:
                return self.yaml.load(content)
            except Exception as e:
                print(f"Error parsing YAML {path}: {e}")
                return {}
        return {}
