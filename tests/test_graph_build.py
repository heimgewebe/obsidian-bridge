import unittest
import json
import os
from scripts.graph.build_graph import build_graph

import tempfile

class TestGraphBuild(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_file = os.path.join(self.temp_dir.name, "graph.v1.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_build_graph_structure(self):
        graph = build_graph(self.output_file)
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
        build_graph(self.output_file)
        self.assertTrue(os.path.exists(self.output_file))

        with open(self.output_file, 'r') as f:
            data = json.load(f)

        self.assertIn("nodes", data)
        self.assertIn("edges", data)

if __name__ == '__main__':
    unittest.main()
