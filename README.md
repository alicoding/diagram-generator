# Diagram Generator

A metadata-driven, FAANG-grade diagram generator following Hexagonal Architecture.

## 🚀 Features

*   **Polyglot Modeling**: Define architecture in **Structure YAML** or **Quick Flow DSL**.
*   **"Quick Draw" Mode**: Write `User -> API` and the system auto-creates the components. No boilerplate.
*   **Live Preview**: `diagram-generator serve` hot-reloads diagrams as you type.
*   **LLM Integration**: Built-in MCP Server for AI agents.
*   **Single Source of Truth**: One metadata set generates Context, Container, and Sequence diagrams.
- **Multi-View Generation**: Context, Container, Sequence, and Flowchart diagrams from a single model.
- **Enterprise Ready**: Validated with MyPy (Strict), Ruff (Linting), and Pytest (Coverage).
- **Mermaid Compatibility**: Robust generation using YAML Frontmatter and standard syntax.

## Architecture
The system uses **Hexagonal Architecture (Ports & Adapters)** to decouple the core logic from external tools.

*   **Core**: Domain entities (`Component`, `Flow`, `ViewConfig`) and Use Cases (`GenerateDiagram`).
*   **Ports**: Interfaces for loading metadata (`MetadataPort`) and rendering diagrams (`DiagramPort`).
*   **Adapters**:
    *   `YAMLMetadataAdapter`: Loads data from local YAML files.
    *   `MermaidDiagramAdapter`: Renders diagrams using Jinja2 templates.

## Installation

```bash
uv pip install .
```

## Quick Start
1.  **Define Components**: Create `data/components/my_system.yaml`.
2.  **Define Views**: Create `data/views/my_views.yaml`.
3.  **Generate**:

```bash
# Check version
diagram-generator version

# Generate all diagrams
diagram-generator generate-all --data-dir ./data --output-dir ./dist
```

## Configuration Guide

### Components (components/*.yaml)
```yaml
components:
  - id: core-service
    name: Core Service
    type: service
    description: Handles business logic.
    technology: Python
```

### Views (views/*.yaml)
```yaml
views:
  - key: context-view
    title: System Context
    type: c4_context
    theme:
      primaryColor: "#E91E63"
```

## Advanced Usage

### Production Data Ingestion
Ingest legacy `internal.yaml` files with rich metadata (JIRA, payloads):
```bash
python3 scripts/ingest_internal.py
python3 scripts/ingest_flows.py
```

### Flow DSL
Combine YAML components with quick DSL flows:
```bash
# interactions.flow
---
config:
    layout: elk
    themeVariables:
        primaryColor: "#ff0000"
---
group "My Group" {
    User -> API : Login
}
API -> DB : Query User
```

### Swimlanes
Use `flowchart_swimlane` view type and DSL `group` syntax to create automatic swimlane diagrams.

## Development

### Running Tests
```bash
pytest
```

### Type Checking
```bash
mypy .
```

### Linting
```bash
ruff check .
```
