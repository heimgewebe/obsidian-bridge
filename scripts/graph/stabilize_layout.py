import json
import os
from typing import Dict, Any

def stabilize_layout(graph_path: str, layout_cache_path: str) -> Dict[str, Any]:
    """
    Ensures layout determinism by applying rules based on Canvas class.
    Pipeline: graph snapshot -> layout cache -> canvas render

    Rules:
    - Existing nodes keep position
    - New nodes placed deterministically
    - Deleted nodes are currently NOT actively cleaned up (WIP)
    """
    layout: Dict[str, Any] = {"nodes": {}}

    # If layout cache exists, load it
    if os.path.exists(layout_cache_path):
        with open(layout_cache_path, 'r') as f:
            layout = json.load(f)
            layout.setdefault("nodes", {})

    # Load the graph
    graph: Dict[str, Any] = {"nodes": [], "edges": []}
    if os.path.exists(graph_path):
        with open(graph_path, 'r') as f:
            graph = json.load(f)

    # Apply stable positioning (placeholder logic)
    for i, node in enumerate(graph.get("nodes", [])):
        node_id = node.get("id")
        if node_id and node_id not in layout["nodes"]:
            # Assign deterministic coordinates based on index or node kind
            layout["nodes"][node_id] = {
                "x": i * 100,
                "y": 0,
                "width": 250,
                "height": 150
            }

    # Save the stabilized layout back to cache
    output_dir = os.path.dirname(layout_cache_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(layout_cache_path, 'w') as f:
        json.dump(layout, f, indent=2)

    return layout

if __name__ == '__main__':
    stabilize_layout(
        "vault-gewebe/obsidian-bridge/meta/graph/graph.v1.json",
        "vault-gewebe/obsidian-bridge/meta/graph/layout.v1.json"
    )
