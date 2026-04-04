import unittest
import sys
from unittest.mock import MagicMock
from datetime import datetime, timezone

# Mock yaml to avoid ModuleNotFoundError in restricted environments
sys.modules['yaml'] = MagicMock()

from scripts.canvas.render_canvas import (
    _get_edge_id,
    _parse_timestamp_utc,
    _parse_weight,
    _generate_canvas_edge_id
)

class TestCanvasUtils(unittest.TestCase):

    def test_get_edge_id_with_id(self):
        edge = {"id": "edge-123", "from": "A", "to": "B", "relation": "rel"}
        self.assertEqual(_get_edge_id(edge), "edge-123")

    def test_get_edge_id_fallback(self):
        edge = {"from": "A", "to": "B", "relation": "rel"}
        self.assertEqual(_get_edge_id(edge), "A__rel__B")

    def test_get_edge_id_missing_keys(self):
        edge = {}
        self.assertEqual(_get_edge_id(edge), "unknown__unknown__unknown")

    def test_parse_timestamp_utc_valid_z(self):
        ts_str = "2026-03-08T12:00:00Z"
        ts = _parse_timestamp_utc(ts_str)
        self.assertEqual(ts, datetime(2026, 3, 8, 12, 0, 0, tzinfo=timezone.utc))

    def test_parse_timestamp_utc_valid_offset(self):
        ts_str = "2026-03-08T12:00:00+01:00"
        ts = _parse_timestamp_utc(ts_str)
        # 12:00+01:00 is 11:00 UTC
        self.assertEqual(ts.astimezone(timezone.utc), datetime(2026, 3, 8, 11, 0, 0, tzinfo=timezone.utc))

    def test_parse_timestamp_utc_naive(self):
        ts_str = "2026-03-08T12:00:00"
        ts = _parse_timestamp_utc(ts_str)
        self.assertEqual(ts, datetime(2026, 3, 8, 12, 0, 0, tzinfo=timezone.utc))

    def test_parse_timestamp_utc_none(self):
        self.assertIsNone(_parse_timestamp_utc(None))
        self.assertIsNone(_parse_timestamp_utc(""))

    def test_parse_timestamp_utc_invalid(self):
        self.assertIsNone(_parse_timestamp_utc("invalid-date"))

    def test_parse_weight_valid(self):
        self.assertEqual(_parse_weight({"weight": 0.5}), 0.5)
        self.assertEqual(_parse_weight({"weight": "0.8"}), 0.8)

    def test_parse_weight_invalid(self):
        self.assertEqual(_parse_weight({"weight": "abc"}), 0.0)
        self.assertEqual(_parse_weight({"weight": None}), 0.0)
        self.assertEqual(_parse_weight({}), 0.0)

    def test_generate_canvas_edge_id(self):
        base_id = "A:B->C"
        canvas_id = _generate_canvas_edge_id(base_id)
        # Check prefix normalization
        self.assertTrue(canvas_id.startswith("A_B_C_"))
        # Check fingerprint (8 chars hex)
        fingerprint = canvas_id.split("_")[-1]
        self.assertEqual(len(fingerprint), 8)
        # Check determinism
        self.assertEqual(canvas_id, _generate_canvas_edge_id(base_id))

if __name__ == '__main__':
    unittest.main()
