import unittest
from scripts.canvas.render_canvas import _parse_weight, _get_edge_id, _generate_canvas_edge_id

class TestCanvasUtils(unittest.TestCase):
    """Unit tests for utility functions in render_canvas.py"""

    def test_parse_weight_missing_key(self):
        self.assertEqual(_parse_weight({}), 0.0)

    def test_parse_weight_none(self):
        self.assertEqual(_parse_weight({"weight": None}), 0.0)

    def test_parse_weight_int(self):
        self.assertEqual(_parse_weight({"weight": 5}), 5.0)

    def test_parse_weight_float(self):
        self.assertEqual(_parse_weight({"weight": 0.5}), 0.5)

    def test_parse_weight_valid_string(self):
        self.assertEqual(_parse_weight({"weight": "0.75"}), 0.75)

    def test_parse_weight_invalid_string(self):
        self.assertEqual(_parse_weight({"weight": "not-a-number"}), 0.0)

    def test_parse_weight_list(self):
        self.assertEqual(_parse_weight({"weight": [1, 2, 3]}), 0.0)

    def test_parse_weight_dict(self):
        self.assertEqual(_parse_weight({"weight": {"value": 0.5}}), 0.0)

    def test_parse_weight_bool_true(self):
        # float(True) is 1.0 in Python
        self.assertEqual(_parse_weight({"weight": True}), 1.0)

    def test_parse_weight_bool_false(self):
        # float(False) is 0.0 in Python
        self.assertEqual(_parse_weight({"weight": False}), 0.0)

    def test_get_edge_id_with_id(self):
        self.assertEqual(_get_edge_id({"id": "my_custom_edge", "from": "A", "to": "B"}), "my_custom_edge")

    def test_get_edge_id_fallback(self):
        self.assertEqual(_get_edge_id({"from": "nodeA", "relation": "connects", "to": "nodeB"}), "nodeA__connects__nodeB")
        # Missing parts
        self.assertEqual(_get_edge_id({}), "unknown__unknown__unknown")

    def test_generate_canvas_edge_id_sanitization(self):
        # Tests sanitizing ':' and '->'
        orig = "node:A->node:B"
        res = _generate_canvas_edge_id(orig)
        self.assertTrue(res.startswith("node_A_node_B_"))
        self.assertNotIn(":", res)
        self.assertNotIn("->", res)

    def test_generate_canvas_edge_id_consistency(self):
        base1 = "some_random_edge_id_123"
        base2 = "another_different_id_456"

        # Deterministic at same input
        res1_a = _generate_canvas_edge_id(base1)
        res1_b = _generate_canvas_edge_id(base1)
        self.assertEqual(res1_a, res1_b)

        # Distinct outputs for different inputs
        res2 = _generate_canvas_edge_id(base2)
        self.assertNotEqual(res1_a, res2)

        # Hash suffix length is exactly 8 characters
        self.assertEqual(len(res1_a.split("_")[-1]), 8)
        self.assertEqual(len(res2.split("_")[-1]), 8)

if __name__ == '__main__':
    unittest.main()
