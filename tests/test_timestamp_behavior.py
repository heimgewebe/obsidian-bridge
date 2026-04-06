
import json

import yaml

import unittest
import os
import tempfile
from scripts.canvas.render_canvas import render_canvas

class TestTimestampBehavior(unittest.TestCase):
    """
    Ensures that the _parsed_ts optimization does not change the behavior of render_canvas.
    Tests mixed, missing, and invalid timestamp cases.
    """
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.graph_path = os.path.join(self.temp_dir.name, "graph.json")
        self.layout_path = os.path.join(self.temp_dir.name, "layout.json")
        self.spec_path = os.path.join(self.temp_dir.name, "spec.yaml")
        with open(self.layout_path, 'w') as f:
            json.dump({"nodes": {}}, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _run_render(self, spec, nodes):
        with open(self.graph_path, 'w') as f:
            json.dump({"nodes": nodes, "edges": []}, f)
        with open(self.spec_path, 'w') as f:
            yaml.dump(spec, f)
        render_canvas(self.spec_path, self.graph_path, self.layout_path, output_root=self.temp_dir.name)
        output_file = spec.get("output", "default.canvas")
        output_path = os.path.join(self.temp_dir.name, output_file)
        with open(output_path, 'r') as f:
            return json.load(f)

    def test_mixed_timestamps_sorting(self):
        # Mixed: valid ISO, naive, missing, invalid
        nodes = [
            {"id": "naive", "kind": "event", "timestamp": "2026-03-01T12:00:00", "file_path": "naive.md"},
            {"id": "valid", "kind": "event", "timestamp": "2026-03-08T12:00:00Z", "file_path": "valid.md"},
            {"id": "missing", "kind": "event", "file_path": "missing.md"},
            {"id": "invalid", "kind": "event", "timestamp": "garbage", "file_path": "invalid.md"}
        ]
        spec = {
            "id": "test-sort",
            "type": "chronik",
            "output": "canvases/sort.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"prioritize_recent": True}
        }
        canvas = self._run_render(spec, nodes)
        # Expected order: valid (03-08), naive (03-01), then others (deterministic by ID)
        files = [n["file"] for n in canvas["nodes"]]
        self.assertEqual(files[0], "valid.md")
        self.assertEqual(files[1], "naive.md")
        # 'invalid' and 'missing' go last, sorted by ID
        self.assertIn("invalid.md", files[2:])
        self.assertIn("missing.md", files[2:])

    def test_date_window_filter(self):
        nodes = [
            {"id": "new", "kind": "event", "timestamp": "2026-03-10T12:00:00Z", "file_path": "new.md"},
            {"id": "old", "kind": "event", "timestamp": "2026-03-01T12:00:00Z", "file_path": "old.md"},
            {"id": "none", "kind": "event", "file_path": "none.md"}
        ]
        spec = {
            "id": "test-window",
            "type": "chronik",
            "output": "canvases/window.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"date_window_days": 5}
        }
        canvas = self._run_render(spec, nodes)
        files = [n["file"] for n in canvas["nodes"]]
        self.assertEqual(files, ["new.md"])

    def test_calendar_month_filter(self):
        nodes = [
            {"id": "march", "kind": "event", "timestamp": "2026-03-15T12:00:00Z", "file_path": "march.md"},
            {"id": "april", "kind": "event", "timestamp": "2026-04-01T12:00:00Z", "file_path": "april.md"}
        ]
        spec = {
            "id": "test-month",
            "type": "chronik",
            "output": "canvases/month.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"calendar_month": "2026-03"}
        }
        canvas = self._run_render(spec, nodes)
        files = [n["file"] for n in canvas["nodes"]]
        self.assertEqual(files, ["march.md"])

if __name__ == "__main__":
    unittest.main()
