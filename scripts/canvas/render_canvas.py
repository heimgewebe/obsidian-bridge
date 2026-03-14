import json
import os
import yaml
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta

def _parse_timestamp_utc(ts_str: Optional[str]) -> Optional[datetime]:
    if not ts_str:
        return None
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts
    except ValueError:
        return None

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
    date_window_days_raw = spec.get("filters", {}).get("date_window_days")
    valid_relations = spec.get("relations", [])
    valid_types = spec.get("source", {}).get("artifact_types", [])

    cutoff_date = None
    if date_window_days_raw is not None:
        try:
            date_window_days = int(date_window_days_raw)
            if date_window_days < 0:
                raise ValueError()
        except ValueError:
            raise ValueError(f"Invalid date_window_days: {date_window_days_raw}. Must be a non-negative integer.")

        # Der Zeitfilter wird am maximalen Graph-Timestamp verankert, um deterministische Builds zu erhalten.
        # Die Systemzeit wird bewusst nicht verwendet, um Churn zu vermeiden.
        max_ts = None
        for n in graph.get("nodes", []):
            if valid_types and n.get("kind") not in valid_types:
                continue
            ts = _parse_timestamp_utc(n.get("timestamp"))
            if ts:
                if max_ts is None or ts > max_ts:
                    max_ts = ts

        if max_ts is None:
            raise ValueError(f"date_window_days is set to {date_window_days}, but no valid timestamps were found in the relevant graph nodes.")

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
            node_ts = _parse_timestamp_utc(node.get("timestamp"))
            if not node_ts or node_ts < cutoff_date:
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
