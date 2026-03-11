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

if __name__ == '__main__':
    unittest.main()
