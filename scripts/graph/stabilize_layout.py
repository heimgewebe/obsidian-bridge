import json
import os
import yaml
import glob
import math
from typing import Dict, Any, List

import sys

def _get_canvas_specs(specs_dir: str) -> List[Dict[str, Any]]:
    specs = []
    if os.path.exists(specs_dir):
        for spec_path in sorted(glob.glob(os.path.join(specs_dir, '*.yaml'))):
            with open(spec_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)
                if isinstance(spec, dict):
                    specs.append(spec)
                else:
                    if spec is not None:
                        print(f"Warning: Skipping {spec_path} as it does not contain a valid YAML dictionary.", file=sys.stderr)
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

        # Spec-specific pruning: remove nodes that are no longer relevant to this canvas
        relevant_node_ids = {n["id"] for n in relevant_nodes if n.get("id")}
        irrelevant_node_ids = [nid for nid in canvas_layout["nodes"].keys() if nid not in relevant_node_ids]
        for nid in irrelevant_node_ids:
            del canvas_layout["nodes"][nid]

        # Add new nodes deterministically depending on layout_type
        # For simplicity, we implement a naive version of the requested layout types

        new_nodes = [n for n in relevant_nodes if n["id"] not in canvas_layout["nodes"]]

        if layout_type == "timeline":
            # links -> rechts = Zeit, oben / unten = Typgruppen
            # Sort by timestamp (fallback to id if timestamp is missing)
            new_nodes.sort(key=lambda x: (x.get("timestamp", ""), x.get("id", "")))

            # Pre-compute id_to_kind for O(1) lookups
            id_to_kind = {n.get("id", ""): n.get("kind", "unknown") for n in relevant_nodes if n.get("id")}

            # Collect existing kinds and deterministically assign y-offsets
            all_kinds = set(id_to_kind.values())
            sorted_kinds = sorted(list(all_kinds))

            kind_offsets = {kind: idx * 300 for idx, kind in enumerate(sorted_kinds)}

            # Find the maximum x_offset for each kind among existing nodes in this canvas
            existing_x_offsets = {kind: 0 for kind in sorted_kinds}
            for existing_nid, existing_node in canvas_layout.get("nodes", {}).items():
                existing_kind = id_to_kind.get(existing_nid, "unknown")
                if existing_kind in existing_x_offsets:
                    existing_x_offsets[existing_kind] = max(existing_x_offsets[existing_kind], existing_node.get("x", 0) + 350)

            for n in new_nodes:
                nid = n["id"]
                kind = n.get("kind", "unknown")

                # Determine placement
                y = kind_offsets[kind]
                x = existing_x_offsets[kind]

                # Update max x_offset for this kind
                existing_x_offsets[kind] += 350

                canvas_layout["nodes"][nid] = {
                    "x": x,
                    "y": y,
                    "width": 250,
                    "height": 150
                }

        elif layout_type == "radial":
            # Zentrum = Entscheidung, innen = Inputs/Preimages, außen = Outcomes/Folgen
            # Sort deterministically
            new_nodes.sort(key=lambda x: x.get("id", ""))

            # Simple heuristic: center has kind "decision", everything else is placed in rings
            center_x, center_y = 0, 0
            radius_inner = 500
            radius_outer = 1000

            # Find existing nodes to avoid shifting them
            existing_count = len(canvas_layout["nodes"])

            # Identify a decision node explicitly to place it at the center regardless of sort order
            decision_nodes = [n for n in new_nodes if n.get("kind") == "decision"]
            decision_node = decision_nodes[0] if decision_nodes else None

            # Process decision node first if it exists and there are no existing nodes
            if decision_node and existing_count == 0:
                nid = decision_node["id"]
                canvas_layout["nodes"][nid] = {
                    "x": center_x,
                    "y": center_y,
                    "width": 250,
                    "height": 150
                }
                existing_count += 1

            for n in new_nodes:
                if n["id"] in canvas_layout["nodes"]:
                    continue

                nid = n["id"]
                kind = n.get("kind", "unknown")

                # Place in concentric circles based on kind (preimages vs outcomes vs others)
                # For a robust deterministic mapping without true graph traversal:
                is_preimage = kind in ["insight", "event", "uncertainty"]
                radius = radius_inner if is_preimage else radius_outer

                # Distribute points deterministically based on their index
                # Add existing count to index to continue the circle deterministically
                idx = existing_count
                # Pseudo-random but deterministic angle based on idx to prevent direct overlaps
                # if the circle grows
                angle = (idx * 137.5) * (math.pi / 180.0) # Golden angle

                x = int(center_x + radius * math.cos(angle))
                y = int(center_y + radius * math.sin(angle))

                existing_count += 1

                canvas_layout["nodes"][nid] = {
                    "x": x,
                    "y": y,
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

        elif layout_type == "hierarchy":
            # Konzepte oben, Entitäten mittig, konkrete Artefakte unten
            # Group by kind deterministically
            hierarchy_levels = {
                "concept": 0,
                "entity": 400,
            }
            # Any other kind goes to bottom (800+)

            x_offsets = {
                "concept": 0,
                "entity": 0,
                "other": 0
            }

            # Initialize offsets based on existing nodes in each lane
            for existing_nid, existing_node in canvas_layout.get("nodes", {}).items():
                # Find kind of existing node
                existing_kind = "unknown"
                for rn in relevant_nodes:
                    if rn["id"] == existing_nid:
                        existing_kind = rn.get("kind", "unknown")
                        break

                if existing_kind == "concept":
                    x_offsets["concept"] = max(x_offsets["concept"], existing_node.get("x", 0) + 350)
                elif existing_kind == "entity":
                    x_offsets["entity"] = max(x_offsets["entity"], existing_node.get("x", 0) + 350)
                else:
                    x_offsets["other"] = max(x_offsets["other"], existing_node.get("x", 0) + 350)

            for n in new_nodes:
                nid = n["id"]
                kind = n.get("kind", "unknown")

                if kind == "concept":
                    y = hierarchy_levels["concept"]
                    x = x_offsets["concept"]
                    x_offsets["concept"] += 350
                elif kind == "entity":
                    y = hierarchy_levels["entity"]
                    x = x_offsets["entity"]
                    x_offsets["entity"] += 350
                else:
                    y = 800
                    x = x_offsets["other"]
                    x_offsets["other"] += 350

                canvas_layout["nodes"][nid] = {
                    "x": x,
                    "y": y,
                    "width": 250,
                    "height": 150
                }

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
