import unittest
from unittest.mock import MagicMock
import sys

# Mock yaml if it's not available to allow testing _parse_weight which doesn't depend on it
yaml_mocked = False
if 'yaml' not in sys.modules:
    try:
        import yaml
    except ImportError:
        sys.modules['yaml'] = MagicMock()
        yaml_mocked = True

from scripts.canvas.render_canvas import _parse_weight

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

if __name__ == '__main__':
    unittest.main()
