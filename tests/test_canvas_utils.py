import unittest
from scripts.canvas.render_canvas import (
    _get_edge_id,
    _generate_canvas_edge_id
)

class TestCanvasEdgeIDUtils(unittest.TestCase):

    def test_get_edge_id_with_id(self):
        edge = {"id": "edge-123", "from": "A", "to": "B", "relation": "rel"}
        self.assertEqual(_get_edge_id(edge), "edge-123")

    def test_get_edge_id_fallback(self):
        edge = {"from": "A", "to": "B", "relation": "rel"}
        self.assertEqual(_get_edge_id(edge), "A__rel__B")

    def test_get_edge_id_missing_keys(self):
        edge = {}
        self.assertEqual(_get_edge_id(edge), "unknown__unknown__unknown")

    def test_generate_canvas_edge_id_determinism(self):
        base_id = "A:B->C"
        canvas_id1 = _generate_canvas_edge_id(base_id)
        canvas_id2 = _generate_canvas_edge_id(base_id)
        self.assertEqual(canvas_id1, canvas_id2)

    def test_generate_canvas_edge_id_normalization(self):
        # Colon and arrow should be normalized to underscores
        base_id = "A:B->C"
        canvas_id = _generate_canvas_edge_id(base_id)
        self.assertTrue(canvas_id.startswith("A_B_C_"))

    def test_generate_canvas_edge_id_format(self):
        base_id = "test-edge"
        canvas_id = _generate_canvas_edge_id(base_id)
        # Should be f"{safe_prefix}_{fingerprint}" where fingerprint is 8 chars hex
        parts = canvas_id.split("_")
        self.assertGreaterEqual(len(parts), 2)
        fingerprint = parts[-1]
        self.assertEqual(len(fingerprint), 8)

    def test_generate_canvas_edge_id_uniqueness(self):
        # Different base IDs should yield different canvas IDs
        id1 = _generate_canvas_edge_id("edge-1")
        id2 = _generate_canvas_edge_id("edge-2")
        self.assertNotEqual(id1, id2)

if __name__ == '__main__':
    unittest.main()
