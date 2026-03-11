import unittest
import json
import os
from scripts.graph.build_graph import build_graph

import tempfile

from unittest.mock import patch, mock_open
from scripts.graph.extract_relations import _parse_frontmatter

class TestGraphBuild(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_file = os.path.join(self.temp_dir.name, "graph.v1.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_build_graph_structure_and_relations(self):
        # We need a robust mock side_effect to return different contents for two files
        # so we can test relations properly without reading the real file system.
        file_contents = {
            "vault-gewebe/obsidian-bridge/folder/test.md": """---
artifact_type: test
artifact_id: t-1
generated_at: 2026-03-08T12:00:00Z
---
# Real Extracted Title

This is a test node with an explicit relation.
- **causes** -> [[target.md]]
- <- **informed** [[target2.md]]
#hashtag_one #hashtag_two
""",
            "vault-gewebe/obsidian-bridge/folder/target.md": """---
artifact_type: target
artifact_id: tg-1
generated_at: 2026-03-08T13:00:00Z
---
# Target Node
This node receives the cause.
""",
            "vault-gewebe/obsidian-bridge/folder/target2.md": """---
artifact_type: target
artifact_id: tg-2
generated_at: 2026-03-08T14:00:00Z
---
# Target Node 2
This node informs the test node.
"""
        }

        def mock_open_side_effect(path, *args, **kwargs):
            return mock_open(read_data=file_contents.get(path, ""))()

        with patch('os.walk') as mock_walk, \
             patch('builtins.open', side_effect=mock_open_side_effect), \
             patch('scripts.graph.build_graph.os.path.relpath', side_effect=lambda path, start: path.replace("vault-gewebe/obsidian-bridge/", "")):

            mock_walk.return_value = [
                ("vault-gewebe/obsidian-bridge/folder", [], ["test.md", "target.md", "target2.md"])
            ]

            graph = build_graph(self.output_file)

        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)

        self.assertEqual(len(graph["nodes"]), 3)

        # Test title and tag parsing from body
        test_node = next(n for n in graph["nodes"] if n["id"] == "test:t-1")
        self.assertEqual(test_node["title"], "Real Extracted Title")
        self.assertIn("hashtag_one", test_node["tags"])
        self.assertIn("hashtag_two", test_node["tags"])

        # Test explicit relations extraction
        edges = graph["edges"]
        self.assertTrue(any(e["from"] == "test:t-1" and e["to"] == "target:tg-1" and e["relation"] == "causes" for e in edges))
        self.assertTrue(any(e["from"] == "target:tg-2" and e["to"] == "test:t-1" and e["relation"] == "informed" for e in edges))

    @patch('scripts.graph.build_graph.os.walk')
    def test_graph_artifact_creation(self, mock_walk):
        mock_walk.return_value = [] # Empty directory simulation
        build_graph(self.output_file)
        self.assertTrue(os.path.exists(self.output_file))

        with open(self.output_file, 'r') as f:
            data = json.load(f)

        self.assertIn("nodes", data)
        self.assertIn("edges", data)

if __name__ == '__main__':
    unittest.main()
