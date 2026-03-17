import unittest
import yaml
from scripts.graph.stabilize_layout import stabilize_layout
import os
import tempfile
import json

class TestLayoutCluster(unittest.TestCase):
    def test_cluster_layout_determinism(self):
        """
        Der Cluster-Layout-Algorithmus muss neue Knoten deterministisch
        innerhalb ihrer semantischen Cluster (Tags) positionieren und
        bestehende Positionen absolut stabil halten.
        """
        # 1. Setup Mock Data
        with tempfile.TemporaryDirectory() as temp_dir:
            graph_path = os.path.join(temp_dir, "graph.json")
            cache_path = os.path.join(temp_dir, "layout.json")
            specs_dir = os.path.join(temp_dir, "specs")
            os.makedirs(specs_dir)

            spec_path = os.path.join(specs_dir, "cluster-spec.yaml")
            spec = {
                "id": "cluster-test",
                "layout": "cluster",
                "source": {
                    "artifact_types": ["insight"]
                }
            }
            with open(spec_path, "w", encoding="utf-8") as f:
                yaml.dump(spec, f)

            # 2. Initial Run with some nodes
            graph_data = {
                "nodes": [
                    {"id": "ins:1", "kind": "insight", "tags": ["alpha", "beta"]},
                    {"id": "ins:2", "kind": "insight", "tags": ["alpha"]},
                    {"id": "ins:3", "kind": "insight", "tags": ["gamma"]},
                    {"id": "ins:4", "kind": "insight", "tags": []}
                ],
                "edges": []
            }
            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(graph_data, f)

            stabilize_layout(graph_path, cache_path, specs_dir)

            with open(cache_path, "r", encoding="utf-8") as f:
                layout = json.load(f)

            nodes = layout["canvases"]["cluster-test"]["nodes"]

            self.assertIn("ins:1", nodes)
            self.assertIn("ins:2", nodes)
            self.assertIn("ins:3", nodes)
            self.assertIn("ins:4", nodes)

            pos1_y = nodes["ins:1"]["y"]
            pos2_y = nodes["ins:2"]["y"]
            pos3_x = nodes["ins:3"]["x"]
            pos4_x = nodes["ins:4"]["x"]

            # Nodes with same primary tag should share X-offset or be grouped deterministically
            self.assertEqual(nodes["ins:1"]["x"], nodes["ins:2"]["x"])

            # ins:3 is gamma, so different X offset from alpha
            self.assertNotEqual(nodes["ins:1"]["x"], pos3_x)

            # ins:4 is untagged, so deterministically placed in its own cluster
            self.assertNotEqual(nodes["ins:1"]["x"], pos4_x)
            self.assertNotEqual(pos3_x, pos4_x)

            # 3. Second Run with new node
            graph_data["nodes"].append(
                {"id": "ins:5", "kind": "insight", "tags": ["alpha"]}
            )
            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(graph_data, f)

            stabilize_layout(graph_path, cache_path, specs_dir)

            with open(cache_path, "r", encoding="utf-8") as f:
                layout_new = json.load(f)

            nodes_new = layout_new["canvases"]["cluster-test"]["nodes"]

            # Stable positions
            self.assertEqual(nodes_new["ins:1"]["y"], pos1_y)
            self.assertEqual(nodes_new["ins:2"]["y"], pos2_y)
            self.assertEqual(nodes_new["ins:3"]["x"], pos3_x)

            # New node in same cluster gets a deterministic new Y-offset
            self.assertEqual(nodes_new["ins:5"]["x"], nodes_new["ins:1"]["x"])
            self.assertGreater(nodes_new["ins:5"]["y"], nodes_new["ins:2"]["y"])

if __name__ == '__main__':
    unittest.main()
