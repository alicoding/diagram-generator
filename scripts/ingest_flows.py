import re
from pathlib import Path

import yaml


def ingest_flows(data_dir: str = "./data", input_file: str = "internal-flow.yaml") -> None: # noqa: PLR0912, PLR0915
    input_file_path = Path(data_dir) / input_file
    output_dir = Path("data_internal/flows")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(input_file_path) as f:
        content = f.read()

    sections = re.split(r"(?m)^id:", content)

    flows = []

    for i, section in enumerate(sections[1:]):
        yaml_text = "id:" + section

        try:
            data = yaml.safe_load(yaml_text)
            if not isinstance(data, dict):
                continue

            flow_id = data.get("id")
            if not flow_id:
                continue

            steps = []
            raw_steps = data.get("flow_steps", [])
            for s in raw_steps:
                step_meta = {}
                if "data" in s:
                    step_meta["data_payload"] = s["data"]
                if "note" in s:
                    step_meta["note"] = s["note"]
                if "action" in s:
                    step_meta["original_action"] = s["action"]
                if "type" in s:
                    step_meta["interaction_type"] = s["type"]

                desc = s.get("action", "Interaction").replace("\n", " ").strip()
                if "data" in s:
                    desc += f"\\n[{s['data']}]"

                protocol = s.get("type", None)
                if protocol == "response":
                    protocol = "HTTP 200"

                steps.append(
                    {
                        "source_id": s.get("from"),
                        "target_id": s.get("to"),
                        "description": desc,
                        "protocol": protocol,
                        "metadata": step_meta,
                    }
                )

            flow_meta = {}
            for k, v in data.items():
                if k not in ["id", "name", "flow_steps", "components"]:
                    flow_meta[k] = v

            flow = {
                "id": flow_id,
                "description": data.get("name", "Imported Flow"),
                "steps": steps,
                "tags": [data.get("status", "import")],
                "metadata": flow_meta,
            }
            flows.append(flow)

        except Exception as e:
            print(f"Error parsing flow section {i}: {e}")

    output_file = output_dir / "ingested_flows.yaml"
    with open(output_file, "w") as f:
        yaml.dump({"flows": flows}, f, sort_keys=False)

    print(f"Successfully ingested {len(flows)} flows into {output_file}")

    view_dir = Path("data_internal/views")
    view_config_path = view_dir / "default.yaml"

    try:
        current_views = yaml.safe_load(view_config_path.read_text())
        if "views" not in current_views:
            current_views["views"] = []

        # Avoid duplicates
        existing_keys = {v["key"] for v in current_views["views"]}

        new_views = [
            {
                "key": "flow-phone-verification",
                "title": "Phone Verification Flow",
                "type": "sequence",
                "flow_id": "phone-verification",
            },
            {
                "key": "flow-id-verification",
                "title": "ID Verification Flow",
                "type": "sequence",
                "flow_id": "id-verification",
            },
        ]

        for nv in new_views:
            if nv["key"] not in existing_keys:
                current_views["views"].append(nv)

        with open(view_config_path, "w") as f:
            yaml.dump(current_views, f, sort_keys=False)

    except Exception as e:
        print(f"Error updating views: {e}")


if __name__ == "__main__":
    ingest_flows()
