import unittest
import os
import json
import yaml
import tempfile
from scripts.graph.stabilize_layout import stabilize_layout

class TestLayoutStabilityTimeline(unittest.TestCase):
    def setUp(self):
        self.graph_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.layout_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.specs_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.specs_dir.cleanup()
        os.unlink(self.graph_file.name)
        os.unlink(self.layout_file.name)

    def test_stabilize_layout_timeline(self):
        graph_data = {
            "nodes": [
                {"id": "node-event-1", "kind": "event", "timestamp": "2023-01-01"},
                {"id": "node-event-2", "kind": "event", "timestamp": "2023-01-02"},
                {"id": "node-insight-1", "kind": "insight", "timestamp": "2023-01-01"}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        with open(self.layout_file.name, 'w') as f:
            json.dump({"canvases": {"timeline_view": {"nodes": {}}}}, f)

        spec_data = {
            "id": "timeline_view",
            "layout": "timeline",
            "source": {"artifact_types": ["event", "insight"]}
        }
        spec_file = os.path.join(self.specs_dir.name, 'timeline.yaml')
        with open(spec_file, 'w') as f:
            yaml.dump(spec_data, f)

        layout = stabilize_layout(self.graph_file.name, self.layout_file.name, specs_dir=self.specs_dir.name)

        self.assertIn("canvases", layout)
        timeline_layout = layout["canvases"]["timeline_view"]
        self.assertIn("nodes", timeline_layout)

        nodes = timeline_layout["nodes"]
        self.assertEqual(nodes["node-event-1"]["y"], 0)   # 'event' comes before 'insight' alphabetically
        self.assertEqual(nodes["node-event-1"]["x"], 0)

        self.assertEqual(nodes["node-event-2"]["y"], 0)
        self.assertEqual(nodes["node-event-2"]["x"], 350) # offset applied

        self.assertEqual(nodes["node-insight-1"]["y"], 300) # next kind offset
        self.assertEqual(nodes["node-insight-1"]["x"], 0)

    def test_stabilize_layout_timeline_incremental(self):
        graph_data = {
            "nodes": [
                {"id": "node-event-1", "kind": "event", "timestamp": "2023-01-01"},
                {"id": "node-event-2", "kind": "event", "timestamp": "2023-01-02"},
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        existing_layout = {
            "canvases": {
                "timeline_view": {
                    "nodes": {
                        "node-event-1": {"x": 500, "y": 0, "width": 250, "height": 150}
                    }
                }
            }
        }
        with open(self.layout_file.name, 'w') as f:
            json.dump(existing_layout, f)

        spec_data = {
            "id": "timeline_view",
            "layout": "timeline",
            "source": {"artifact_types": ["event"]}
        }
        spec_file = os.path.join(self.specs_dir.name, 'timeline.yaml')
        with open(spec_file, 'w') as f:
            yaml.dump(spec_data, f)

        layout = stabilize_layout(self.graph_file.name, self.layout_file.name, specs_dir=self.specs_dir.name)

        nodes = layout["canvases"]["timeline_view"]["nodes"]

        self.assertEqual(nodes["node-event-1"]["x"], 500)
        self.assertEqual(nodes["node-event-1"]["y"], 0)

        # New node should be incrementally offset from the existing node's max X within its kind
        self.assertEqual(nodes["node-event-2"]["x"], 500 + 350)
        self.assertEqual(nodes["node-event-2"]["y"], 0)

if __name__ == '__main__':
    unittest.main()
