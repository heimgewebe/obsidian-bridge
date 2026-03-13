import unittest
import io
import sys
from unittest.mock import patch, mock_open
from scripts.graph.extract_relations import extract_relations

class TestExtractRelations(unittest.TestCase):
    def test_extract_relations_resolution(self):
        file_contents = {
            "vault-gewebe/obsidian-bridge/folder1/source.md": """---
artifact_type: test
artifact_id: src
---
- **causes** -> [[exact_target.md]]
- **informed** -> [[folder2/exact_target.md]]
- **references** -> [[ambiguous_target.md]]
""",
            "vault-gewebe/obsidian-bridge/folder1/exact_target.md": """---
artifact_type: test
artifact_id: t-1
---""",
            "vault-gewebe/obsidian-bridge/folder2/exact_target.md": """---
artifact_type: test
artifact_id: t-2
---""",
            "vault-gewebe/obsidian-bridge/folder1/ambiguous_target.md": """---
artifact_type: test
artifact_id: t-3
---""",
            "vault-gewebe/obsidian-bridge/folder2/ambiguous_target.md": """---
artifact_type: test
artifact_id: t-4
---""",
        }

        def mock_open_side_effect(path, *args, **kwargs):
            return mock_open(read_data=file_contents.get(path, ""))()

        files = list(file_contents.keys())

        # Redirect stderr to capture warnings
        stderr_backup = sys.stderr
        stderr_trap = io.StringIO()
        sys.stderr = stderr_trap

        try:
            with patch('builtins.open', side_effect=mock_open_side_effect):
                relations = extract_relations(files)
        finally:
            sys.stderr = stderr_backup

        warnings = stderr_trap.getvalue()

        # Check edges
        edges = {(r["from"], r["to"], r["relation"]) for r in relations}

        # Resolution rules under test:
        # - Links that match multiple files by basename (e.g. [[exact_target.md]])
        #   are treated as ambiguous and do not produce an edge.
        # - Links with an explicit folder-qualified path (e.g. [[folder2/exact_target.md]])
        #   resolve uniquely even if the basename exists in multiple folders.
        # - Ambiguous links emit a warning and no relation edge is created.

        self.assertIn(("test:src", "test:t-2", "informed"), edges)
        self.assertNotIn(("test:src", "test:t-1", "causes"), edges)

        # Check warnings
        self.assertIn("Ambiguous link '[[exact_target.md]]'", warnings)
        self.assertIn("Ambiguous link '[[ambiguous_target.md]]'", warnings)

    def test_extract_relations_exact_priority(self):
        file_contents = {
            "vault-gewebe/obsidian-bridge/folder1/source.md": """---
artifact_type: test
artifact_id: src
---
- **causes** -> [[folder1/target.md]]
""",
            "vault-gewebe/obsidian-bridge/folder1/target.md": """---
artifact_type: test
artifact_id: t-1
---""",
            "vault-gewebe/obsidian-bridge/folder2/target.md": """---
artifact_type: test
artifact_id: t-2
---"""
        }

        def mock_open_side_effect(path, *args, **kwargs):
            return mock_open(read_data=file_contents.get(path, ""))()

        files = list(file_contents.keys())

        with patch('builtins.open', side_effect=mock_open_side_effect):
            relations = extract_relations(files)

        edges = {(r["from"], r["to"], r["relation"]) for r in relations}
        self.assertIn(("test:src", "test:t-1", "causes"), edges)

if __name__ == '__main__':
    unittest.main()
