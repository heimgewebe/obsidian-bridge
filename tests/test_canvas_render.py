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

        # The cutoff date is 2026-03-08 minus 10 days (2026-02-26).
        # Therefore, 'mid' (2026-03-01) and 'new' (2026-03-08) are included, while 'old' (2026-02-01) is excluded.
        self.assertEqual(len(canvas["nodes"]), 2)
        node_files = [n["file"] for n in canvas["nodes"]]
        self.assertIn("chronik/mid.md", node_files)
        self.assertIn("chronik/new.md", node_files)
        self.assertNotIn("chronik/old.md", node_files)

        # Edge from old to mid should not be present
        self.assertEqual(len(canvas["edges"]), 1)

    def test_render_canvas_calendar_month(self):
        graph_data = {
            "nodes": [
                {"id": "evt-feb", "kind": "event", "file_path": "chronik/feb.md", "timestamp": "2026-02-15T12:00:00Z"},
                {"id": "evt-mar1", "kind": "event", "file_path": "chronik/mar1.md", "timestamp": "2026-03-01T12:00:00Z"},
                {"id": "evt-mar2", "kind": "event", "file_path": "chronik/mar2.md", "timestamp": "2026-03-31T23:59:59Z"},
                {"id": "evt-apr", "kind": "event", "file_path": "chronik/apr.md", "timestamp": "2026-04-01T00:00:00Z"},
                {"id": "evt-none", "kind": "event", "file_path": "chronik/none.md"}
            ],
            "edges": []
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        spec_data = {
            "id": "test-calendar-month",
            "type": "chronik",
            "output": "canvases/calendar-month.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"calendar_month": "2026-03"}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/calendar-month.canvas")
        with open(output_path, 'r') as f:
            canvas = json.load(f)

        self.assertEqual(len(canvas["nodes"]), 2)
        node_files = [n["file"] for n in canvas["nodes"]]
        self.assertIn("chronik/mar1.md", node_files)
        self.assertIn("chronik/mar2.md", node_files)
        self.assertNotIn("chronik/feb.md", node_files)
        self.assertNotIn("chronik/apr.md", node_files)
        self.assertNotIn("chronik/none.md", node_files)

    def test_render_canvas_calendar_month_timezone_boundary(self):
        graph_data = {
            "nodes": [
                # In UTC, 2026-03-31T23:00:00-02:00 corresponds to 2026-04-01T01:00:00Z.
                # It should belong to April, not March.
                {"id": "evt-bound1", "kind": "event", "file_path": "chronik/boundary.md", "timestamp": "2026-03-31T23:00:00-02:00"}
            ],
            "edges": []
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        # Test if it's correctly skipped for March
        spec_data = {
            "id": "test-boundary",
            "type": "chronik",
            "output": "canvases/boundary.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"calendar_month": "2026-03"}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)
        with open(os.path.join(self.temp_dir.name, "canvases/boundary.canvas"), 'r') as f:
            canvas = json.load(f)
        self.assertEqual(len(canvas["nodes"]), 0)

        # Test if it correctly shows up in April
        spec_data["filters"]["calendar_month"] = "2026-04"
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)
        with open(os.path.join(self.temp_dir.name, "canvases/boundary.canvas"), 'r') as f:
            canvas = json.load(f)
        self.assertEqual(len(canvas["nodes"]), 1)

    def test_render_canvas_invalid_calendar_month_raises(self):
        graph_data = {"nodes": [{"id": "evt-1", "kind": "event", "file_path": "1.md"}], "edges": []}
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        # Test non-string
        spec_data_type = {
            "id": "test-type", "type": "chronik", "output": "canvases/type.canvas",
            "source": {"artifact_types": ["event"]}, "filters": {"calendar_month": 202603}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data_type, f)

        with self.assertRaises(ValueError) as context:
            render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)
        self.assertIn("Must be a string", str(context.exception))

        # Test out of bounds month
        spec_data_bounds = {
            "id": "test-bounds", "type": "chronik", "output": "canvases/bounds.canvas",
            "source": {"artifact_types": ["event"]}, "filters": {"calendar_month": "2026-13"}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data_bounds, f)

        with self.assertRaises(ValueError) as context:
            render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)
        self.assertIn("Must be a valid month in YYYY-MM format", str(context.exception))

        # Test wrong format
        spec_data_format = {
            "id": "test-format", "type": "chronik", "output": "canvases/format.canvas",
            "source": {"artifact_types": ["event"]}, "filters": {"calendar_month": "2026/03"}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data_format, f)

        with self.assertRaises(ValueError) as context:
            render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)
        self.assertIn("Must be a valid month in YYYY-MM format", str(context.exception))


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

    def test_render_canvas_invalid_date_window_raises(self):
        graph_data = {
            "nodes": [
                {"id": "evt-1", "kind": "event", "file_path": "chronik/1.md", "timestamp": "2026-03-08T12:00:00Z"}
            ],
            "edges": []
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        # Test negative value
        spec_data_negative = {
            "id": "test-negative",
            "type": "chronik",
            "output": "canvases/negative.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"date_window_days": -5}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data_negative, f)

        with self.assertRaises(ValueError) as context:
            render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)
        self.assertIn("Must be a non-negative integer", str(context.exception))

        # Test non-integer value
        spec_data_string = {
            "id": "test-string",
            "type": "chronik",
            "output": "canvases/string.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"date_window_days": "foo"}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data_string, f)

        with self.assertRaises(ValueError) as context:
            render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)
        self.assertIn("Must be a non-negative integer", str(context.exception))

    def test_render_canvas_invalid_max_depth_raises(self):
        graph_data = {
            "nodes": [
                {"id": "evt-1", "kind": "event", "file_path": "chronik/1.md"}
            ],
            "edges": []
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        # Test negative value
        spec_data_negative = {
            "id": "test-depth-negative",
            "type": "chronik",
            "output": "canvases/depth-negative.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"max_depth": -1}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data_negative, f)

        with self.assertRaises(ValueError) as context:
            render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)
        self.assertIn("Must be a non-negative integer", str(context.exception))

    def test_render_canvas_invalid_max_clusters_raises(self):
        graph_data = {
            "nodes": [
                {"id": "evt-1", "kind": "event", "file_path": "chronik/1.md"}
            ],
            "edges": []
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        # Test negative value
        spec_data_negative = {
            "id": "test-clusters-negative",
            "type": "chronik",
            "output": "canvases/clusters-negative.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"max_clusters": 0}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data_negative, f)

        with self.assertRaises(ValueError) as context:
            render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)
        self.assertIn("Must be an integer >= 1", str(context.exception))

    def test_render_canvas_max_depth(self):
        graph_data = {
            "nodes": [
                {"id": "root", "kind": "concept", "file_path": "root.md"},
                {"id": "child1", "kind": "concept", "file_path": "child1.md"},
                {"id": "child2", "kind": "concept", "file_path": "child2.md"},
                {"id": "grandchild", "kind": "concept", "file_path": "grandchild.md"},
                {"id": "event_cause", "kind": "event", "file_path": "event_cause.md"}
            ],
            "edges": [
                {"id": "e1", "from": "root", "to": "child1", "relation": "references"},
                {"id": "e2", "from": "root", "to": "child2", "relation": "references"},
                {"id": "e3", "from": "child1", "to": "grandchild", "relation": "references"},
                {"id": "e_event_cause", "from": "event_cause", "to": "root", "relation": "references"}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        spec_data = {
            "id": "test-depth",
            "type": "knowledge",
            "output": "canvases/depth.canvas",
            "source": {"artifact_types": ["concept"]},
            "relations": ["references"],
            "filters": {"max_depth": 1}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/depth.canvas")
        with open(output_path, 'r') as f:
            canvas = json.load(f)

        self.assertEqual(len(canvas["nodes"]), 3)
        node_files = [n["file"] for n in canvas["nodes"]]
        self.assertIn("root.md", node_files)
        self.assertIn("child1.md", node_files)
        self.assertIn("child2.md", node_files)
        self.assertNotIn("grandchild.md", node_files)

    def test_render_canvas_max_clusters(self):
        graph_data = {
            "nodes": [
                {"id": "n1", "kind": "concept", "file_path": "n1.md", "tags": ["clusterA"]},
                {"id": "n2", "kind": "concept", "file_path": "n2.md", "tags": ["clusterA"]},
                {"id": "n3", "kind": "concept", "file_path": "n3.md", "tags": ["clusterB"]},
                {"id": "n4", "kind": "concept", "file_path": "n4.md", "tags": ["clusterC"]},
                {"id": "n_notag", "kind": "concept", "file_path": "notag.md", "tags": []}
            ],
            "edges": []
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        spec_data = {
            "id": "test-clusters",
            "type": "knowledge",
            "output": "canvases/clusters.canvas",
            "source": {"artifact_types": ["concept"]},
            "filters": {"max_clusters": 2}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/clusters.canvas")
        with open(output_path, 'r') as f:
            canvas = json.load(f)

        # clusterA has 2 nodes, clusterB and clusterC have 1 node.
        # Ties are broken deterministically by alphabetical order of the tag name.
        # Therefore, clusterA and clusterB are strictly selected.
        # Exactly 3 nodes should be rendered.
        self.assertEqual(len(canvas["nodes"]), 3)
        node_files = [n["file"] for n in canvas["nodes"]]
        self.assertIn("n1.md", node_files)
        self.assertIn("n2.md", node_files)
        self.assertIn("n3.md", node_files)
        self.assertNotIn("n4.md", node_files)

    def test_render_canvas_prioritized_relations(self):
        graph_data = {
            "nodes": [
                {"id": "evt-1", "kind": "event", "file_path": "chronik/evt1.md"},
                {"id": "evt-2", "kind": "event", "file_path": "chronik/evt2.md"},
                {"id": "evt-3", "kind": "event", "file_path": "chronik/evt3.md"}
            ],
            "edges": [
                # Notice we define edges out of priority order to verify deterministic sorting
                {"id": "edge-z-unimportant", "from": "evt-3", "to": "evt-1", "relation": "references"},
                {"id": "edge-a-causes", "from": "evt-1", "to": "evt-2", "relation": "causes"},
                {"id": "edge-b-informed", "from": "evt-2", "to": "evt-3", "relation": "informed"}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        # Spec limits to 2 edges, prioritizes 'informed' then 'causes'
        spec_data = {
            "id": "test-priority",
            "type": "chronik",
            "output": "canvases/priority.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {
                "max_edges": 2,
                "prioritized_relations": ["informed", "causes"]
            }
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/priority.canvas")
        with open(output_path, 'r') as f:
            canvas = json.load(f)

        self.assertEqual(len(canvas["edges"]), 2)
        rendered_relations = [edge["label"] for edge in canvas["edges"]]

        # We expect 'informed' and 'causes' to be rendered, while 'references' gets truncated out
        self.assertIn("informed", rendered_relations)
        self.assertIn("causes", rendered_relations)
        self.assertNotIn("references", rendered_relations)

    def test_render_canvas_fallback_edge_id(self):
        graph_data = {
            "nodes": [
                {"id": "evt-1", "kind": "event", "file_path": "chronik/evt1.md"},
                {"id": "evt-2", "kind": "event", "file_path": "chronik/evt2.md"}
            ],
            "edges": [
                {"from": "evt-1", "to": "evt-2", "relation": "references"} # No explicit ID
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        spec_data = {
            "id": "test-fallback",
            "type": "chronik",
            "output": "canvases/fallback.canvas",
            "source": {"artifact_types": ["event"]}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/fallback.canvas")
        with open(output_path, 'r') as f:
            canvas = json.load(f)

        self.assertEqual(len(canvas["edges"]), 1)
        # Expected fallback is "{from}__{relation}__{to}" safely formatted with fingerprint
        edge_id = canvas["edges"][0]["id"]
        self.assertTrue(edge_id.startswith("evt-1__references__evt-2_"))
        self.assertNotIn(":", edge_id)

    def test_render_canvas_prioritize_recent(self):
        graph_data = {
            "nodes": [
                {"id": "evt-old", "kind": "event", "file_path": "old.md", "timestamp": "2020-01-01T12:00:00Z"},
                {"id": "evt-missing", "kind": "event", "file_path": "missing.md"},
                {"id": "evt-new", "kind": "event", "file_path": "new.md", "timestamp": "2026-01-01T12:00:00Z"}
            ],
            "edges": []
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        spec_data = {
            "id": "test-recent",
            "type": "chronik",
            "output": "canvases/recent.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {
                "max_nodes": 2,
                "prioritize_recent": True
            }
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/recent.canvas")
        with open(output_path, 'r') as f:
            canvas = json.load(f)

        self.assertEqual(len(canvas["nodes"]), 2)
        # Should pick new.md first, then old.md, ignoring missing.md which drops to the bottom of the list
        rendered_files = [n["file"] for n in canvas["nodes"]]
        self.assertIn("new.md", rendered_files)
        self.assertIn("old.md", rendered_files)
        self.assertNotIn("missing.md", rendered_files)

    def test_render_canvas_prioritize_strongest(self):
        graph_data = {
            "nodes": [
                {"id": "n1", "kind": "event", "file_path": "n1.md"},
                {"id": "n2", "kind": "event", "file_path": "n2.md"}
            ],
            "edges": [
                {"id": "e-weak", "from": "n1", "to": "n2", "relation": "references", "weight": 0.1},
                {"id": "e-strong", "from": "n1", "to": "n2", "relation": "references", "weight": 0.9}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        spec_data = {
            "id": "test-strongest",
            "type": "chronik",
            "output": "canvases/strongest.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {
                "max_edges": 1,
                "prioritize_strongest": True
            }
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/strongest.canvas")
        with open(output_path, 'r') as f:
            canvas = json.load(f)

        self.assertEqual(len(canvas["edges"]), 1)
        self.assertTrue("e-strong" in canvas["edges"][0]["id"])

    def test_render_canvas_invalid_prioritized_relations_raises(self):
        graph_data = {
            "nodes": [
                {"id": "evt-1", "kind": "event", "file_path": "chronik/1.md"}
            ],
            "edges": []
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        spec_data = {
            "id": "test-invalid-priority",
            "type": "chronik",
            "output": "canvases/invalid-priority.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"prioritized_relations": "not-a-list"}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        with self.assertRaises(ValueError) as context:
            render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)
        self.assertIn("Must be a list of strings", str(context.exception))

    def test_render_canvas_local_id_stability(self):
        # Initial graph with 2 nodes relevant to the spec
        graph_data_1 = {
            "nodes": [
                {"id": "n1", "kind": "event", "file_path": "n1.md"},
                {"id": "n2", "kind": "event", "file_path": "n2.md"}
            ],
            "edges": [
                {"id": "e1", "from": "n1", "to": "n2", "relation": "references"}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data_1, f)

        spec_data = {
            "id": "test-stability",
            "type": "chronik",
            "output": "canvases/stability.canvas",
            "source": {"artifact_types": ["event"]}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/stability.canvas")
        with open(output_path, 'r') as f:
            canvas1 = json.load(f)

        node_ids_1 = [n["id"] for n in canvas1["nodes"]]
        # IDs should be strictly sequential based on added nodes (0 and 1)
        self.assertEqual(node_ids_1, ["canvas_node_0", "canvas_node_1"])

        # Verify edge references the correct local IDs
        self.assertEqual(canvas1["edges"][0]["fromNode"], "canvas_node_0")
        self.assertEqual(canvas1["edges"][0]["toNode"], "canvas_node_1")

        # Now add an irrelevant node that comes alphabetically BEFORE the relevant nodes
        # In the old logic, this would shift 'i' and change canvas_node_ids
        graph_data_2 = {
            "nodes": [
                {"id": "a-irrelevant", "kind": "concept", "file_path": "irrelevant.md"},
                {"id": "n1", "kind": "event", "file_path": "n1.md"},
                {"id": "n2", "kind": "event", "file_path": "n2.md"}
            ],
            "edges": [
                {"id": "e1", "from": "n1", "to": "n2", "relation": "references"}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data_2, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        with open(output_path, 'r') as f:
            canvas2 = json.load(f)

        node_ids_2 = [n["id"] for n in canvas2["nodes"]]

        # The node IDs should be identical to canvas1, unharmed by the irrelevant node
        self.assertEqual(node_ids_2, ["canvas_node_0", "canvas_node_1"])

        # Edges should still correctly map to the stable IDs
        self.assertEqual(canvas2["edges"][0]["fromNode"], "canvas_node_0")
        self.assertEqual(canvas2["edges"][0]["toNode"], "canvas_node_1")

    def test_render_canvas_contradictions(self):
        graph_data = {
            "nodes": [
                {"id": "con-1", "kind": "contradiction", "file_path": "observatorium/con-1.md"},
                {"id": "ins-1", "kind": "insight", "file_path": "observatorium/ins-1.md"}
            ],
            "edges": [
                {"id": "edge-1", "from": "con-1", "to": "ins-1", "relation": "contradicts"}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        spec_data = {
            "id": "test-contradictions",
            "type": "observatorium",
            "output": "canvases/contradictions.canvas",
            "source": {"artifact_types": ["contradiction", "insight"]},
            "relations": ["contradicts"]
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/contradictions.canvas")
        with open(output_path, 'r') as f:
            canvas = json.load(f)

        self.assertEqual(len(canvas["nodes"]), 2)
        node_files = [n["file"] for n in canvas["nodes"]]
        self.assertIn("observatorium/con-1.md", node_files)
        self.assertIn("observatorium/ins-1.md", node_files)

        self.assertEqual(len(canvas["edges"]), 1)
        self.assertEqual(canvas["edges"][0]["label"], "contradicts")

    def test_render_canvas_edge_quota_ignores_irrelevant_edges(self):
        # Irrelevant edges sorted before relevant edges must not consume the max_edges quota.
        graph_data = {
            "nodes": [
                {"id": "evt-1", "kind": "event", "file_path": "chronik/evt1.md"},
                {"id": "evt-2", "kind": "event", "file_path": "chronik/evt2.md"}
            ],
            "edges": [
                {"id": "a-irrelevant-edge", "from": "nonexistent", "to": "evt-2", "relation": "references"},
                {"id": "z-relevant-edge", "from": "evt-1", "to": "evt-2", "relation": "references"}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        # Spec limits to 1 edge
        spec_data = {
            "id": "test-edge-quota",
            "type": "chronik",
            "output": "canvases/edge-quota.canvas",
            "source": {"artifact_types": ["event"]},
            "filters": {"max_edges": 1}
        }
        with open(self.spec_file.name, 'w') as f:
            yaml.dump(spec_data, f)

        render_canvas(self.spec_file.name, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/edge-quota.canvas")
        with open(output_path, 'r') as f:
            canvas = json.load(f)

        self.assertEqual(len(canvas["edges"]), 1)
        # Verify the relevant edge was actually picked by checking its semantic connections,
        # meaning the irrelevant edge was explicitly skipped without incrementing the quota counter.
        edge = canvas["edges"][0]
        self.assertEqual(edge["label"], "references")

        # Map local canvas node IDs to their file paths to verify semantic connections
        node_file_by_id = {n["id"]: n["file"] for n in canvas["nodes"]}
        self.assertEqual(node_file_by_id[edge["fromNode"]], "chronik/evt1.md")
        self.assertEqual(node_file_by_id[edge["toNode"]], "chronik/evt2.md")


    def test_render_canvas_investigations_exploratory_analysis(self):
        # This test ensures that the real 'investigations-exploratory-analysis.yaml'
        # spec is renderable and actually pulls the correct subset of node types and
        # relations (event, insight, decision, hypothesis, contradiction, causes, derives_from,
        # informed, contradicts). It explicitly tests the "global explorative slice
        # without implicit tag-based topic scoping" to prevent semantic drift.
        graph_data = {
            "nodes": [
                {"id": "evt-1", "kind": "event", "file_path": "chronik/evt-1.md", "tags": ["investigation"]},
                {"id": "ins-1", "kind": "insight", "file_path": "observatorium/ins-1.md", "tags": ["investigation"]},
                {"id": "dec-1", "kind": "decision", "file_path": "decisions/dec-1.md", "tags": ["investigation"]},
                {"id": "hyp-1", "kind": "hypothesis", "file_path": "knowledge/hyp-1.md", "tags": ["investigation"]},
                {"id": "con-1", "kind": "contradiction", "file_path": "observatorium/con-1.md", "tags": ["investigation"]},
                {"id": "ins-2", "kind": "insight", "file_path": "observatorium/ins-2.md", "tags": ["completely-unrelated-tag"]},
                {"id": "other-1", "kind": "concept", "file_path": "knowledge/con-1.md", "tags": ["other"]}
            ],
            "edges": [
                {"id": "e1", "from": "evt-1", "to": "ins-1", "relation": "informed"},
                {"id": "e2", "from": "ins-1", "to": "dec-1", "relation": "causes"},
                {"id": "e3", "from": "hyp-1", "to": "ins-1", "relation": "derives_from"},
                {"id": "e4", "from": "con-1", "to": "hyp-1", "relation": "contradicts"},
                {"id": "e6", "from": "evt-1", "to": "ins-2", "relation": "informed"},
                {"id": "e5", "from": "other-1", "to": "evt-1", "relation": "references"}
            ]
        }
        with open(self.graph_file.name, 'w') as f:
            json.dump(graph_data, f)

        # We load the actual spec from the repository rather than mocking it,
        # ensuring this test acts as a true regression anchor against the active contract.
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spec_path = os.path.join(repo_root, "config/canvas-specs/investigations-exploratory-analysis.yaml")
        render_canvas(spec_path, self.graph_file.name, self.layout_file.name, output_root=self.temp_dir.name)

        output_path = os.path.join(self.temp_dir.name, "canvases/investigations/exploratory-analysis.canvas")
        with open(output_path, 'r') as f:
            canvas = json.load(f)

        # Verify semantic node inclusion
        self.assertEqual(len(canvas["nodes"]), 6)
        node_files = [n["file"] for n in canvas["nodes"]]
        self.assertIn("chronik/evt-1.md", node_files)
        self.assertIn("observatorium/ins-1.md", node_files)
        self.assertIn("decisions/dec-1.md", node_files)
        self.assertIn("knowledge/hyp-1.md", node_files)
        self.assertIn("observatorium/con-1.md", node_files)
        self.assertIn("observatorium/ins-2.md", node_files)
        self.assertNotIn("knowledge/con-1.md", node_files)

        # Verify semantic edge inclusion (strict exact set matching)
        self.assertEqual(len(canvas["edges"]), 5)

        node_file_by_id = {n["id"]: n["file"] for n in canvas["nodes"]}
        semantic_edges = {
            (node_file_by_id[e["fromNode"]], node_file_by_id[e["toNode"]], e["label"])
            for e in canvas["edges"]
        }
        expected_edges = {
            ("chronik/evt-1.md", "observatorium/ins-1.md", "informed"),
            ("observatorium/ins-1.md", "decisions/dec-1.md", "causes"),
            ("knowledge/hyp-1.md", "observatorium/ins-1.md", "derives_from"),
            ("observatorium/con-1.md", "knowledge/hyp-1.md", "contradicts"),
            ("chronik/evt-1.md", "observatorium/ins-2.md", "informed"),
        }

        self.assertEqual(semantic_edges, expected_edges)
if __name__ == '__main__':
    unittest.main()
