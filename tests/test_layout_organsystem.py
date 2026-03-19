import unittest
import yaml
from scripts.graph.stabilize_layout import stabilize_layout
import os
import tempfile
import json

class TestLayoutOrgansystem(unittest.TestCase):
    def test_organsystem_layout_determinism(self):
        """
        Der Organsystem-Layout-Algorithmus muss Repos/Organe auf feste Positionen
        platzieren und neue Nodes in diesen Bahnen deterministisch ergänzen.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            graph_path = os.path.join(temp_dir, "graph.json")
            cache_path = os.path.join(temp_dir, "layout.json")
            specs_dir = os.path.join(temp_dir, "specs")
            os.makedirs(specs_dir)

            # Create Spec
            spec = {
                "id": "test-organsystem",
                "layout": "organsystem"
            }
            with open(os.path.join(specs_dir, "test-organsystem.yaml"), "w") as f:
                yaml.dump(spec, f)

            # Create Graph
            graph = {
                "nodes": [
                    {"id": "node:chronik-1", "title": "Chronik Component"},
                    {"id": "node:hausKI-1", "title": "HausKI Engine"},
                    {"id": "node:unknown-1", "title": "Random Service"}
                ],
                "edges": []
            }
            with open(graph_path, "w") as f:
                json.dump(graph, f)

            # Run 1: initial generation
            layout1 = stabilize_layout(graph_path, cache_path, specs_dir)
            canvas_nodes1 = layout1["canvases"]["test-organsystem"]["nodes"]

            # chronik: x=0, y=0
            # hausKI: x=800, y=0
            # others: below fixed grid (fallback grid) - first index
            self.assertEqual(canvas_nodes1["node:chronik-1"]["x"], 0)
            self.assertEqual(canvas_nodes1["node:chronik-1"]["y"], 0)

            self.assertEqual(canvas_nodes1["node:hausKI-1"]["x"], 800)
            self.assertEqual(canvas_nodes1["node:hausKI-1"]["y"], 0)

            # First fallback node will have x=0 (fallback_index % cols)*width = 0
            # and y = 1200 + (fallback_index // cols)*height
            self.assertEqual(canvas_nodes1["node:unknown-1"]["x"], 0)
            self.assertTrue(canvas_nodes1["node:unknown-1"]["y"] >= 1200)

            # Save layout cache
            with open(cache_path, "w") as f:
                json.dump(layout1, f)

            # Add more nodes
            graph["nodes"].extend([
                {"id": "node:chronik-2", "title": "Another Chronik Component"},
                {"id": "node:hausKI-2", "title": "Another HausKI Component"},
                {"id": "node:unknown-2", "title": "Another unknown"}
            ])
            with open(graph_path, "w") as f:
                json.dump(graph, f)

            # Run 2: stability check
            layout2 = stabilize_layout(graph_path, cache_path, specs_dir)
            canvas_nodes2 = layout2["canvases"]["test-organsystem"]["nodes"]

            # Old nodes should not move
            self.assertEqual(canvas_nodes2["node:chronik-1"]["x"], canvas_nodes1["node:chronik-1"]["x"])
            self.assertEqual(canvas_nodes2["node:chronik-1"]["y"], canvas_nodes1["node:chronik-1"]["y"])

            # Note: Current organsystem layout logic in stabilize_layout.py places multiple matches
            # in the EXACT SAME POSITION! It doesn't stack them currently. It just matches title and puts it at fx, fy.
            # So chronik-2 will also be at 0,0 according to current code logic.
            # Let's verify that this is what happens right now to reflect repo truth.
            self.assertEqual(canvas_nodes2["node:chronik-2"]["x"], 0)
            self.assertEqual(canvas_nodes2["node:chronik-2"]["y"], 0)

            # The unknown-2 will go to fallback grid index
            self.assertTrue(canvas_nodes2["node:unknown-2"]["x"] >= 350) # Assuming next index is 1

if __name__ == '__main__':
    unittest.main()
