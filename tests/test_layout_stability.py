import unittest
import os
import json
import tempfile
from scripts.graph.stabilize_layout import stabilize_layout

class TestLayoutStability(unittest.TestCase):
    def setUp(self):
        self.graph_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.layout_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')

        graph_data = {
            "nodes": [{"id": "node-1"}, {"id": "node-2"}]
        }

        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

    def tearDown(self):
        os.unlink(self.graph_file.name)
        os.unlink(self.layout_file.name)

    def test_stabilize_layout_new_nodes(self):
        # Empty layout file initially
        with open(self.layout_file.name, 'w') as f:
            json.dump({"nodes": {}}, f)

        layout = stabilize_layout(self.graph_file.name, self.layout_file.name)

        self.assertIn("nodes", layout)
        self.assertIn("node-1", layout["nodes"])
        self.assertIn("node-2", layout["nodes"])

        node1 = layout["nodes"]["node-1"]
        self.assertEqual(node1["x"], 0)
        self.assertEqual(node1["y"], 0)
        self.assertEqual(node1["width"], 250)
        self.assertEqual(node1["height"], 150)

        node2 = layout["nodes"]["node-2"]
        self.assertEqual(node2["x"], 300)
        self.assertEqual(node2["y"], 0)
        self.assertEqual(node2["width"], 250)
        self.assertEqual(node2["height"], 150)

    def test_stabilize_layout_keeps_existing(self):
        # Pre-populate layout file with existing node position
        existing_layout = {
            "nodes": {
                "node-1": {"x": 500, "y": 600, "width": 100, "height": 100}
            }
        }

        with open(self.layout_file.name, 'w') as f:
            json.dump(existing_layout, f)

        layout = stabilize_layout(self.graph_file.name, self.layout_file.name)

        # Verify node-1 kept its position
        self.assertEqual(layout["nodes"]["node-1"]["x"], 500)
        self.assertEqual(layout["nodes"]["node-1"]["y"], 600)

        # Verify node-2 was added deterministically
        self.assertIn("node-2", layout["nodes"])

if __name__ == '__main__':
    unittest.main()
