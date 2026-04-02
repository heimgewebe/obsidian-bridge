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

            # First fallback node is expected to be placed in the fallback grid (y >= 1200).
            # The exact x-position is an internal implementation detail and not asserted.
            self.assertTrue(canvas_nodes1["node:unknown-1"]["y"] >= 1200)

            # Verify that stabilize_layout persisted the layout to cache_path
            with open(cache_path, "r") as f:
                cached_layout = json.load(f)
            self.assertEqual(cached_layout, layout1)

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

            # Auch alte Fallback-Knoten müssen ihre deterministische Position behalten
            self.assertEqual(canvas_nodes2["node:unknown-1"]["x"], canvas_nodes1["node:unknown-1"]["x"])
            self.assertEqual(canvas_nodes2["node:unknown-1"]["y"], canvas_nodes1["node:unknown-1"]["y"])

            # Das Organsystem-Layout positioniert Nodes auf vordefinierten Ankern.
            # (current limitation: Der Algorithmus stapelt derzeit mehrere Treffer desselben
            # Organs noch nicht deterministisch untereinander, sondern platziert sie auf
            # derselben Basis-Koordinate. Das wird hier aber nicht als harte Assertion erzwungen,
            # um zukünftige Verbesserungen am Algorithmus nicht zu blockieren.)
            self.assertIn("node:chronik-2", canvas_nodes2)
            self.assertIn("node:hausKI-2", canvas_nodes2)

            # Unbekannte Knoten wandern ins Fallback-Grid und werden dort deterministisch ergänzt
            self.assertIn("node:unknown-2", canvas_nodes2)
            self.assertTrue(canvas_nodes2["node:unknown-2"]["y"] >= 1200)

            # Sie sollten deterministisch an einem neuen Platz abgelegt werden,
            # ohne die exakte Implementierung des Grids hier starr zu kodieren.
            pos1 = (canvas_nodes2["node:unknown-1"]["x"], canvas_nodes2["node:unknown-1"]["y"])
            pos2 = (canvas_nodes2["node:unknown-2"]["x"], canvas_nodes2["node:unknown-2"]["y"])
            self.assertNotEqual(pos1, pos2)

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

if __name__ == '__main__':
    unittest.main()
