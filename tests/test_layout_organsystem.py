import unittest
import yaml
from scripts.graph.stabilize_layout import stabilize_layout
import os
import tempfile
import json

class TestLayoutOrgansystem(unittest.TestCase):
    def test_organsystem_layout_determinism(self):
        """
        Current components keep their fixed anchors. Retired or unknown names use
        the deterministic fallback grid and retain cached positions.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            graph_path = os.path.join(temp_dir, "graph.json")
            cache_path = os.path.join(temp_dir, "layout.json")
            specs_dir = os.path.join(temp_dir, "specs")
            os.makedirs(specs_dir)

            spec = {"id": "test-organsystem", "layout": "organsystem"}
            with open(os.path.join(specs_dir, "test-organsystem.yaml"), "w") as f:
                yaml.dump(spec, f)

            graph = {
                "nodes": [
                    {"id": "node:chronik-1", "title": "Chronik Component"},
                    {"id": "node:hausKI-1", "title": "HausKI Engine"},
                    {"id": "node:heimlern-1", "title": "Heimlern Legacy"},
                    {"id": "node:heimgeist-1", "title": "Heimgeist Legacy"},
                    {"id": "node:unknown-1", "title": "Random Service"},
                ],
                "edges": [],
            }
            with open(graph_path, "w") as f:
                json.dump(graph, f)

            layout1 = stabilize_layout(graph_path, cache_path, specs_dir)
            nodes1 = layout1["canvases"]["test-organsystem"]["nodes"]

            self.assertEqual(nodes1["node:chronik-1"]["x"], 0)
            self.assertEqual(nodes1["node:chronik-1"]["y"], 0)

            fallback_ids = [
                "node:hausKI-1",
                "node:heimlern-1",
                "node:heimgeist-1",
                "node:unknown-1",
            ]
            fallback_positions = []
            for node_id in fallback_ids:
                self.assertGreaterEqual(nodes1[node_id]["y"], 1200)
                fallback_positions.append(
                    (nodes1[node_id]["x"], nodes1[node_id]["y"])
                )
            self.assertEqual(len(fallback_positions), len(set(fallback_positions)))

            with open(cache_path, "r") as f:
                self.assertEqual(json.load(f), layout1)

            graph["nodes"].extend(
                [
                    {"id": "node:chronik-2", "title": "Another Chronik Component"},
                    {"id": "node:hausKI-2", "title": "Another HausKI Component"},
                ]
            )
            with open(graph_path, "w") as f:
                json.dump(graph, f)

            layout2 = stabilize_layout(graph_path, cache_path, specs_dir)
            nodes2 = layout2["canvases"]["test-organsystem"]["nodes"]

            self.assertEqual(nodes2["node:chronik-1"], nodes1["node:chronik-1"])
            for node_id in fallback_ids:
                self.assertEqual(nodes2[node_id], nodes1[node_id])

            self.assertEqual(nodes2["node:chronik-2"]["x"], 0)
            self.assertEqual(nodes2["node:chronik-2"]["y"], 200)

            self.assertGreaterEqual(nodes2["node:hausKI-2"]["y"], 1200)
            all_positions = [(node["x"], node["y"]) for node in nodes2.values()]
            self.assertEqual(len(all_positions), len(set(all_positions)))

    def test_organsystem_stacks_multiple_nodes_by_y_offset(self):
        """Multiple nodes that map to the same organ must be stacked vertically (y += 200 per node).

        Without Y-offset stacking, every additional node for the same organ would be
        placed at the same (fx, fy) coordinate and overlap visually.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            graph_path = os.path.join(temp_dir, "graph.json")
            cache_path = os.path.join(temp_dir, "layout.json")
            specs_dir = os.path.join(temp_dir, "specs")
            os.makedirs(specs_dir)

            spec = {"id": "test-organ-stack", "layout": "organsystem"}
            with open(os.path.join(specs_dir, "test-organ-stack.yaml"), "w") as f:
                yaml.dump(spec, f)

            # Three nodes all mapping to "chronik" (fixed position x=0, y=0)
            graph = {
                "nodes": [
                    {"id": "node:chronik-a", "title": "Chronik A"},
                    {"id": "node:chronik-b", "title": "Chronik B"},
                    {"id": "node:chronik-c", "title": "Chronik C"},
                ],
                "edges": []
            }
            with open(graph_path, "w") as f:
                json.dump(graph, f)

            layout = stabilize_layout(graph_path, cache_path, specs_dir)
            nodes = layout["canvases"]["test-organ-stack"]["nodes"]

            # All three nodes must exist
            self.assertIn("node:chronik-a", nodes)
            self.assertIn("node:chronik-b", nodes)
            self.assertIn("node:chronik-c", nodes)

            # Nodes are processed in sorted-ID order: -a, -b, -c
            # chronik anchor: x=0, y=0; each additional node gets +200 on y
            ys = sorted([nodes["node:chronik-a"]["y"],
                         nodes["node:chronik-b"]["y"],
                         nodes["node:chronik-c"]["y"]])
            self.assertEqual(ys[0], 0)    # first: y=0
            self.assertEqual(ys[1], 200)  # second: y=200
            self.assertEqual(ys[2], 400)  # third: y=400

            # All share the same x anchor (x=0 for chronik)
            xs = {nodes["node:chronik-a"]["x"],
                  nodes["node:chronik-b"]["x"],
                  nodes["node:chronik-c"]["x"]}
            self.assertEqual(xs, {0})

            # No two nodes may share the same (x, y) — no overlap
            positions = [(n["x"], n["y"]) for n in nodes.values()]
            self.assertEqual(len(positions), len(set(positions)))

    def test_organsystem_gap_slot_no_collision(self):
        """New node must not collide when existing nodes occupy non-contiguous slots.

        Scenario: two existing nodes already cached on slot 0 (y=0) and slot 2 (y=400).
        The count-based approach would yield count=2 → y=400, causing a collision.
        The slot-based approach must yield next_slot = max({0,2})+1 = 3 → y=600.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            graph_path = os.path.join(temp_dir, "graph.json")
            cache_path = os.path.join(temp_dir, "layout.json")
            specs_dir = os.path.join(temp_dir, "specs")
            os.makedirs(specs_dir)

            spec = {"id": "test-organ-gap", "layout": "organsystem"}
            with open(os.path.join(specs_dir, "test-organ-gap.yaml"), "w") as f:
                yaml.dump(spec, f)

            graph = {
                "nodes": [
                    {"id": "node:chronik-slot0", "title": "Chronik Slot0"},
                    {"id": "node:chronik-slot2", "title": "Chronik Slot2"},
                    {"id": "node:chronik-new",   "title": "Chronik New"},
                ],
                "edges": []
            }
            with open(graph_path, "w") as f:
                json.dump(graph, f)

            # Pre-populate cache with nodes on slot 0 (y=0) and slot 2 (y=400), leaving slot 1 empty.
            # chronik anchor is (x=0, y=0).
            pre_cache = {
                "canvases": {
                    "test-organ-gap": {
                        "nodes": {
                            "node:chronik-slot0": {"x": 0, "y": 0,   "width": 250, "height": 150},
                            "node:chronik-slot2": {"x": 0, "y": 400, "width": 250, "height": 150},
                        }
                    }
                }
            }
            with open(cache_path, "w") as f:
                json.dump(pre_cache, f)

            layout = stabilize_layout(graph_path, cache_path, specs_dir)
            nodes = layout["canvases"]["test-organ-gap"]["nodes"]

            self.assertIn("node:chronik-new", nodes)
            new_node = nodes["node:chronik-new"]

            # Must land on slot 3 (y=600), not slot 2 (y=400) which is already occupied.
            self.assertEqual(new_node["x"], 0)
            self.assertEqual(new_node["y"], 600)

            # No two nodes share the same (x, y)
            positions = [(n["x"], n["y"]) for n in nodes.values()]
            self.assertEqual(len(positions), len(set(positions)))

    def test_organsystem_two_new_nodes_same_run_no_collision(self):
        """Two new nodes added in the same stabilize run must receive distinct consecutive slots."""
        with tempfile.TemporaryDirectory() as temp_dir:
            graph_path = os.path.join(temp_dir, "graph.json")
            cache_path = os.path.join(temp_dir, "layout.json")
            specs_dir = os.path.join(temp_dir, "specs")
            os.makedirs(specs_dir)

            spec = {"id": "test-organ-tworun", "layout": "organsystem"}
            with open(os.path.join(specs_dir, "test-organ-tworun.yaml"), "w") as f:
                yaml.dump(spec, f)

            graph = {
                "nodes": [
                    {"id": "node:chronik-x", "title": "Chronik X"},
                    {"id": "node:chronik-y", "title": "Chronik Y"},
                ],
                "edges": []
            }
            with open(graph_path, "w") as f:
                json.dump(graph, f)

            layout = stabilize_layout(graph_path, cache_path, specs_dir)
            nodes = layout["canvases"]["test-organ-tworun"]["nodes"]

            self.assertIn("node:chronik-x", nodes)
            self.assertIn("node:chronik-y", nodes)

            # Both must be on x=0 (chronik anchor), on different y values
            self.assertEqual(nodes["node:chronik-x"]["x"], 0)
            self.assertEqual(nodes["node:chronik-y"]["x"], 0)
            self.assertNotEqual(nodes["node:chronik-x"]["y"], nodes["node:chronik-y"]["y"])

            # No two nodes share the same (x, y)
            positions = [(n["x"], n["y"]) for n in nodes.values()]
            self.assertEqual(len(positions), len(set(positions)))

if __name__ == '__main__':
    unittest.main()
