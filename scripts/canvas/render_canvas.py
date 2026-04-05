import collections
import json
import os
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta

def _get_edge_id(edge: Dict[str, Any]) -> str:
    edge_id = edge.get("id")
    if edge_id:
        return str(edge_id)

    frm = str(edge.get("from", "unknown"))
    rel = str(edge.get("relation", "unknown"))
    to = str(edge.get("to", "unknown"))
    return f"{frm}__{rel}__{to}"

def _generate_canvas_edge_id(base_edge_id: str) -> str:
    safe_prefix = base_edge_id.replace(":", "_").replace("->", "_")[:32]
    fingerprint = hashlib.md5(base_edge_id.encode('utf-8')).hexdigest()[:8]
    return f"{safe_prefix}_{fingerprint}"

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

def _parse_weight(edge: Dict[str, Any]) -> float:
    weight = edge.get("weight")
    if weight is None:
        return 0.0
    try:
        return float(weight)
    except (ValueError, TypeError):
        return 0.0

def _node_in_scope(node: Dict[str, Any], valid_types: list, required_tags: list) -> bool:
    """Returns True if the node passes both the artifact_type and required_tags filters.

    required_tags uses AND semantics: every tag in required_tags must be present on the
    node.  A node that carries only a subset of the required tags is excluded.
    """
    if valid_types and node.get("kind") not in valid_types:
        return False
    if required_tags:
        node_tags = set(node.get("tags") or [])
        if not all(tag in node_tags for tag in required_tags):
            return False
    return True

def render_canvas(spec_path: str, graph_path: str, layout_path: str, output_root: str = "vault-gewebe/obsidian-bridge") -> None:
    """
    Generates a deterministic .canvas file from a YAML declarative spec.
    Validates against size limits (Guards against graph-spaghetti).
    """
    import yaml
    # Load spec
    with open(spec_path, 'r') as f:
        spec = yaml.safe_load(f)

    # Load graph and layout
    graph = {"nodes": [], "edges": []}
    if os.path.exists(graph_path):
        with open(graph_path, 'r') as f:
            graph = json.load(f)

    # Pre-parse timestamps for performance optimization.
    # This avoids redundant calls to _parse_timestamp_utc in sorting and filtering.
    # Mutating in-place is safe here as the 'graph' object is local to render_canvas.
    for node in graph.get("nodes", []):
        node["_parsed_ts"] = _parse_timestamp_utc(node.get("timestamp"))

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
    filters = spec.get("filters") or {}
    max_nodes = filters.get("max_nodes", 100)
    max_edges = filters.get("max_edges", 200)
    max_depth_raw = filters.get("max_depth")
    max_clusters_raw = filters.get("max_clusters")
    date_window_days_raw = filters.get("date_window_days")
    calendar_month_raw = filters.get("calendar_month")
    prioritize_recent = filters.get("prioritize_recent", False)
    if not isinstance(prioritize_recent, bool):
        raise ValueError(f"Invalid prioritize_recent: {prioritize_recent}. Must be a boolean.")
    prioritize_strongest = filters.get("prioritize_strongest", False)
    if not isinstance(prioritize_strongest, bool):
        raise ValueError(f"Invalid prioritize_strongest: {prioritize_strongest}. Must be a boolean.")
    prioritized_relations_raw = filters.get("prioritized_relations", [])
    required_tags_raw = filters.get("required_tags", [])
    valid_relations = spec.get("relations", [])
    valid_types = spec.get("source", {}).get("artifact_types", [])

    if required_tags_raw:
        if not isinstance(required_tags_raw, list) or not all(isinstance(x, str) for x in required_tags_raw):
            raise ValueError(f"Invalid required_tags: {required_tags_raw}. Must be a list of strings.")
    required_tags = list(required_tags_raw) if required_tags_raw else []

    prioritized_relations = []
    if prioritized_relations_raw:
        if not isinstance(prioritized_relations_raw, list) or not all(isinstance(x, str) for x in prioritized_relations_raw):
            raise ValueError(f"Invalid prioritized_relations: {prioritized_relations_raw}. Must be a list of strings.")

        # Restrict prioritized_relations to valid_relations if valid_relations is defined
        if valid_relations:
            prioritized_relations = [rel for rel in prioritized_relations_raw if rel in valid_relations]
        else:
            prioritized_relations = prioritized_relations_raw

    max_depth = None
    if max_depth_raw is not None:
        try:
            max_depth = int(max_depth_raw)
            if max_depth < 0:
                raise ValueError()
        except ValueError:
            raise ValueError(f"Invalid max_depth: {max_depth_raw}. Must be a non-negative integer.")

    max_clusters = None
    if max_clusters_raw is not None:
        try:
            max_clusters = int(max_clusters_raw)
            if max_clusters < 1:
                raise ValueError()
        except ValueError:
            raise ValueError(f"Invalid max_clusters: {max_clusters_raw}. Must be an integer >= 1.")

    cutoff_date = None

    # Pre-parse timestamps to optimize filtering and sorting pipeline
    for n in graph.get("nodes", []):
        n["_parsed_ts"] = _parse_timestamp_utc(n.get("timestamp"))

    if date_window_days_raw is not None:
        try:
            date_window_days = int(date_window_days_raw)
            if date_window_days < 0:
                raise ValueError()
        except ValueError:
            raise ValueError(f"Invalid date_window_days: {date_window_days_raw}. Must be a non-negative integer.")

        # Der Zeitfilter wird am maximalen Graph-Timestamp verankert, um deterministische Builds zu erhalten.
        # Die Systemzeit wird bewusst nicht verwendet, um Churn zu vermeiden.
        # Nur in-scope Knoten (valid_types + required_tags) fließen in die Berechnung ein, damit
        # out-of-scope Knoten den Anker nicht verzerren.
        max_ts = None
        for n in graph.get("nodes", []):
            if not _node_in_scope(n, valid_types, required_tags):
                continue
            ts = n.get("_parsed_ts")
            if ts:
                if max_ts is None or ts > max_ts:
                    max_ts = ts

        if max_ts is None:
            raise ValueError(f"date_window_days is set to {date_window_days}, but no valid timestamps were found in the relevant graph nodes.")

        cutoff_date = max_ts - timedelta(days=date_window_days)

    calendar_month_target = None
    if calendar_month_raw is not None:
        if not isinstance(calendar_month_raw, str):
            raise ValueError(f"Invalid calendar_month: {calendar_month_raw}. Must be a string.")
        try:
            # Parse to ensure it's a real month and not 2026-13, and strictly enforce format.
            parsed_month = datetime.strptime(calendar_month_raw, "%Y-%m")
            calendar_month_target = parsed_month.strftime("%Y-%m")
        except ValueError:
            raise ValueError(f"Invalid calendar_month: {calendar_month_raw}. Must be a valid month in YYYY-MM format.")

    # Determine allowed nodes based on depth
    allowed_by_depth = set()
    if max_depth is not None:
        # We need a starting point for depth traversal relative to this canvas (filtered nodes/edges).
        relevant_node_ids = {
            n.get("id") for n in graph.get("nodes", [])
            if n.get("id") and _node_in_scope(n, valid_types, required_tags)
        }

        incoming_counts = {}
        adj = {}

        for edge in graph.get("edges", []):
            if valid_relations and edge.get("relation") not in valid_relations:
                continue
            u, v = edge.get("from"), edge.get("to")

            # Edges are only relevant if both ends are in relevant_node_ids
            if u in relevant_node_ids and v in relevant_node_ids:
                incoming_counts[v] = incoming_counts.get(v, 0) + 1
                if u not in adj: adj[u] = []
                adj[u].append(v)

        roots = sorted([nid for nid in relevant_node_ids if incoming_counts.get(nid, 0) == 0])

        # If there are no nodes with 0 incoming edges (e.g., a cycle), deterministically
        # pick the node with the lexicographically smallest ID as a fallback root.
        if not roots and relevant_node_ids:
            roots = [min(relevant_node_ids)]

        # BFS using deque
        queue = collections.deque([(root, 0) for root in roots])
        visited = set()

        while queue:
            curr, depth = queue.popleft()
            if curr in visited: continue
            visited.add(curr)
            if depth <= max_depth:
                allowed_by_depth.add(curr)
                # Sort neighbors to guarantee deterministic traversal order
                for neighbor in sorted(adj.get(curr, [])):
                    queue.append((neighbor, depth + 1))
    else:
        # If no depth limit, allow all nodes
        allowed_by_depth = {n.get("id") for n in graph.get("nodes", []) if n.get("id")}

    # Calculate clusters if max_clusters is set
    allowed_tags = None
    if max_clusters is not None:
        tag_counts = {}
        for node in graph.get("nodes", []):
            if not _node_in_scope(node, valid_types, required_tags):
                continue
            tags = node.get("tags") or []
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Sort tags by count descending, then alphabetically
        sorted_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))
        allowed_tags = {t[0] for t in sorted_tags[:max_clusters]}

    # Sort nodes deterministically before processing limits
    all_nodes = list(graph.get("nodes", []))
    if prioritize_recent:
        # Sort by timestamp descending (most recent first), then ID for determinism
        def _recent_node_sort_key(node: Dict[str, Any]) -> tuple:
            ts = node.get("_parsed_ts")
            node_id = str(node.get("id") or "")
            if ts is not None:
                # Valid dates go first, sorted by highest timestamp (using negation)
                return (0, -ts.timestamp(), node_id)
            else:
                # Missing or invalid dates go last
                return (1, 0, node_id)

        all_nodes.sort(key=_recent_node_sort_key)
    else:
        # Default deterministic sort, safely handling potential None IDs from dirty graphs
        all_nodes.sort(key=lambda x: str(x.get("id") or ""))

    # Process nodes up to max_nodes
    added_nodes = 0
    node_id_map = {}

    for node in all_nodes:
        node_id = node.get("id")
        if not node_id:
            # Skip nodes without a valid ID to avoid None mapping collisions
            continue

        if node_id not in allowed_by_depth:
            continue

        if allowed_tags is not None:
            node_tags = node.get("tags") or []
            # If the node has no tags that are in the allowed top N clusters, skip it
            # (Nodes without any tags are automatically skipped if max_clusters is set)
            if not node_tags or not any(t in allowed_tags for t in node_tags):
                continue

        if not _node_in_scope(node, valid_types, required_tags):
            continue

        if cutoff_date is not None:
            node_ts = node.get("_parsed_ts")
            if not node_ts or node_ts < cutoff_date:
                continue

        if calendar_month_target is not None:
            node_ts = node.get("_parsed_ts")
            if not node_ts:
                continue
            # Ensure time is evaluated in UTC to prevent timezone boundary Schrödinger months
            utc_ts = node_ts.astimezone(timezone.utc)
            node_month_str = utc_ts.strftime("%Y-%m")
            if node_month_str != calendar_month_target:
                continue

        if added_nodes >= max_nodes:
            break

        # Deterministic, locally dense canvas node ID based on the current included-node index
        canvas_node_id = f"canvas_node_{added_nodes}"
        node_id_map[node_id] = canvas_node_id

        node_layout = layout.get("nodes", {}).get(node_id, {"x": added_nodes*100, "y": 0, "width": 250, "height": 150})

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

    relation_rank = {rel: idx for idx, rel in enumerate(prioritized_relations)}

    all_edges = graph.get("edges", [])

    # Sort edges deterministically
    all_edges = sorted(
        all_edges,
        key=lambda e: (
            # Priority relation goes first
            relation_rank.get(e.get("relation"), float('inf')),
            # If prioritize_strongest is set, rank by highest weight first
            (_parse_weight(e) * -1) if prioritize_strongest else 0.0,
            str(_get_edge_id(e) or ""),
            str(e.get("from") or ""),
            str(e.get("to") or ""),
            str(e.get("relation") or "")
        )
    )

    for edge in all_edges:
        from_id = edge.get("from")
        to_id = edge.get("to")
        relation = edge.get("relation")

        if added_edges >= max_edges:
            break

        if valid_relations and relation not in valid_relations:
            continue

        if from_id in node_id_map and to_id in node_id_map:
            base_edge_id = _get_edge_id(edge)

            # Create a safe and collision-free ID for the canvas
            # We use a hash of the stable base_edge_id to ensure there are no collisions from normalization
            canvas_edge_id = _generate_canvas_edge_id(base_edge_id)

            canvas_model["edges"].append({
                "id": canvas_edge_id,
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
