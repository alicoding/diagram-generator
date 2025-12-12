# Roadmap

## Vision
Make `diagram-generator` the de-facto standard for **Metadata-Driven Architecture as Code**.

## Q4 2025 (Focus: Developer Experience) - [COMPLETED]

### 1. Robustness "Quick Draw" Mode ✅
- [x] **Goal**: Allow users to draw diagrams without pre-defining every component.
- [x] **Implementation**: Auto-discover missing components in relationships and render them as generic boxes.
- [x] **Value**: Reduces friction for quick prototyping.

### 2. Live Preview Server ✅
- [x] **Goal**: Instant feedback loop.
- [x] **Implementation**: `diagram-generator serve` command.
- [x] **details**: Uses `watchdog` to monitor YAML changes and hot-reload the diagram in the browser.

### 3. LLM Integration (MCP Server) ✅
- [x] **Goal**: Allow AI agents (Claude, Custom Agents) to interact with the architecture.
- [x] **Implementation**: `diagram-generator mcp` command.
- [x] **Capabilities**:
    - `list_components()`
    - `add_service()`
    - `query_graph()`

## Q1 2026 (Focus: Visualization & Cloud)

### 1. Interactive Diagrams
- [ ] Render diagrams using a JS library (e.g., React Flow or D3) instead of static Mermaid images.
- [ ] Click-to-nav for drill-down (System -> Container -> Component).

### 2. Cloud Import
- [ ] Import from AWS/GCP/Azure via Terraform state or API.
- [ ] "Reverse Engineering" the architecture.

### 3. Enterprise Plugins
- [ ] Confluence/Backstage integration (push diagrams to documentation portals).
