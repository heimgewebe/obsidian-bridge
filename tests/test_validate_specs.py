import unittest
import tempfile
import json
import yaml
import os
from scripts.util.validate_specs import validate_specs

class TestValidateSpecs(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.schema_path = os.path.join(self.temp_dir.name, "schema.json")
        self.specs_dir = os.path.join(self.temp_dir.name, "specs")
        os.makedirs(self.specs_dir)

        # Basic valid schema for tests
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "id": {"type": "string"}
            },
            "required": ["id"]
        }
        with open(self.schema_path, "w") as f:
            json.dump(schema, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_valid_spec(self):
        spec_path = os.path.join(self.specs_dir, "valid.yaml")
        with open(spec_path, "w") as f:
            yaml.dump({"id": "test-id"}, f)

        result = validate_specs(self.specs_dir, self.schema_path)
        self.assertEqual(result, 0)

    def test_invalid_yaml(self):
        spec_path = os.path.join(self.specs_dir, "invalid.yaml")
        with open(spec_path, "w") as f:
            f.write("id: [this is broken yaml\n")

        result = validate_specs(self.specs_dir, self.schema_path)
        self.assertEqual(result, 1)

    def test_schema_violation(self):
        spec_path = os.path.join(self.specs_dir, "violation.yaml")
        with open(spec_path, "w") as f:
            yaml.dump({"not_an_id": "test-id"}, f)

        result = validate_specs(self.specs_dir, self.schema_path)
        self.assertEqual(result, 1)

    def test_invalid_schema_json(self):
        with open(self.schema_path, "w") as f:
            f.write("this is not json")

        spec_path = os.path.join(self.specs_dir, "valid.yaml")
        with open(spec_path, "w") as f:
            yaml.dump({"id": "test-id"}, f)

        result = validate_specs(self.specs_dir, self.schema_path)
        self.assertEqual(result, 1)

if __name__ == '__main__':
    unittest.main()
