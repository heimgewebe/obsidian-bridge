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
    - Deleted nodes are actively cleaned up to prevent layout drift
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

    # Apply stable positioning (grid layout)
    # Sort nodes by ID to ensure determinism across runs
    nodes = sorted(graph.get("nodes", []), key=lambda x: x.get("id", ""))

    # Prune stale nodes from layout cache to prevent layout drift
    current_node_ids = {n.get("id") for n in nodes if n.get("id")}
    stale_node_ids = [nid for nid in layout["nodes"].keys() if nid not in current_node_ids]
    for nid in stale_node_ids:
        del layout["nodes"][nid]

    # We use a grid to assign new positions. We need to find the next available spot.
    # For simplicity of the grid, let's keep track of an index for new nodes.
    grid_cols = 5
    cell_width = 300
    cell_height = 200

    # Count how many existing nodes we have to offset the grid correctly
    # (A simple heuristic to avoid overlapping for newly added nodes)
    new_node_index = len(layout.get("nodes", {}))

    for node in nodes:
        node_id = node.get("id")
        if node_id and node_id not in layout["nodes"]:
            # Assign deterministic coordinates based on grid index
            x = (new_node_index % grid_cols) * cell_width
            y = (new_node_index // grid_cols) * cell_height

            layout["nodes"][node_id] = {
                "x": x,
                "y": y,
                "width": 250,
                "height": 150
            }
            new_node_index += 1

    # Save the stabilized layout back to cache
    output_dir = os.path.dirname(layout_cache_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Use encoding='utf-8' and newline='\n' to ensure deterministic file output on all platforms
    with open(layout_cache_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(layout, f, indent=2)

    return layout

if __name__ == '__main__':
    stabilize_layout(
        "vault-gewebe/obsidian-bridge/meta/graph/graph.v1.json",
        "vault-gewebe/obsidian-bridge/meta/graph/layout.v1.json"
    )
