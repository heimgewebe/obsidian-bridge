import unittest
import os
import json
import tempfile
import yaml
from scripts.canvas.render_canvas import render_canvas

class TestCanvasRender(unittest.TestCase):
    def setUp(self):
        # Create temp files for graph, layout and spec
        self.graph_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.layout_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.spec_file = tempfile.NamedTemporaryFile(delete=False, suffix='.yaml')

        graph_data = {
            "nodes": [{"id": "evt-1", "kind": "event", "file_path": "chronik/evt.md"}],
            "edges": []
        }

        layout_data = {
            "nodes": {"evt-1": {"x": 10, "y": 20, "width": 100, "height": 50}}
        }

        spec_data = {
            "id": "test-canvas",
            "type": "chronik",
            "output": "canvases/test.canvas",
            "source": {"artifact_types": ["event"]},
            "layout": "timeline"
        }

        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        with open(self.layout_file.name, 'w') as f:
            json.dump(layout_data, f)

        self.temp_dir = tempfile.TemporaryDirectory()
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

    def tearDown(self):
        os.unlink(self.graph_file.name)
        os.unlink(self.layout_file.name)
        os.unlink(self.spec_file.name)
        self.temp_dir.cleanup()

    def test_render_canvas_output(self):
        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/test.canvas")
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r') as f:
            canvas = json.load(f)

        self.assertIn("nodes", canvas)
        self.assertIn("edges", canvas)
        self.assertEqual(len(canvas["nodes"]), 1)

        node = canvas["nodes"][0]
        self.assertEqual(node["type"], "file")
        self.assertEqual(node["file"], "chronik/evt.md")

    def test_render_canvas_size_limit(self):
        # Create a graph with 3 nodes
        graph_data = {
            "nodes": [
                {"id": "evt-1", "kind": "event", "file_path": "chronik/evt1.md"},
                {"id": "evt-2", "kind": "event", "file_path": "chronik/evt2.md"},
                {"id": "evt-3", "kind": "event", "file_path": "chronik/evt3.md"}
            ],
            "edges": []
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        # Spec limits to 2 nodes
        spec_data = {
            "id": "test-limit",
            "type": "chronik",
            "output": "canvases/limit.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"max_nodes": 2}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/limit.canvas")
        with open(output_path, 'r') as f:
            canvas = json.load(f)

        self.assertEqual(len(canvas["nodes"]), 2)

    def test_render_canvas_edge_limit(self):
        # Create a graph with 3 nodes and 3 edges
        graph_data = {
            "nodes": [
                {"id": "evt-1", "kind": "event", "file_path": "chronik/evt1.md"},
                {"id": "evt-2", "kind": "event", "file_path": "chronik/evt2.md"},
                {"id": "evt-3", "kind": "event", "file_path": "chronik/evt3.md"}
            ],
            "edges": [
                {"id": "edge-1", "from": "evt-1", "to": "evt-2", "relation": "references"},
                {"id": "edge-2", "from": "evt-2", "to": "evt-3", "relation": "references"},
                {"id": "edge-3", "from": "evt-3", "to": "evt-1", "relation": "references"}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        # Spec limits to 2 edges
        spec_data = {
            "id": "test-edge-limit",
            "type": "chronik",
            "output": "canvases/edge-limit.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"max_edges": 2}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/edge-limit.canvas")
        with open(output_path, 'r') as f:
            canvas = json.load(f)

        self.assertEqual(len(canvas["nodes"]), 3)
        self.assertEqual(len(canvas["edges"]), 2)

        # Ensure all rendered edges only connect to nodes that exist in the canvas
        canvas_node_ids = {node["id"] for node in canvas["nodes"]}
        for edge in canvas["edges"]:
            self.assertIn(edge["fromNode"], canvas_node_ids)
            self.assertIn(edge["toNode"], canvas_node_ids)

    def test_render_canvas_date_window_positive(self):
        graph_data = {
            "nodes": [
                {"id": "evt-old", "kind": "event", "file_path": "chronik/old.md", "timestamp": "2026-02-01T12:00:00Z"},
                {"id": "evt-mid", "kind": "event", "file_path": "chronik/mid.md", "timestamp": "2026-03-01T12:00:00Z"},
                {"id": "evt-new", "kind": "event", "file_path": "chronik/new.md", "timestamp": "2026-03-08T12:00:00Z"}
            ],
            "edges": [
                {"id": "edge-1", "from": "evt-old", "to": "evt-mid", "relation": "references"},
                {"id": "edge-2", "from": "evt-mid", "to": "evt-new", "relation": "references"}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        # 10 days window from max (2026-03-08) -> cuts off before 2026-02-26
        spec_data = {
            "id": "test-date-window",
            "type": "chronik",
            "output": "canvases/date-window.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"date_window_days": 10}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/date-window.canvas")
        with open(output_path, 'r') as f:
            canvas = json.load(f)

        # Should only include mid and new, but since mid is 2026-03-01, it is within 10 days of 2026-03-08. Wait, 08 - 10 = -2 days... actually Feb 26.
        # So mid is included, new is included. old (Feb 01) is excluded.
        self.assertEqual(len(canvas["nodes"]), 2)
        node_files = [n["file"] for n in canvas["nodes"]]
        self.assertIn("chronik/mid.md", node_files)
        self.assertIn("chronik/new.md", node_files)
        self.assertNotIn("chronik/old.md", node_files)

        # Edge from old to mid should not be present
        self.assertEqual(len(canvas["edges"]), 1)

    def test_render_canvas_mixed_timestamps(self):
        graph_data = {
            "nodes": [
                {"id": "evt-naive", "kind": "event", "file_path": "chronik/naive.md", "timestamp": "2026-03-07T12:00:00"},
                {"id": "evt-aware", "kind": "event", "file_path": "chronik/aware.md", "timestamp": "2026-03-08T12:00:00Z"}
            ],
            "edges": []
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        spec_data = {
            "id": "test-mixed",
            "type": "chronik",
            "output": "canvases/mixed.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"date_window_days": 5}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/mixed.canvas")
        with open(output_path, 'r') as f:
            canvas = json.load(f)

        self.assertEqual(len(canvas["nodes"]), 2)

    def test_render_canvas_missing_timestamps_raises(self):
        graph_data = {
            "nodes": [
                {"id": "evt-none", "kind": "event", "file_path": "chronik/none.md"}
            ],
            "edges": []
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        spec_data = {
            "id": "test-missing",
            "type": "chronik",
            "output": "canvases/missing.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"date_window_days": 5}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        with self.assertRaises(ValueError) as context:
            render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        self.assertIn("no valid timestamps were found", str(context.exception))

if __name__ == '__main__':
    unittest.main()
