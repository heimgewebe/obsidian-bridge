import unittest
import os
import tempfile
import json
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
        with open(self.spec_path, 'w') as f:
            import yaml
            yaml.dump(spec, f)
        with open(self.graph_path, 'w') as f:
            json.dump({"nodes": nodes, "edges": []}, f)
        render_canvas(self.spec_path, self.graph_path, self.layout_path, output_root=self.temp_dir.name)
        output_file = spec.get("output", "default.canvas")
        output_path = os.path.join(self.temp_dir.name, output_file)
        with open(output_path, 'r') as f:
            return json.load(f)

    def test_mixed_timestamps_sorting(self):
        nodes = [
            {"id": "naive", "kind": "insight", "timestamp": "2026-03-01T12:00:00", "file_path": "naive.md"},
            {"id": "valid", "kind": "insight", "timestamp": "2026-03-08T12:00:00Z", "file_path": "valid.md"},
            {"id": "missing", "kind": "insight", "file_path": "missing.md"},
            {"id": "invalid", "kind": "insight", "timestamp": "garbage", "file_path": "invalid.md"}
        ]
        spec = {
            "id": "sort",
            "type": "observatorium",
            "source": {"artifact_types": ["insight"]},
            "filters": {"prioritize_recent": True},
            "output": "sort.canvas"
        }
        canvas = self._run_render(spec, nodes)
        files = [n["file"] for n in canvas["nodes"]]
        self.assertEqual(files[0], "valid.md")
        self.assertEqual(files[1], "naive.md")
        self.assertIn("invalid.md", files[2:])
        self.assertIn("missing.md", files[2:])

    def test_date_window_filter(self):
        nodes = [
            {"id": "new", "kind": "insight", "timestamp": "2026-03-10T12:00:00Z", "file_path": "new.md"},
            {"id": "old", "kind": "insight", "timestamp": "2026-03-01T12:00:00Z", "file_path": "old.md"},
            {"id": "none", "kind": "insight", "file_path": "none.md"}
        ]
        spec = {
            "id": "window",
            "type": "observatorium",
            "source": {"artifact_types": ["insight"]},
            "filters": {"date_window_days": 5},
            "output": "window.canvas"
        }
        canvas = self._run_render(spec, nodes)
        files = [n["file"] for n in canvas["nodes"]]
        self.assertEqual(files, ["new.md"])

    def test_calendar_month_filter(self):
        nodes = [
            {"id": "march", "kind": "insight", "timestamp": "2026-03-15T12:00:00Z", "file_path": "march.md"},
            {"id": "april", "kind": "insight", "timestamp": "2026-04-01T12:00:00Z", "file_path": "april.md"}
        ]
        spec = {
            "id": "month",
            "type": "observatorium",
            "source": {"artifact_types": ["insight"]},
            "filters": {"calendar_month": "2026-03"},
            "output": "month.canvas"
        }
        canvas = self._run_render(spec, nodes)
        files = [n["file"] for n in canvas["nodes"]]
        self.assertEqual(files, ["march.md"])

if __name__ == "__main__":
    unittest.main()
