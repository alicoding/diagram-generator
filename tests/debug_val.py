from diagram_generator.core.domain.component import Component
from pydantic import TypeAdapter
import yaml

data = """
id: customer
name: Customer
type: person
description: End user (person or business) using Tangerine services
tags:
- actors
metadata:
  participant_name: Customer
  display_name: Customer<br/>(Person or Business)
  icon: "👤"
  use_cases:
  - Person onboarding
  - Business onboarding
  - Account recovery
  style_name: defaultStyle
"""

try:
    obj = yaml.safe_load(data)
    print(f"Testing object: {obj}")
    # Component is a Union. In Pydantic V2 we usually use TypeAdapter to validate into a Union.
    ta = TypeAdapter(Component)
    model = ta.validate_python(obj)
    print(f"Success! Model type: {type(model)}")
except Exception as e:
    print(f"Validation Error: {e}")
