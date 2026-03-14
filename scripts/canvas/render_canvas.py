import json
import os
import yaml
from typing import Dict, Any

def render_canvas(spec_path: str, graph_path: str, layout_path: str, output_root: str = "vault-gewebe/obsidian-bridge") -> None:
    """
    Generates a deterministic .canvas file from a YAML declarative spec.
    Validates against size limits (Guards against graph-spaghetti).
    """
    # Load spec
    with open(spec_path, 'r') as f:
        spec = yaml.safe_load(f)

    # Load graph and layout
    graph = {"nodes": [], "edges": []}
    if os.path.exists(graph_path):
        with open(graph_path, 'r') as f:
            graph = json.load(f)

    layout = {"nodes": {}}
    if os.path.exists(layout_path):
        with open(layout_path, 'r') as f:
            raw_layout = json.load(f)

            if isinstance(raw_layout, dict) and "canvases" in raw_layout:
                canvas_id = spec.get("id", "default")
                layout = raw_layout.get("canvases", {}).get(canvas_id, {"nodes": {}})
            elif isinstance(raw_layout, dict) and "nodes" in raw_layout:
                layout = {"nodes": raw_layout["nodes"]}
            else:
                layout = {"nodes": {}}

    # Construct neutral internal canvas representation
    canvas_model = {
        "nodes": [],
        "edges": []
    }

    # Apply filters (Guards)
    max_nodes = spec.get("filters", {}).get("max_nodes", 100)
    max_edges = spec.get("filters", {}).get("max_edges", 200)
    date_window_days = spec.get("filters", {}).get("date_window_days")
    valid_relations = spec.get("relations", [])
    valid_types = spec.get("source", {}).get("artifact_types", [])

    from datetime import datetime, timezone, timedelta

    cutoff_date = None
    if date_window_days is not None:
        # We need a reference date. To be deterministic, we should perhaps use the max date in the graph.
        # However, a common approach is current time.
        # But wait, the system memory says:
        # "Markdown file generation must be idempotent to prevent Git churn; dynamic fields like `generated_at` should use the canonical graph node's timestamp rather than the current system time."
        # If we use the system time for date_window_days, the canvas will change every day!
        # Let's find the maximum timestamp in the graph's relevant nodes to be our "now",
        # or just use the current time but be aware of churn. Let's use max timestamp in graph.
        max_ts = None
        for n in graph.get("nodes", []):
            ts_str = n.get("timestamp")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if max_ts is None or ts > max_ts:
                        max_ts = ts
                except ValueError:
                    pass
        if max_ts:
            cutoff_date = max_ts - timedelta(days=date_window_days)

    # Process nodes up to max_nodes
    added_nodes = 0
    node_id_map = {}

    for i, node in enumerate(graph.get("nodes", [])):
        node_id = node.get("id")
        if not node_id:
            # Skip nodes without a valid ID to avoid None mapping collisions
            continue

        if valid_types and node.get("kind") not in valid_types:
            continue

        if cutoff_date is not None:
            ts_str = node.get("timestamp")
            if ts_str:
                try:
                    node_ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if node_ts < cutoff_date:
                        continue
                except ValueError:
                    continue
            else:
                # If no timestamp and we have a window, skip
                continue

        if added_nodes >= max_nodes:
            break

        # Simple text representation of node type for canvas internal ID
        canvas_node_id = f"canvas_node_{i}"
        node_id_map[node_id] = canvas_node_id

        node_layout = layout.get("nodes", {}).get(node_id, {"x": i*100, "y": 0, "width": 250, "height": 150})

        # Determine canvas node type (file or text)
        canvas_node = {
            "id": canvas_node_id,
            "x": node_layout.get("x", 0),
            "y": node_layout.get("y", 0),
            "width": node_layout.get("width", 250),
            "height": node_layout.get("height", 150),
        }

        if node.get("file_path"):
            canvas_node["type"] = "file"
            canvas_node["file"] = node.get("file_path")
        else:
            canvas_node["type"] = "text"
            canvas_node["text"] = node.get("title", "Unknown Node")

        canvas_model["nodes"].append(canvas_node)
        added_nodes += 1

    # Process edges
    added_edges = 0
    for i, edge in enumerate(graph.get("edges", [])):
        from_id = edge.get("from")
        to_id = edge.get("to")
        relation = edge.get("relation")

        if added_edges >= max_edges:
            break

        if valid_relations and relation not in valid_relations:
            continue

        if from_id in node_id_map and to_id in node_id_map:
            canvas_model["edges"].append({
                "id": f"canvas_edge_{i}",
                "fromNode": node_id_map[from_id],
                "fromSide": "right",
                "toNode": node_id_map[to_id],
                "toSide": "left",
                "label": relation
            })
            added_edges += 1

    # Write output
    output_file = spec.get("output", f"canvases/{spec.get('id', 'default')}.canvas")
    output_path = os.path.join(output_root, output_file)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Use encoding='utf-8' and newline='\n' to ensure deterministic file output on all platforms
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(canvas_model, f, indent=2)

if __name__ == '__main__':
    # Simple test render
    render_canvas(
        "config/canvas-specs/system.yaml",
        "vault-gewebe/obsidian-bridge/meta/graph/graph.v1.json",
        "vault-gewebe/obsidian-bridge/meta/graph/layout.v1.json"
    )
