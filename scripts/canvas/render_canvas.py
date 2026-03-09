import json
import os
import yaml
from typing import Dict, Any

def render_canvas(spec_path: str, graph_path: str, layout_path: str) -> None:
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
            layout = json.load(f)

    # Construct neutral internal canvas representation
    canvas_model = {
        "nodes": [],
        "edges": []
    }

    # Apply filters (Guards)
    max_nodes = spec.get("filters", {}).get("max_nodes", 100)
    valid_relations = spec.get("relations", [])
    valid_types = spec.get("source", {}).get("artifact_types", [])

    # Process nodes up to max_nodes
    added_nodes = 0
    node_id_map = {}

    for i, node in enumerate(graph.get("nodes", [])):
        if added_nodes >= max_nodes:
            break

        node_id = node.get("id")

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
    for i, edge in enumerate(graph.get("edges", [])):
        from_id = edge.get("from")
        to_id = edge.get("to")
        relation = edge.get("relation")

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

    # Write output
    output_file = spec.get("output", f"canvases/{spec.get('id', 'default')}.canvas")
    output_path = os.path.join("vault-gewebe/obsidian-bridge", output_file)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(canvas_model, f, indent=2)

if __name__ == '__main__':
    # Simple test render
    render_canvas(
        "config/canvas-specs/system.yaml",
        "vault-gewebe/obsidian-bridge/meta/graph/graph.v1.json",
        "vault-gewebe/obsidian-bridge/meta/graph/layout.v1.json"
    )
