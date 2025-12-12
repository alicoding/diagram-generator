import re
from pathlib import Path

import yaml
from rich.console import Console

console = Console()


def ingest(data_dir: str = "./data", input_file: str = "internal.yaml") -> None: # noqa: PLR0912, PLR0915
    input_path = Path(input_file)
    output_dir = Path(data_dir) / "components"
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(input_path) as f:
        lines = f.readlines()

    blocks = []
    current_buffer = []
    # Types: 'map', 'list', None
    current_type = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            current_buffer.append(line)
            continue

        # Determine line type
        is_list_item = line.startswith("- ")
        # Regex for key (e.g. "actors:") at start of line
        is_key = re.match(r"^[a-z0-9_]+:", line)

        new_type = current_type
        if is_list_item:
            new_type = "list"
        elif is_key:
            new_type = "map"
        elif line.startswith(" "):
            # Continuation of previous block
            pass
        else:
            # Unknown, assume continuation
            pass

        # If type changed, flush buffer
        if current_type is not None and new_type is not None and new_type != current_type:
            # But wait, if we are in a map, a key is valid.
            # If we are in a list, a key means SWITCH to map.
            # If we are in a map, a list item means SWITCH to list.
            # If we are in a map, another key at root is just another key in the SAME map.

            # Refined Logic:
            # Switch triggers:
            # Map -> List (line starts with "- ")
            # List -> Map (line starts with "key:")

            if (current_type == "map" and is_list_item) or (current_type == "list" and is_key):
                blocks.append((current_type, "".join(current_buffer)))
                current_buffer = []
                current_type = new_type

        if current_type is None:
            current_type = new_type

        current_buffer.append(line)

    # Flush final
    if current_buffer and current_type:
        blocks.append((current_type, "".join(current_buffer)))

    components = []

    console.print(f"[bold green]Found {len(blocks)} blocks.[/bold green]")

    for b_type, content in blocks:
        try:
            data = yaml.safe_load(content)
            if not data:
                continue

            if b_type == "list":
                if isinstance(data, list):
                    for item in data:
                        if "id" not in item:
                            continue
                        if "type" not in item:
                            item["type"] = "component"
                        components.append(item)
                else:
                    console.print("[yellow]Warning: List block parsed but wasn't a list?[/yellow]")

            elif b_type == "map":
                if isinstance(data, dict):
                    # Iterate categories (actors, systems, etc.)
                    for category, items in data.items():
                        if not items or not isinstance(items, dict):
                            continue
                        for key, props in items.items():
                            comp_id = props.get("id", key)

                            # Infer type
                            comp_type = props.get("type")
                            if not comp_type:
                                if category == "actors":
                                    comp_type = "person"
                                elif category == "systems":
                                    comp_type = "system"
                                elif category == "vendors":
                                    comp_type = "external_system"
                                elif category == "auxiliary_services":
                                    comp_type = "component"
                                else:
                                    comp_type = "component"

                            if comp_type == "actor":
                                comp_type = "person"
                            if comp_type == "component":
                                comp_type = "service"  # Fix for Pydantic validation
                            if comp_type == "api":
                                comp_type = "service"  # Fix for API type
                            if comp_type == "integration":
                                comp_type = "service" # Fix for Integration type
                            if comp_type == "ui":
                                comp_type = "web_ui"  # Fix for UI type

                            component = {
                                "id": comp_id,
                                "name": props.get("name", key),
                                "type": comp_type,
                                "description": props.get("description", ""),
                                "tags": [category],
                            }
                            # Copy props with sanitization
                            for k, v in props.items():
                                if k in component:
                                    continue

                                # Handle complex fields that might be strings in source
                                if k == "deployment":
                                    if isinstance(v, str):
                                        # Move to metadata
                                        if "metadata" not in component:
                                            component["metadata"] = {}
                                        component["metadata"]["deployment_string"] = v
                                        continue
                                    # If dict, keep it (Service supports it)

                                # Handle nulls
                                if v is None:
                                    continue

                                component[k] = v

                            components.append(component)
                else:
                    console.print("[yellow]Warning: Map block parsed but wasn't a dict?[/yellow]")

        except Exception as e:
            console.print(f"[bold red]Error parsing block ({b_type}): {e}[/bold red]")

    # Remove duplicates (by id)
    unique_components = {}
    for c in components:
        unique_components[c["id"]] = c

    final_list = list(unique_components.values())

    # Save
    output_file = output_dir / "ingested.yaml"
    with open(output_file, "w") as f:
        yaml.dump({"components": final_list}, f, sort_keys=False)

    console.print(
        f"[bold green]Successfully ingested {len(final_list)} unique components into {output_file}[/bold green]"
    )

    # Create default view
    view_dir = Path("data_internal/views")
    view_dir.mkdir(parents=True, exist_ok=True)
    view_config = {
        "views": [
            {
                "key": "internal-landscape",
                "title": "Internal Production Landscape",
                "type": "c4_context",
                "theme": {"primaryColor": "#2E7D32"},
            },
            {
                "key": "internal-containers",
                "title": "Internal Containers",
                "type": "c4_container",
                "filters": {"include_external": True},
            },
        ]
    }
    with open(view_dir / "default.yaml", "w") as f:
        yaml.dump(view_config, f, sort_keys=False)


if __name__ == "__main__":
    ingest()
