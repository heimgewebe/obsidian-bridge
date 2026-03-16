import os
import sys
import json
import yaml
try:
    import jsonschema
except ImportError:
    print("Error: jsonschema not installed. Required for spec validation in CI/Build.", file=sys.stderr)
    sys.exit(1)

def validate_specs(specs_dir: str, schema_path: str) -> int:
    if not os.path.exists(schema_path):
        print(f"Error: Schema not found at {schema_path}", file=sys.stderr)
        return 1

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Schema at {schema_path} is invalid JSON: {e}", file=sys.stderr)
        return 1

    errors = 0
    # Walk and sort for deterministic output
    for root, dirs, files in os.walk(specs_dir):
        dirs.sort()
        files.sort()
        for file in files:
            if not file.endswith('.yaml'):
                continue

            spec_path = os.path.join(root, file)
            with open(spec_path, 'r', encoding='utf-8') as f:
                try:
                    spec = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    print(f"Error parsing YAML in {spec_path}: {e}", file=sys.stderr)
                    errors += 1
                    continue

                if not isinstance(spec, dict):
                    print(f"Error: {spec_path} does not contain a valid YAML dictionary.", file=sys.stderr)
                    errors += 1
                    continue

                try:
                    jsonschema.validate(instance=spec, schema=schema)
                    # print(f"Validated {spec_path} successfully.")
                except jsonschema.exceptions.ValidationError as e:
                    print(f"Validation error in {spec_path}: {e.message}", file=sys.stderr)
                    errors += 1

    if errors > 0:
        print(f"Failed: {errors} spec validation errors found.", file=sys.stderr)
        return 1
    else:
        print("All specs validated successfully against schema.")
        return 0

if __name__ == '__main__':
    schema_file = "contracts/canvas-spec.v1.json"
    specs_folder = "config/canvas-specs"
    sys.exit(validate_specs(specs_folder, schema_file))
