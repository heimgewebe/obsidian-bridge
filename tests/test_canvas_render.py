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

        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

    def tearDown(self):
        os.unlink(self.graph_file.name)
        os.unlink(self.layout_file.name)
        os.unlink(self.spec_file.name)

    def test_render_canvas_output(self):
        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name)

        output_path = "vault-gewebe/obsidian-bridge/canvases/test.canvas"
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r') as f:
            canvas = json.load(f)

        self.assertIn("nodes", canvas)
        self.assertIn("edges", canvas)
        self.assertEqual(len(canvas["nodes"]), 1)

        node = canvas["nodes"][0]
        self.assertEqual(node["type"], "file")
        self.assertEqual(node["file"], "chronik/evt.md")

if __name__ == '__main__':
    unittest.main()
