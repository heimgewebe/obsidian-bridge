import re
import os
import yaml
from typing import List, Dict, Any

def _parse_frontmatter(content: str) -> Dict[str, Any]:
    parts = content.split("---")
    if len(parts) >= 3:
        try:
            return yaml.safe_load(parts[1]) or {}
        except Exception:
            return {}
    return {}

def extract_relations(markdown_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Extracts implicit relations from structured artifacts via wikilinks.
    """
    relations = []

    # regex for [[path/to/artifact]]
    wikilink_regex = re.compile(r"\[\[(.*?)\]\]")

    # Map normalized file paths to artifact_id to create edges properly
    # First pass: map paths to IDs
    path_to_id = {}
    contents = {}

    for md_path in markdown_paths:
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
                contents[md_path] = content
                fm = _parse_frontmatter(content)

                # Assume standard format type:id if possible
                art_type = fm.get("artifact_type", "unknown")
                art_id = fm.get("artifact_id", os.path.basename(md_path).replace(".md", ""))
                node_id = f"{art_type}:{art_id}"

                path_to_id[md_path] = node_id
        except Exception:
            pass

    # Regexes for explicit relations
    # Form 1: - **relation_type** -> [[target]]
    rel_out_regex = re.compile(r"-\s*\*\*(.*?)\*\*\s*->\s*\[\[(.*?)\]\]")
    # Form 2: - <- **relation_type** [[target]]
    rel_in_regex = re.compile(r"-\s*<-\s*\*\*(.*?)\*\*\s*\[\[(.*?)\]\]")

    # Second pass: extract links and build edges
    edge_set = set()

    def add_edge(frm: str, to: str, rel: str):
        if frm != to:
            edge_key = f"{frm}->{to}:{rel}"
            if edge_key not in edge_set:
                edge_set.add(edge_key)
                relations.append({
                    "id": f"edge:{edge_key}",
                    "from": frm,
                    "to": to,
                    "relation": rel,
                    "weight": 1.0
                })

    for md_path, content in contents.items():
        source_id = path_to_id.get(md_path)
        if not source_id:
            continue

        lines = content.splitlines()
        for line in lines:
            # Check explicit outgoing
            out_match = rel_out_regex.search(line)
            in_match = rel_in_regex.search(line)

            if out_match:
                rel = out_match.group(1).strip()
                target_raw = out_match.group(2)
                links_to_process = [(target_raw, rel, "out")]
            elif in_match:
                rel = in_match.group(1).strip()
                target_raw = in_match.group(2)
                links_to_process = [(target_raw, rel, "in")]
            else:
                # Fallback to generic wikilinks
                links = wikilink_regex.findall(line)
                links_to_process = [(l, "references", "out") for l in links]

            for target_raw, rel, direction in links_to_process:
                # Clean link (remove aliases if present e.g. [[path|alias]])
                target_path = target_raw.split("|")[0]
                # Try to resolve target_path against path_to_id
                target_id = None

                # Simple heuristic: look for a path in path_to_id that ends with the target_path
                target_path_norm = target_path if target_path.endswith(".md") else f"{target_path}.md"

                for p, n_id in path_to_id.items():
                    if p.endswith(target_path_norm):
                        target_id = n_id
                        break

                if target_id:
                    if direction == "out":
                        add_edge(source_id, target_id, rel)
                    else:
                        add_edge(target_id, source_id, rel)

    # To guarantee determinism
    relations.sort(key=lambda x: x["id"])

    return relations

if __name__ == '__main__':
    # Typically would be called with a list of markdown file paths to parse
    extract_relations([])
