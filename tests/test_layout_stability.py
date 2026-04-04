import unittest
import os
import json
import yaml
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

    def test_stabilize_layout_writes_canvases_format(self):
        """The written JSON file must have the canonical {canvases: {id: {nodes: {...}}}} structure.

        This test reads back the persisted file and validates its top-level shape so that
        render_canvas and stabilize_layout stay in sync on the wire format.
        """
        with open(self.layout_file.name, 'w') as f:
            json.dump({"canvases": {"default": {"nodes": {}}}}, f)

        stabilize_layout(self.graph_file.name, self.layout_file.name, specs_dir=self.specs_dir.name)

        with open(self.layout_file.name, 'r') as f:
            written = json.load(f)

        # Top-level key must be "canvases", not "nodes"
        self.assertIn("canvases", written)
        self.assertNotIn("nodes", written)

        # The canvas entry for "default" must exist and have a "nodes" sub-key
        self.assertIn("default", written["canvases"])
        self.assertIn("nodes", written["canvases"]["default"])

        # Nodes must carry the four geometry fields
        for node_data in written["canvases"]["default"]["nodes"].values():
            self.assertIn("x", node_data)
            self.assertIn("y", node_data)
            self.assertIn("width", node_data)
            self.assertIn("height", node_data)

    def test_stabilize_layout_migrates_flat_format(self):
        """A legacy flat layout file ({nodes: {...}}) must be migrated to the canonical format."""
        flat_layout = {
            "nodes": {
                "node-1": {"x": 10, "y": 20, "width": 250, "height": 150}
            }
        }
        with open(self.layout_file.name, 'w') as f:
            json.dump(flat_layout, f)

        stabilize_layout(self.graph_file.name, self.layout_file.name, specs_dir=self.specs_dir.name)

        with open(self.layout_file.name, 'r') as f:
            written = json.load(f)

        # After migration the file must use the canonical format
        self.assertIn("canvases", written)
        self.assertNotIn("nodes", written)

        # The migrated node must have been moved under canvases.default.nodes
        default_nodes = written["canvases"]["default"]["nodes"]
        self.assertIn("node-1", default_nodes)
        self.assertEqual(default_nodes["node-1"]["x"], 10)
        self.assertEqual(default_nodes["node-1"]["y"], 20)

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

    def test_stabilize_layout_hierarchy(self):
        graph_data = {
            "nodes": [
                {"id": "node-concept", "kind": "concept"},
                {"id": "node-entity", "kind": "entity"},
                {"id": "node-other", "kind": "other"}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        with open(self.layout_file.name, 'w') as f:
            json.dump({"canvases": {"hierarchy": {"nodes": {}}}}, f)

        # Create a spec for hierarchy layout
        spec_data = {
            "id": "hierarchy",
            "layout": "hierarchy",
            "source": {"artifact_types": ["concept", "entity", "other"]}
        }
        spec_file = os.path.join(self.specs_dir.name, 'hierarchy.yaml')
        with open(spec_file, 'w') as f:
            yaml.dump(spec_data, f)

        layout = stabilize_layout(self.graph_file.name, self.layout_file.name, specs_dir=self.specs_dir.name)

        self.assertIn("canvases", layout)
        hierarchy_layout = layout["canvases"]["hierarchy"]
        self.assertIn("nodes", hierarchy_layout)

        # Check y levels based on kind
        nodes = hierarchy_layout["nodes"]
        self.assertEqual(nodes["node-concept"]["y"], 0)
        self.assertEqual(nodes["node-entity"]["y"], 400)
        self.assertEqual(nodes["node-other"]["y"], 800)

    def test_stabilize_layout_hierarchy_incremental(self):
        graph_data = {
            "nodes": [
                {"id": "node-concept-existing", "kind": "concept"},
                {"id": "node-concept-new", "kind": "concept"},
                {"id": "node-entity-existing", "kind": "entity"},
                {"id": "node-entity-new", "kind": "entity"}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        existing_layout = {
            "canvases": {
                "hierarchy": {
                    "nodes": {
                        "node-concept-existing": {"x": 500, "y": 0, "width": 250, "height": 150},
                        "node-entity-existing": {"x": 800, "y": 400, "width": 250, "height": 150}
                    }
                }
            }
        }
        with open(self.layout_file.name, 'w') as f:
            json.dump(existing_layout, f)

        # Create a spec for hierarchy layout
        spec_data = {
            "id": "hierarchy",
            "layout": "hierarchy",
            "source": {"artifact_types": ["concept", "entity"]}
        }
        spec_file = os.path.join(self.specs_dir.name, 'hierarchy.yaml')
        with open(spec_file, 'w') as f:
            yaml.dump(spec_data, f)

        layout = stabilize_layout(self.graph_file.name, self.layout_file.name, specs_dir=self.specs_dir.name)

        nodes = layout["canvases"]["hierarchy"]["nodes"]

        # Ensure existing nodes kept their positions
        self.assertEqual(nodes["node-concept-existing"]["x"], 500)
        self.assertEqual(nodes["node-concept-existing"]["y"], 0)
        self.assertEqual(nodes["node-entity-existing"]["x"], 800)
        self.assertEqual(nodes["node-entity-existing"]["y"], 400)

        # Ensure new nodes are placed incrementally based on the max x of existing nodes in their lane
        self.assertEqual(nodes["node-concept-new"]["x"], 500 + 350)
        self.assertEqual(nodes["node-concept-new"]["y"], 0)
        self.assertEqual(nodes["node-entity-new"]["x"], 800 + 350)
        self.assertEqual(nodes["node-entity-new"]["y"], 400)

if __name__ == '__main__':
    unittest.main()
