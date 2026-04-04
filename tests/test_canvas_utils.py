import unittest
from scripts.canvas.render_canvas import _get_edge_id, _generate_canvas_edge_id

class TestCanvasUtils(unittest.TestCase):
    def test_get_edge_id_explicit(self):
        edge = {"id": "explicit_id", "from": "A", "to": "B"}
        self.assertEqual(_get_edge_id(edge), "explicit_id")

    def test_get_edge_id_fallback(self):
        edge = {"from": "nodeA", "to": "nodeB", "relation": "rel"}
        self.assertEqual(_get_edge_id(edge), "nodeA__rel__nodeB")

        edge_no_rel = {"from": "nodeA", "to": "nodeB"}
        self.assertEqual(_get_edge_id(edge_no_rel), "nodeA__unknown__nodeB")

    def test_generate_canvas_edge_id_deterministic(self):
        base_id = "nodeA->nodeB:relation"
        res1 = _generate_canvas_edge_id(base_id)
        res2 = _generate_canvas_edge_id(base_id)
        self.assertEqual(res1, res2)

    def test_generate_canvas_edge_id_normalization(self):
        base_id1 = "A:B->C"
        res1 = _generate_canvas_edge_id(base_id1)
        self.assertTrue(res1.startswith("A_B_C"))

    def test_generate_canvas_edge_id_different_inputs(self):
        res1 = _generate_canvas_edge_id("nodeA->nodeB")
        res2 = _generate_canvas_edge_id("nodeA->nodeC")
        self.assertNotEqual(res1, res2)

if __name__ == '__main__':
    unittest.main()
