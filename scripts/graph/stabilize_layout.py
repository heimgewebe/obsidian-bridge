import json
import os
import yaml
import glob
import math
from typing import Dict, Any, List

def _get_canvas_specs(specs_dir: str) -> List[Dict[str, Any]]:
    specs = []
    if os.path.exists(specs_dir):
        for spec_path in sorted(glob.glob(os.path.join(specs_dir, '*.yaml'))):
            with open(spec_path, 'r', encoding='utf-8') as f:
                specs.append(yaml.safe_load(f))
    return specs

def stabilize_layout(graph_path: str, layout_cache_path: str, specs_dir: str = "config/canvas-specs") -> Dict[str, Any]:
    layout: Dict[str, Any] = {"canvases": {}}

    if os.path.exists(layout_cache_path):
        with open(layout_cache_path, 'r', encoding='utf-8') as f:
            cached_layout = json.load(f)
            # Migration support if old layout was flat
            if "nodes" in cached_layout and "canvases" not in cached_layout:
                layout["canvases"]["default"] = {"nodes": cached_layout["nodes"]}
            else:
                layout = cached_layout
            layout.setdefault("canvases", {})

    graph: Dict[str, Any] = {"nodes": [], "edges": []}
    if os.path.exists(graph_path):
        with open(graph_path, 'r', encoding='utf-8') as f:
            graph = json.load(f)

    nodes = sorted(graph.get("nodes", []), key=lambda x: x.get("id", ""))
    edges = sorted(graph.get("edges", []), key=lambda x: x.get("id", ""))

    current_node_ids = {n.get("id") for n in nodes if n.get("id")}

    specs = _get_canvas_specs(specs_dir)
    if not specs:
        # Fallback to a single generic layout if no specs
        specs = [{"id": "default", "layout": "grid"}]

    for spec in specs:
        canvas_id = spec.get("id", "default")
        layout_type = spec.get("layout", "grid")

        canvas_layout = layout["canvases"].setdefault(canvas_id, {"nodes": {}})

        # Prune stale nodes
        stale_node_ids = [nid for nid in canvas_layout["nodes"].keys() if nid not in current_node_ids]
        for nid in stale_node_ids:
            del canvas_layout["nodes"][nid]

        # Filter nodes based on spec to only layout relevant nodes
        valid_types = spec.get("source", {}).get("artifact_types", [])

        relevant_nodes = []
        for n in nodes:
            if not n.get("id"): continue
            if valid_types and n.get("kind") not in valid_types:
                continue
            relevant_nodes.append(n)

        # Add new nodes deterministically depending on layout_type
        # For simplicity, we implement a naive version of the requested layout types

        new_nodes = [n for n in relevant_nodes if n["id"] not in canvas_layout["nodes"]]

        if layout_type == "timeline":
            # links -> rechts = Zeit, oben / unten = Typgruppen
            # Sort by timestamp
            new_nodes.sort(key=lambda x: x.get("timestamp", ""))

            # Group by kind
            kind_offsets = {}
            for kind in set(n.get("kind", "unknown") for n in relevant_nodes):
                kind_offsets[kind] = len(kind_offsets) * 300

            x_offset = len(canvas_layout["nodes"]) * 350
            for n in new_nodes:
                nid = n["id"]
                kind = n.get("kind", "unknown")
                canvas_layout["nodes"][nid] = {
                    "x": x_offset,
                    "y": kind_offsets[kind],
                    "width": 250,
                    "height": 150
                }
                x_offset += 350

        elif layout_type == "radial":
            # Zentrum = Entscheidung, innen = Inputs, außen = Outcomes
            # simplistic: just place them in a circle around a center
            center_x, center_y = 0, 0
            radius = 400 + (len(canvas_layout["nodes"]) * 10)

            angle_step = (2 * math.pi) / max(1, len(new_nodes))
            for i, n in enumerate(new_nodes):
                nid = n["id"]
                angle = i * angle_step
                canvas_layout["nodes"][nid] = {
                    "x": int(center_x + radius * math.cos(angle)),
                    "y": int(center_y + radius * math.sin(angle)),
                    "width": 250,
                    "height": 150
                }

        elif layout_type == "cluster":
            # Cluster je Thema
            # Just grid them by tag/topic
            tag_offsets = {}

            x_offset = len(canvas_layout["nodes"]) * 350
            for n in new_nodes:
                nid = n["id"]
                tags = n.get("tags", ["untagged"])
                primary_tag = tags[0] if tags else "untagged"

                if primary_tag not in tag_offsets:
                    tag_offsets[primary_tag] = {"x": x_offset, "y": 0}
                    x_offset += 400

                canvas_layout["nodes"][nid] = {
                    "x": tag_offsets[primary_tag]["x"],
                    "y": tag_offsets[primary_tag]["y"],
                    "width": 250,
                    "height": 150
                }
                tag_offsets[primary_tag]["y"] += 200

        elif layout_type == "organsystem":
            # Feste Positionen für: chronik, semantAH, hausKI, heimlern, heimgeist, leitstand, wgx, metarepo
            fixed_positions = {
                "chronik": (0, 0),
                "semantAH": (400, 0),
                "hausKI": (800, 0),
                "heimlern": (0, 400),
                "heimgeist": (400, 400),
                "leitstand": (800, 400),
                "wgx": (0, 800),
                "metarepo": (400, 800)
            }
            grid_cols = 4
            cell_width, cell_height = 350, 250
            fallback_index = len(canvas_layout["nodes"])
            for n in new_nodes:
                nid = n["id"]
                # Heuristic: use title or ID to map
                found = False
                for key, (fx, fy) in fixed_positions.items():
                    if key.lower() in n.get("title", "").lower() or key.lower() in nid.lower():
                        canvas_layout["nodes"][nid] = {"x": fx, "y": fy, "width": 250, "height": 150}
                        found = True
                        break
                if not found:
                    canvas_layout["nodes"][nid] = {
                        "x": (fallback_index % grid_cols) * cell_width,
                        "y": (fallback_index // grid_cols) * cell_height + 1200,
                        "width": 250,
                        "height": 150
                    }
                    fallback_index += 1
        else:
            # Default grid layout
            grid_cols = 5
            cell_width, cell_height = 300, 200
            new_node_index = len(canvas_layout["nodes"])

            for n in new_nodes:
                nid = n["id"]
                x = (new_node_index % grid_cols) * cell_width
                y = (new_node_index // grid_cols) * cell_height

                canvas_layout["nodes"][nid] = {
                    "x": x,
                    "y": y,
                    "width": 250,
                    "height": 150
                }
                new_node_index += 1

    output_dir = os.path.dirname(layout_cache_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(layout_cache_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(layout, f, indent=2)

    return layout

if __name__ == '__main__':
    stabilize_layout(
        "vault-gewebe/obsidian-bridge/meta/graph/graph.v1.json",
        "vault-gewebe/obsidian-bridge/meta/graph/layout.v1.json"
    )
