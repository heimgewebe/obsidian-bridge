import unittest
import os
import json
import tempfile
from scripts.markdown.render_markdown import render_markdown, calculate_deterministic_path

class TestMarkdownRender(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.graph_file = os.path.join(self.temp_dir.name, "graph.json")
        self.output_dir = os.path.join(self.temp_dir.name, "output")

        self.graph_data = {
            "nodes": [
                {
                    "id": "event:evt-1",
                    "kind": "event",
                    "title": "Test Event",
                    "file_path": "chronik/events/2026/01/event--2026-01-01--evt-1.md",
                    "source_repo": "chronik",
                    "timestamp": "2026-01-01T12:00:00Z"
                },
                {
                    "id": "decision:dec-1",
                    "kind": "decision",
                    "title": "Test Decision",
                    "file_path": "decisions/policy/decision--2026-01-02--dec-1.md",
                    "source_repo": "decisions",
                    "timestamp": "2026-01-02T12:00:00Z"
                },
                {
                    "id": "insight:ins-1",
                    "kind": "insight",
                    "title": "Test Insight",
                    # Deliberately missing file_path to test fallback
                    "source_repo": "observatorium",
                    "timestamp": "2026-01-03T12:00:00Z"
                }
            ],
            "edges": [
                {
                    "id": "e1",
                    "from": "event:evt-1",
                    "to": "decision:dec-1",
                    "relation": "informed"
                },
                {
                    "id": "e2",
                    "from": "event:evt-1",
                    "to": "insight:ins-1",
                    "relation": "causes"
                }
            ]
        }

        with open(self.graph_file, "w", encoding="utf-8") as f:
            json.dump(self.graph_data, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_graph_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            render_markdown("nonexistent_graph.json", self.output_dir)

    def test_missing_timestamp_and_path_raises_error(self):
        bad_node = {"id": "test:1", "kind": "test"}
        with self.assertRaises(ValueError):
            calculate_deterministic_path(bad_node)

    def test_missing_timestamp_raises_error_during_render(self):
        # Create a graph with a node missing a timestamp but having a file path
        bad_graph_data = {
            "nodes": [
                {
                    "id": "event:evt-no-time",
                    "kind": "event",
                    "title": "Test Event Missing Time",
                    "file_path": "chronik/events/event--no-time.md",
                    "source_repo": "chronik"
                }
            ],
            "edges": []
        }
        bad_graph_file = os.path.join(self.temp_dir.name, "bad_graph.json")
        with open(bad_graph_file, "w", encoding="utf-8") as f:
            json.dump(bad_graph_data, f)

        with self.assertRaises(ValueError) as context:
            render_markdown(bad_graph_file, self.output_dir)

        self.assertIn("Missing timestamp", str(context.exception))

    def test_markdown_generation(self):
        render_markdown(self.graph_file, self.output_dir)

        # Check files are generated
        evt_path = os.path.join(self.output_dir, "chronik/events/2026/01/event--2026-01-01--evt-1.md")
        dec_path = os.path.join(self.output_dir, "decisions/policy/decision--2026-01-02--dec-1.md")
        ins_path = os.path.join(self.output_dir, "observatorium/insights/insight--2026-01-03--ins-1.md")

        self.assertTrue(os.path.exists(evt_path))
        self.assertTrue(os.path.exists(dec_path))
        self.assertTrue(os.path.exists(ins_path)) # Fallback path generated

        # Check content and links
        with open(evt_path, "r", encoding="utf-8") as f:
            evt_content = f.read()

        # Frontmatter
        self.assertIn("artifact_type: event", evt_content)
        self.assertIn("artifact_id: evt-1", evt_content)

        # Relations sorted
        self.assertIn("## Ausgehende Relationen", evt_content)
        self.assertIn("- **causes** -> [[observatorium/insights/insight--2026-01-03--ins-1]]", evt_content)
        self.assertIn("- **informed** -> [[decisions/policy/decision--2026-01-02--dec-1]]", evt_content)

        with open(dec_path, "r", encoding="utf-8") as f:
            dec_content = f.read()

        self.assertIn("## Eingehende Relationen", dec_content)
        self.assertIn("- <- **informed** [[chronik/events/2026/01/event--2026-01-01--evt-1]]", dec_content)

    def test_canonical_path_precedence(self):
        # Provide a node where file_path intentionally deviates from the schema calculated by timestamp/kind
        divergent_graph_data = {
            "nodes": [
                {
                    "id": "event:evt-divergent",
                    "kind": "event",
                    "title": "Divergent Event",
                    "file_path": "chronik/events/special_folder/my_event.md",
                    "source_repo": "chronik",
                    "timestamp": "2026-01-01T12:00:00Z" # calculated path would be chronik/events/2026/01/event--2026-01-01--evt-divergent.md
                },
                {
                    "id": "decision:dec-normal",
                    "kind": "decision",
                    "title": "Normal Decision",
                    "file_path": "decisions/policy/decision--2026-01-02--dec-normal.md",
                    "source_repo": "decisions",
                    "timestamp": "2026-01-02T12:00:00Z"
                }
            ],
            "edges": [
                {
                    "id": "e1",
                    "from": "event:evt-divergent",
                    "to": "decision:dec-normal",
                    "relation": "informed"
                }
            ]
        }
        divergent_graph_file = os.path.join(self.temp_dir.name, "divergent_graph.json")
        with open(divergent_graph_file, "w", encoding="utf-8") as f:
            json.dump(divergent_graph_data, f)

        # Rendering should print a warning but succeed using canonical path
        import io
        import sys

        captured_output = io.StringIO()
        original_stderr = sys.stderr
        try:
            sys.stderr = captured_output
            render_markdown(divergent_graph_file, self.output_dir)
        finally:
            sys.stderr = original_stderr

        self.assertIn("Warning: Node event:evt-divergent has canonical path", captured_output.getvalue())

        # Check file was generated at canonical path
        canonical_file_path = os.path.join(self.output_dir, "chronik/events/special_folder/my_event.md")
        self.assertTrue(os.path.exists(canonical_file_path))

        # Check links from the normal node point to the canonical path
        normal_file_path = os.path.join(self.output_dir, "decisions/policy/decision--2026-01-02--dec-normal.md")
        self.assertTrue(os.path.exists(normal_file_path))
        with open(normal_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("[[chronik/events/special_folder/my_event]]", content)

if __name__ == "__main__":
    unittest.main()
