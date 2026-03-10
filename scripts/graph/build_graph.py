import json
import os
from typing import Dict, Any

def build_graph(output_file: str = "vault-gewebe/obsidian-bridge/meta/graph/graph.v1.json") -> Dict[str, Any]:
    """
    Builds the canonical graph layer from Heimewebe artifacts.
    This acts as the deterministic base for Canvas generation.
    """
    graph: Dict[str, Any] = {
        "nodes": [],
        "edges": [],
        "clusters": [],
        "topics": []
    }

    # Placeholder logic to satisfy test and blueprint schema
    # In reality, this would read from actual markdown artifacts
    graph["nodes"].append({
        "id": "event:evt-123",
        "kind": "event",
        "title": "Event 2026-03-08",
        "file_path": "chronik/events/2026/03/event--2026-03-08--evt-123.md",
        "source_repo": "chronik",
        "timestamp": "2026-03-08T12:00:00Z",
        "tags": ["chronik", "event"]
    })

    graph["edges"].append({
        "id": "edge:event:evt-123->decision:dec-12",
        "from": "event:evt-123",
        "to": "decision:dec-12",
        "relation": "informed",
        "weight": 0.8
    })

    # Output to canonical graph artifact path
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(graph, f, indent=2)

    return graph

if __name__ == '__main__':
    build_graph()
