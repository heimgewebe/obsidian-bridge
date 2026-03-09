import unittest
import json
import os
from scripts.graph.build_graph import build_graph

class TestGraphBuild(unittest.TestCase):
    def test_build_graph_structure(self):
        graph = build_graph()
        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)
        self.assertIsInstance(graph["nodes"], list)
        self.assertIsInstance(graph["edges"], list)

        # Test basic schema fields from the blueprint
        node = graph["nodes"][0]
        self.assertIn("id", node)
        self.assertIn("kind", node)
        self.assertIn("file_path", node)

    def test_graph_artifact_creation(self):
        output_file = "vault-gewebe/obsidian-bridge/meta/graph/graph.v1.json"
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, 'r') as f:
            data = json.load(f)

        self.assertIn("nodes", data)
        self.assertIn("edges", data)

if __name__ == '__main__':
    unittest.main()
