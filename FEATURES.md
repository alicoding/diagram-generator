# Diagram Generator Features Reference

> **Auto-Generated**: This document is generated directly from the Pydantic models in the code.

## Table of Contents
- [Components](#components)
- [Relationships](#relationships)
- [Views](#views)
- [Flows](#flows)
- [Quick Flow DSL](#quick-flow-dsl)

# Quick Flow DSL
You can define relationships rapidly using the `.flow` text format (powered by Lark).
Place these files in `data/relationships/` or `data/flows/`.

**Syntax:**
```text
Source -> Target : Description
```

**Example:**
```text
User -> Frontend : Clicks Button
Frontend -> Backend : API Request
```

**Implicit Components ("Quick Draw"):**
You do NOT need to define components in YAML first. Any ID used in a `.flow` file that doesn't exist will be automatically created as a Generic Component.

# Components
All components share common fields, but specific types have extra properties.
