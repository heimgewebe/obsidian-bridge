import unittest
import os
import json
import yaml
import tempfile
from scripts.graph.stabilize_layout import stabilize_layout

class TestLayoutStabilityRadial(unittest.TestCase):
    def setUp(self):
        self.graph_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.layout_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.specs_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.specs_dir.cleanup()
        os.unlink(self.graph_file.name)
        os.unlink(self.layout_file.name)

    def test_radial_decision_centered_despite_sorting(self):
        # We purposely name the decision node so it sorts AFTER the event node
        # lexicographically. E.g., "z-decision" vs "a-event".
        graph_data = {
            "nodes": [
                {"id": "a-event", "kind": "event"},
                {"id": "z-decision", "kind": "decision"}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        with open(self.layout_file.name, 'w') as f:
            json.dump({"canvases": {"radial_view": {"nodes": {}}}}, f)

        spec_data = {
            "id": "radial_view",
            "layout": "radial",
            "source": {"artifact_types": ["decision", "event"]}
        }
        spec_file = os.path.join(self.specs_dir.name, 'radial.yaml')
        with open(spec_file, 'w') as f:
            yaml.dump(spec_data, f)

        layout = stabilize_layout(self.graph_file.name, self.layout_file.name, specs_dir=self.specs_dir.name)

        nodes = layout["canvases"]["radial_view"]["nodes"]

        # Even though "z-decision" sorts after "a-event", it should be placed at 0,0
        self.assertEqual(nodes["z-decision"]["x"], 0)
        self.assertEqual(nodes["z-decision"]["y"], 0)

        # The other node should be offset
        self.assertNotEqual(nodes["a-event"]["x"], 0)
        self.assertNotEqual(nodes["a-event"]["y"], 0)


    def test_radial_incremental_stability(self):
        graph_data = {
            "nodes": [
                {"id": "c-decision", "kind": "decision"},
                {"id": "a-event", "kind": "event"},
                {"id": "b-insight", "kind": "insight"}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        # Existing layout has the decision and ONE of the ring nodes.
        existing_layout = {
            "canvases": {
                "radial_view": {
                    "nodes": {
                        "c-decision": {"x": 0, "y": 0, "width": 250, "height": 150},
                        "a-event": {"x": 300, "y": 400, "width": 250, "height": 150}
                    }
                }
            }
        }
        with open(self.layout_file.name, 'w') as f:
            json.dump(existing_layout, f)

        spec_data = {
            "id": "radial_view",
            "layout": "radial",
            "source": {"artifact_types": ["decision", "event", "insight"]}
        }
        spec_file = os.path.join(self.specs_dir.name, 'radial.yaml')
        with open(spec_file, 'w') as f:
            yaml.dump(spec_data, f)

        layout = stabilize_layout(self.graph_file.name, self.layout_file.name, specs_dir=self.specs_dir.name)

        nodes = layout["canvases"]["radial_view"]["nodes"]

        # Assert existing nodes are unchanged
        self.assertEqual(nodes["c-decision"]["x"], 0)
        self.assertEqual(nodes["c-decision"]["y"], 0)

        self.assertEqual(nodes["a-event"]["x"], 300)
        self.assertEqual(nodes["a-event"]["y"], 400)

        # The new node should be positioned deterministically
        self.assertIn("b-insight", nodes)
        self.assertNotEqual(nodes["b-insight"]["x"], 0)
        self.assertNotEqual(nodes["b-insight"]["y"], 0)


if __name__ == '__main__':
    unittest.main()
