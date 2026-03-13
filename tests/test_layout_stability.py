import unittest
import os
import json
import tempfile
from scripts.graph.stabilize_layout import stabilize_layout

class TestLayoutStability(unittest.TestCase):
    def setUp(self):
        self.graph_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.layout_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')

        # Wir stellen ein temporäres specs_dir bereit, erzeugen darin aber keine Specs.
        # Deshalb greift in stabilize_layout der eingebaute Fallback-Spec:
        # [{"id": "default", "layout": "grid"}]
        # Da dieser Fallback-Spec keine artifact_types-Filter definiert,
        # ist im Testgraphen kein 'kind'-Attribut bei den Nodes zwingend nötig.
        self.specs_dir = tempfile.TemporaryDirectory()

        graph_data = {
            "nodes": [{"id": "node-1"}, {"id": "node-2"}]
        }

        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

    def tearDown(self):
        self.specs_dir.cleanup()
        os.unlink(self.graph_file.name)
        os.unlink(self.layout_file.name)

    def test_stabilize_layout_new_nodes(self):
        # Empty layout file initially
        with open(self.layout_file.name, 'w') as f:
            json.dump({"canvases": {"default": {"nodes": {}}}}, f)

        layout = stabilize_layout(self.graph_file.name, self.layout_file.name, specs_dir=self.specs_dir.name)

        self.assertIn("canvases", layout)
        default_layout = layout["canvases"]["default"]

        self.assertIn("nodes", default_layout)
        self.assertIn("node-1", default_layout["nodes"])
        self.assertIn("node-2", default_layout["nodes"])

        node1 = default_layout["nodes"]["node-1"]
        self.assertEqual(node1["x"], 0)
        self.assertEqual(node1["y"], 0)
        self.assertEqual(node1["width"], 250)
        self.assertEqual(node1["height"], 150)

        node2 = default_layout["nodes"]["node-2"]
        self.assertEqual(node2["x"], 300)
        self.assertEqual(node2["y"], 0)
        self.assertEqual(node2["width"], 250)
        self.assertEqual(node2["height"], 150)

    def test_stabilize_layout_keeps_existing(self):
        # Pre-populate layout file with existing node position
        existing_layout = {
            "canvases": {
                "default": {
                    "nodes": {
                        "node-1": {"x": 500, "y": 600, "width": 100, "height": 100}
                    }
                }
            }
        }

        with open(self.layout_file.name, 'w') as f:
            json.dump(existing_layout, f)

        layout = stabilize_layout(self.graph_file.name, self.layout_file.name, specs_dir=self.specs_dir.name)
        default_layout = layout["canvases"]["default"]

        # Verify node-1 kept its position
        self.assertEqual(default_layout["nodes"]["node-1"]["x"], 500)
        self.assertEqual(default_layout["nodes"]["node-1"]["y"], 600)

        # Verify node-2 was added deterministically
        self.assertIn("node-2", default_layout["nodes"])

    def test_stabilize_layout_removes_stale(self):
        # Pre-populate layout file with existing and stale node positions
        existing_layout = {
            "canvases": {
                "default": {
                    "nodes": {
                        "node-1": {"x": 500, "y": 600, "width": 100, "height": 100},
                        "stale-node": {"x": 800, "y": 900, "width": 100, "height": 100}
                    }
                }
            }
        }

        with open(self.layout_file.name, 'w') as f:
            json.dump(existing_layout, f)

        layout = stabilize_layout(self.graph_file.name, self.layout_file.name, specs_dir=self.specs_dir.name)
        default_layout = layout["canvases"]["default"]

        # Verify stale node is removed to prevent layout drift
        self.assertNotIn("stale-node", default_layout["nodes"])
        self.assertIn("node-1", default_layout["nodes"])

        # Verify node-2 doesn't "march away" due to stale node index counting
        # new_node_index should be 1, since "stale-node" is deleted before node-2 is placed.
        # grid_cols = 5, cell_width = 300, cell_height = 200
        # => x = 1 * 300 = 300, y = 0
        node2 = default_layout["nodes"]["node-2"]
        self.assertEqual(node2["x"], 300)
        self.assertEqual(node2["y"], 0)

    def test_stabilize_layout_robustness_empty_spec(self):
        """Test that empty or comment-only YAML spec files do not crash the layout generation."""
        empty_spec_file = os.path.join(self.specs_dir.name, 'empty.yaml')
        with open(empty_spec_file, 'w') as f:
            f.write("# Just a comment\n")

        with open(self.layout_file.name, 'w') as f:
            json.dump({"canvases": {"default": {"nodes": {}}}}, f)

        # Should not raise any exceptions despite the empty/comment-only YAML
        layout = stabilize_layout(self.graph_file.name, self.layout_file.name, specs_dir=self.specs_dir.name)

        self.assertIn("canvases", layout)
        default_layout = layout["canvases"]["default"]
        self.assertIn("nodes", default_layout)
        self.assertIn("node-1", default_layout["nodes"])

if __name__ == '__main__':
    unittest.main()
