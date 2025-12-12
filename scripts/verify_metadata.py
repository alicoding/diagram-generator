from diagram_generator.adapters.input.yaml_loader import YAMLMetadataAdapter

loader = YAMLMetadataAdapter("data_internal")
flows = loader.load_flows()

print(f"Loaded {len(flows)} flows.")
for f in flows:
    if f.metadata:
        print(f"Flow '{f.id}' has metadata keys: {list(f.metadata.keys())}")
        if f.id == "phone-verification":
            print(f"  Example Metadata: {f.metadata}")
    
    # Check steps
    for s in f.steps:
        if s.metadata:
            print(f"  Step to '{s.target_id}' has metadata: {s.metadata}")
            break # Just one example
