import traceback
from pathlib import Path
from typing import Any

from lark import Lark, Tree, Visitor

try:
    from ruamel.yaml import YAML
except ImportError:
    YAML = None # type: ignore

from diagram_generator.core.domain.component import (
    Component,
    ComponentType,
    Container,
    Database,
    ExternalSystem,
    GenericComponent,
    LegacySystem,
    Person,
    Service,
    System,
    WebUI,
)
from diagram_generator.core.domain.flow import Flow, FlowStep
from diagram_generator.core.domain.relationship import Relationship


class DSLVisitor(Visitor[Any]):
    def __init__(self, flow_id: str):
        self.flow_id = flow_id
        self.relationships: list[Relationship] = []
        self.components: list[Component] = []
        self.flow_steps: list[FlowStep] = []
        self.current_group: str | None = None
        self.last_entity_id: str | None = None

    def connection(self, tree: Tree[Any]) -> None:
        # Children: ID, arrow, ID, [description], [properties]
        args = tree.children
        
        # ID is a terminal (Token), so use it directly
        source_id = str(args[0])
        self.last_entity_id = source_id

        # arrow is likely a Tree if it's a rule 'arrow: ARROW | DARROW'
        # or a Token if it's inlined. Based on grammar, it's a rule.
        arrow_node = args[1]
        if isinstance(arrow_node, Tree):
            arrow = str(arrow_node.children[0])
        else:
            arrow = str(arrow_node)

        target_id = str(args[2])
        self.last_entity_id = target_id
        
        description = ""
        properties: dict[str, Any] = {}
        
        # Iterate remaining args to find description/properties
        for arg in args[3:]:
            if isinstance(arg, Tree):
                if arg.data == "description":
                    description = str(arg.children[0])
                elif arg.data == "properties":
                    properties = self._parse_properties(arg)

        # Create Relationship (Static Model)
        rel = Relationship(
            source_id=source_id,
            target_id=target_id,
            description=description.strip(),
            protocol=None,
            tags=[],
            metadata=properties
        )
        if self.current_group:
            rel.metadata["group"] = self.current_group
        self.relationships.append(rel)

        # Create FlowStep (Behavioral Model)
        step = FlowStep(
            source_id=source_id,
            target_id=target_id,
            description=description.strip(),
            is_dashed=("-->" in arrow),
            protocol=None,
            metadata=properties
        )
        self.flow_steps.append(step)

    def component_def(self, tree: Tree[Any]) -> None: # noqa: PLR0912
        # ID, [type], [properties]
        args = tree.children
        comp_id = str(args[0])
        self.last_entity_id = comp_id
        
        comp_type_enum = ComponentType.generic
        properties: dict[str, Any] = {}
        
        for arg in args[1:]:
             if arg is None:
                 continue
             
             if isinstance(arg, Tree):
                 if arg.data == "type":
                     try:
                         comp_type_enum = ComponentType(str(arg.children[0]).lower())
                     except ValueError:
                         pass
                 elif arg.data == "properties":
                     properties = self._parse_properties(arg)

        # Factory Logic
        common_args = {
            "id": comp_id,
            "name": properties.get("label", comp_id),
            "description": properties.get("description", "Imported from DSL"),
            "metadata": properties
        }

        comp: Component
        if comp_type_enum == ComponentType.person:
            comp = Person(**common_args)
        elif comp_type_enum == ComponentType.system:
            comp = System(**common_args)
        elif comp_type_enum == ComponentType.database:
            comp = Database(**common_args, type=ComponentType.database) 
        elif comp_type_enum == ComponentType.service:
            comp = Service(**common_args)
        elif comp_type_enum == ComponentType.web_ui:
            comp = WebUI(**common_args)
        elif comp_type_enum == ComponentType.container:
            comp = Container(**common_args)
        elif comp_type_enum == ComponentType.external_system:
            comp = ExternalSystem(**common_args)
        elif comp_type_enum == ComponentType.legacy_system:
            comp = LegacySystem(**common_args)
        else:
            comp = GenericComponent(**common_args, type=ComponentType.generic)

        if self.current_group:
            comp.metadata["group"] = self.current_group
            
        self.components.append(comp)

    def group_def(self, tree: Tree[Any]) -> None:
        # group "Name" { statements }
        # tree.children[0] is name (ID or ESCAPED_STRING)
        name_token = tree.children[0]
        # original_group = self.current_group  # Unused
        
        group_name = str(name_token).strip('"')
        self.current_group = group_name
        
        # Traverse children (Lark Visitor is bottom-up, but we need context)
        # Assuming we are using visit_topdown in the loader
        pass

    def note_def(self, tree: Tree[Any]) -> None:
        # note "Text"
        text = str(tree.children[0]).strip('"')
        
        anchor = self.last_entity_id if self.last_entity_id else "NOTE_ANCHOR"
        position = "right of" if self.last_entity_id else "over"

        # Create a FlowStep representing a note
        step = FlowStep(
            source_id=anchor,
            target_id=anchor,
            description=text,
            is_dashed=False,
            protocol=None,
            metadata={"type": "note", "position": position}
        )
        self.flow_steps.append(step)

    def _parse_properties(self, tree: Tree[Any]) -> dict[str, Any]:
        props = {}
        for child in tree.children:
            if isinstance(child, Tree) and child.data == "property":
                key = str(child.children[0])
                val = str(child.children[1]).strip('"')
                props[key] = val
        return props

class DSLLoader:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        grammar_path = Path(__file__).parent.parent.parent / "dsl" / "grammar.lark"
        with open(grammar_path) as f:
            self.grammar = f.read()
        self.parser = Lark(self.grammar, parser='lalr', propagate_positions=True)

    def load_debug(self) -> tuple[list[Component], list[Relationship], list[Flow]]:
        relationships = []
        components = []
        flows = []
        
        target_dirs = [
            self.data_dir / "relationships", 
            self.data_dir / "flows"
        ]
        print(f"DEBUG: DSL Loader Target Dirs: {target_dirs}")
        
        processed_files = set()

        files: list[Path] = []
        for d in target_dirs:
            if d.exists():
                print(f"DEBUG: Scanning dir {d}")
                found = list(d.glob("*.flow"))
                print(f"DEBUG: Found {len(found)} flows in {d}")
                files.extend(found)
            else:
                print(f"DEBUG: Directory {d} does not exist")


        for file_path in files:
            if str(file_path) in processed_files:
                continue
            processed_files.add(str(file_path))
            
            try:
                with open(file_path) as f:
                    text = f.read()
                
                config: dict[str, Any] = {}
                # Parsing YAML Frontmatter
                if text.startswith("---"):
                    parts = text.split("---", 2)
                    if len(parts) >= 3: # noqa: PLR2004
                        frontmatter = parts[1]
                        dsl_content = parts[2]
                        try:
                            if YAML is not None:
                                yaml = YAML(typ='safe')
                                config = yaml.load(frontmatter) or {}
                                # If config is nested under 'config' key
                                if "config" in config:
                                    config = config["config"]
                            text = dsl_content
                        except Exception as e:
                            print(f"Error parsing frontmatter in {file_path}: {e}")
                
                tree = self.parser.parse(text)
                
                # Use TopDown visitor to handle Group Context
                visitor = DSLVisitor(flow_id=file_path.stem)
                
                visitor.visit_topdown(tree)
                
                relationships.extend(visitor.relationships)
                components.extend(visitor.components)
                
                # Create Flow object
                if visitor.flow_steps:
                    flow = Flow(
                        id=file_path.stem, # Filename as ID e.g. "showcase"
                        description=f"Flow loaded from {file_path.name}",
                        steps=visitor.flow_steps,
                        metadata={"source": "dsl", "config": config}
                    )
                    flows.append(flow)
                    
            except Exception as e:
                print(f"Error parsing DSL file {file_path}: {e}")
                traceback.print_exc()

        return components, relationships, flows


