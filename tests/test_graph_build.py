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

    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open, read_data="""---
artifact_type: test
artifact_id: t-1
title: Test Node
generated_at: 2026-03-08T12:00:00Z
---
This is a test node with a link to [[target.md]].
""")
    def test_build_graph_structure(self, mock_file, mock_walk):
        mock_walk.return_value = [
            ("vault-gewebe/obsidian-bridge/folder", [], ["test.md", "target.md"])
        ]

        # Override the vault dir to limit scope during testing
        with patch('scripts.graph.build_graph.os.path.relpath', side_effect=lambda path, start: path.replace("vault-gewebe/obsidian-bridge/", "")):
            with patch('scripts.graph.build_graph.os.walk', return_value=[("vault-gewebe/obsidian-bridge/folder", [], ["test.md"])]):
                graph = build_graph(self.output_file)

        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)
        self.assertIsInstance(graph["nodes"], list)
        self.assertIsInstance(graph["edges"], list)

        if len(graph["nodes"]) > 0:
            # Test basic schema fields from the blueprint
            node = graph["nodes"][0]
            self.assertEqual(node["id"], "test:t-1")
            self.assertEqual(node["kind"], "test")
            self.assertIn("file_path", node)

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
