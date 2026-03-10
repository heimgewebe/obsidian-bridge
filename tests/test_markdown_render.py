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

if __name__ == "__main__":
    unittest.main()
