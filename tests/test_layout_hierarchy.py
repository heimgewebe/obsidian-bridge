import unittest
import yaml
from scripts.graph.stabilize_layout import stabilize_layout
import os
import tempfile
import json

class TestLayoutHierarchy(unittest.TestCase):
    def test_hierarchy_layout_determinism(self):
        """
        Der Hierarchy-Layout-Algorithmus muss neue Knoten deterministisch
        innerhalb ihrer Hierarchieebene (Konzepte oben, Entitäten mittig, Rest unten)
        positionieren und bestehende Positionen absolut stabil halten.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            graph_path = os.path.join(temp_dir, "graph.json")
            cache_path = os.path.join(temp_dir, "layout.json")
            specs_dir = os.path.join(temp_dir, "specs")
            os.makedirs(specs_dir)

            # Create Spec
            spec = {
                "id": "test-hierarchy",
                "layout": "hierarchy"
            }
            with open(os.path.join(specs_dir, "test-hierarchy.yaml"), "w") as f:
                yaml.dump(spec, f)

            # Create Graph
            graph = {
                "nodes": [
                    {"id": "concept:c1", "kind": "concept"},
                    {"id": "entity:e1", "kind": "entity"},
                    {"id": "event:ev1", "kind": "event"} # Other
                ],
                "edges": []
            }
            with open(graph_path, "w") as f:
                json.dump(graph, f)

            # Run 1: initial generation
            layout1 = stabilize_layout(graph_path, cache_path, specs_dir)
            canvas_nodes1 = layout1["canvases"]["test-hierarchy"]["nodes"]

            # Concepts should be at y=0
            self.assertEqual(canvas_nodes1["concept:c1"]["y"], 0)
            # Entities should be at y=400
            self.assertEqual(canvas_nodes1["entity:e1"]["y"], 400)
            # Alle übrigen Kind-Typen ('other') werden deterministisch auf y=800 gesammelt
            self.assertEqual(canvas_nodes1["event:ev1"]["y"], 800)

            # Save layout cache
            with open(cache_path, "w") as f:
                json.dump(layout1, f)

            # Add more nodes
            graph["nodes"].extend([
                {"id": "concept:c2", "kind": "concept"},
                {"id": "entity:e2", "kind": "entity"},
                {"id": "insight:in1", "kind": "insight"}
            ])
            with open(graph_path, "w") as f:
                json.dump(graph, f)

            # Run 2: stability check
            layout2 = stabilize_layout(graph_path, cache_path, specs_dir)
            canvas_nodes2 = layout2["canvases"]["test-hierarchy"]["nodes"]

            # Old nodes should not move
            self.assertEqual(canvas_nodes2["concept:c1"]["x"], canvas_nodes1["concept:c1"]["x"])
            self.assertEqual(canvas_nodes2["concept:c1"]["y"], canvas_nodes1["concept:c1"]["y"])
            self.assertEqual(canvas_nodes2["entity:e1"]["x"], canvas_nodes1["entity:e1"]["x"])
            self.assertEqual(canvas_nodes2["entity:e1"]["y"], canvas_nodes1["entity:e1"]["y"])

            # New nodes should be placed at appropriate levels and right of existing ones
            self.assertEqual(canvas_nodes2["concept:c2"]["y"], 0)
            self.assertEqual(canvas_nodes2["entity:e2"]["y"], 400)
            self.assertEqual(canvas_nodes2["insight:in1"]["y"], 800)

            self.assertTrue(canvas_nodes2["concept:c2"]["x"] > canvas_nodes2["concept:c1"]["x"])
            self.assertTrue(canvas_nodes2["entity:e2"]["x"] > canvas_nodes2["entity:e1"]["x"])
            self.assertTrue(canvas_nodes2["insight:in1"]["x"] > canvas_nodes2["event:ev1"]["x"])

if __name__ == '__main__':
    unittest.main()
