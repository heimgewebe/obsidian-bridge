import json
import os
import sys
import yaml
from typing import Dict, Any

# Ensure we can import from scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from scripts.graph.extract_relations import extract_relations, _parse_frontmatter

def build_graph(output_file: str = "vault-gewebe/obsidian-bridge/meta/graph/graph.v1.json") -> Dict[str, Any]:
    """
    Builds the canonical graph layer from Heimgewebe artifacts.
    This acts as the deterministic base for Canvas generation.
    """
    graph: Dict[str, Any] = {
        "nodes": [],
        "edges": [],
        "clusters": [],
        "topics": []
    }

    vault_dir = "vault-gewebe/obsidian-bridge"
    markdown_files = []

    # Find all markdown files, ignoring meta directory
    for root, dirs, files in os.walk(vault_dir):
        if 'meta' in dirs:
            dirs.remove('meta') # don't visit meta dir

        for file in files:
            if file.endswith(".md"):
                markdown_files.append(os.path.join(root, file))

    # To guarantee determinism
    markdown_files.sort()

    import re

    for md_path in markdown_files:
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
                fm = _parse_frontmatter(content)

                art_type = fm.get("artifact_type", "unknown")
                art_id = fm.get("artifact_id", os.path.basename(md_path).replace(".md", ""))
                node_id = f"{art_type}:{art_id}"

                # relative file path from vault root
                rel_path = os.path.relpath(md_path, vault_dir).replace('\\', '/')

                # Timestamp handling
                timestamp = fm.get("generated_at")
                if not timestamp:
                    # Skip files without usable date (e.g. index placeholders) to keep graph clean
                    print(f"Warning: Skipping {md_path} due to missing generated_at", file=sys.stderr)
                    continue

                # Convert datetime to string if yaml parsed it as such
                if hasattr(timestamp, "isoformat"):
                    timestamp = timestamp.isoformat()

                # Extract title
                title = fm.get("title")
                if not title:
                    h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    title = h1_match.group(1).strip() if h1_match else f"{art_type.capitalize()} {art_id}"

                # Extract tags
                tags = fm.get("tags")
                if tags is None:
                    # Find body tags (exclude those in frontmatter block usually by looking for lines with `#tag`)
                    # Using a simple lookbehind to avoid # markdown headings
                    tags_matches = re.findall(r"(?<!^)#([a-zA-Z0-9_\-]+)", content, re.MULTILINE)
                    # Also collect tags at the beginning of the line, as long as it isn't an H1 (e.g., #tag)
                    # Exclude matching `# ` (which is a heading)
                    tags_matches_start = re.findall(r"^#([a-zA-Z0-9_\-]+)", content, re.MULTILINE)
                    tags = list(set(tags_matches + tags_matches_start))
                elif not isinstance(tags, list):
                    tags = []

                node = {
                    "id": node_id,
                    "kind": art_type,
                    "title": title,
                    "file_path": rel_path,
                    "source_repo": fm.get("source_repo", "unknown"),
                    "timestamp": timestamp,
                    "tags": sorted(tags)
                }

                graph["nodes"].append(node)
        except Exception as e:
            print(f"Warning: Failed to parse {md_path}: {e}", file=sys.stderr)

    # To guarantee determinism
    graph["nodes"].sort(key=lambda x: x["id"])

    # Extract edges
    graph["edges"] = extract_relations(markdown_files)

    # Output to canonical graph artifact path
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(graph, f, indent=2)

    return graph

if __name__ == '__main__':
    build_graph()
