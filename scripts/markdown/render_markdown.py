import json
import os
import yaml
from typing import Dict, Any

def calculate_deterministic_path(node: Dict[str, Any]) -> str:
    """Calculates the file path deterministically based on the roadmap schema."""
    kind = node.get("kind", "unknown")
    node_id = node.get("id", "")
    artifact_id = node_id.split(":")[-1] if ":" in node_id else node_id

    timestamp = node.get("timestamp", "")
    if not timestamp and not node.get("file_path"):
        raise ValueError(f"Missing both timestamp and file_path for node: {node_id}")

    date_str = timestamp.split("T")[0] if timestamp else "unknown-date"

    # E.g. event--2026-03-08--evt-123.md
    filename = f"{kind}--{date_str}--{artifact_id}.md"

    source_repo = node.get("source_repo", "unknown")

    if source_repo == "chronik" and kind == "event":
        parts = date_str.split("-")
        if len(parts) >= 2:
            year, month = parts[0], parts[1]
            return f"chronik/events/{year}/{month}/{filename}"
        return f"chronik/events/{filename}"
    elif source_repo == "decisions" and kind == "decision":
        return f"decisions/policy/{filename}"
    elif source_repo == "observatorium" and kind == "insight":
        return f"observatorium/insights/{filename}"
    elif source_repo == "index" and kind == "system_component":
        # Keep original logic if it's special like index/navigation.md
        return node.get("file_path", f"index/{filename}")

    # Fallback to file_path from node if present, else a generic path
    return node.get("file_path", f"{source_repo}/{filename}")

def render_markdown(graph_path: str, output_root: str = "vault-gewebe/obsidian-bridge") -> None:
    """
    Generates deterministic Markdown files from the canonical graph layer.
    Enforces the filename schema and YAML frontmatter as defined in the blueprint.
    Generates Markdown links between nodes based on graph edges.
    """
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"Graph file not found: {graph_path}")

    with open(graph_path, 'r', encoding="utf-8") as f:
        graph = json.load(f)

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # Map node id to deterministic file path
    node_paths = {}
    for node in nodes:
        node_id = node.get("id")
        if not node_id:
            continue

        canonical_path = node.get("file_path")
        calculated_path = calculate_deterministic_path(node)

        if canonical_path:
            if canonical_path != calculated_path:
                # canonical_path from the graph is the absolute source of truth.
                # calculated_path is only used to detect architectural drift.
                import sys
                print(f"Warning: Node {node_id} has canonical path '{canonical_path}' which differs from calculated deterministic path '{calculated_path}'. Using canonical.", file=sys.stderr)
            file_path = canonical_path
        else:
            file_path = calculated_path

        node_paths[node_id] = file_path

    # Group edges by node
    # outgoing edges
    outgoing_edges = {}
    # incoming edges
    incoming_edges = {}
    for edge in edges:
        from_id = edge.get("from")
        to_id = edge.get("to")
        relation = edge.get("relation")

        if from_id:
            outgoing_edges.setdefault(from_id, []).append((relation, to_id))
        if to_id:
            incoming_edges.setdefault(to_id, []).append((relation, from_id))

    for node in nodes:
        node_id = node.get("id", "")
        file_path = node_paths.get(node_id)
        if not file_path or not file_path.endswith(".md"):
            continue

        full_path = os.path.join(output_root, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        artifact_id = node_id.split(":")[-1] if ":" in node_id else node_id

        # Use the timestamp from the node for generated_at to be idempotent
        # If timestamp is missing, raise an error to enforce strict determinism
        generated_at = node.get("timestamp")
        if not generated_at:
            raise ValueError(f"Missing timestamp for node {node_id}, cannot deterministically generate 'generated_at'.")

        frontmatter = {
            "artifact_type": node.get("kind", "unknown"),
            "artifact_id": artifact_id,
            "source_repo": node.get("source_repo", "unknown"),
            "generated_by": "obsidian-bridge",
            "generated_at": generated_at,
            "origin_path": file_path,
            "confidence": "medium"  # default per blueprint
        }

        # Build content
        content_lines = []
        content_lines.append("---")
        # Dump YAML correctly formatted
        yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        content_lines.append(yaml_str.strip())
        content_lines.append("---")
        content_lines.append(f"\n# {node.get('title', 'Unknown Title')}\n")

        # Add basic tags if present
        tags = node.get("tags", [])
        if tags:
            tag_str = " ".join([f"#{t}" for t in tags])
            content_lines.append(f"{tag_str}\n")

        content_lines.append(f"*This is a generated placeholder for the artifact {artifact_id}.*\n")

        # Add links based on edges
        has_relations = False
        relations_text = []

        out_edges = outgoing_edges.get(node_id, [])
        if out_edges:
            relations_text.append("## Ausgehende Relationen\n")
            for relation, to_id in sorted(out_edges, key=lambda x: (x[0], x[1])):
                to_path = node_paths.get(to_id)
                if to_path:
                    # Obsidian link without the .md extension usually, but we can also use file path
                    # Let's use standard obsidian format [[file_path_without_md]]
                    link_target = to_path.replace(".md", "")
                    relations_text.append(f"- **{relation}** -> [[{link_target}]]")
            relations_text.append("\n")
            has_relations = True

        in_edges = incoming_edges.get(node_id, [])
        if in_edges:
            relations_text.append("## Eingehende Relationen\n")
            for relation, from_id in sorted(in_edges, key=lambda x: (x[0], x[1])):
                from_path = node_paths.get(from_id)
                if from_path:
                    link_target = from_path.replace(".md", "")
                    relations_text.append(f"- <- **{relation}** [[{link_target}]]")
            relations_text.append("\n")
            has_relations = True

        if has_relations:
            content_lines.extend(relations_text)

        with open(full_path, "w", encoding="utf-8", newline="\n") as f_out:
            f_out.write("\n".join(content_lines))

if __name__ == "__main__":
    import sys
    graph_path = sys.argv[1] if len(sys.argv) > 1 else "vault-gewebe/obsidian-bridge/meta/graph/graph.v1.json"
    render_markdown(graph_path)
