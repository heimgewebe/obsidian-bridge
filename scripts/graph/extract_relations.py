import re
import os
import yaml
from typing import List, Dict, Any, Optional

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
    basename_to_paths = {}
    contents = {}

    import sys

    # Vault-relative paths are canonical.
    vault_prefix = "vault-gewebe/obsidian-bridge/"

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

                # Normalize to use forward slashes
                norm_path = md_path.replace('\\', '/')
                # Strip prefix to store vault-relative paths
                if norm_path.startswith(vault_prefix):
                    norm_path = norm_path[len(vault_prefix):]

                path_to_id[norm_path] = node_id

                # Also map basename for fallback resolution
                basename = os.path.basename(norm_path)
                if basename not in basename_to_paths:
                    basename_to_paths[basename] = []
                basename_to_paths[basename].append(norm_path)

        except Exception:
            pass

    # Regexes for explicit relations
    # Form 1: - **relation_type** -> [[target]]
    rel_out_regex = re.compile(r"-\s*\*\*(.*?)\*\*\s*->\s*\[\[(.*?)\]\]")
    # Form 2: - <- **relation_type** [[target]]
    rel_in_regex = re.compile(r"-\s*<-\s*\*\*(.*?)\*\*\s*\[\[(.*?)\]\]")

    # Second pass: extract links and build edges
    edge_set = set()

    # Pre-defined known relation fields in frontmatter to map to edge types
    frontmatter_relation_fields = {
        "causes": "causes",
        "contradicts": "contradicts",
        "derives_from": "derives_from",
        "informed": "informed",
        "precedes": "precedes",
        "clusters_with": "clusters_with",
        "belongs_to_topic": "belongs_to_topic",
        "references": "references",
        "related": "references"  # Often used as a fallback or generic field
    }

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

    def resolve_target_id(target_raw: str, norm_md_path: str) -> Optional[str]:
        # Clean link (remove aliases if present e.g. [[path|alias]])
        target_path = target_raw.split("|")[0]
        # Clean link (remove anchor links if present e.g. [[path#heading]])
        target_path = target_path.split("#")[0]
        # Try to resolve target_path against path_to_id

        normalized_target_path = os.path.normpath(target_path).replace("\\", "/").lstrip("./")
        if normalized_target_path.startswith(vault_prefix):
            normalized_target_path = normalized_target_path[len(vault_prefix):]

        # 1. Exact path match
        exact_match_candidates = [
            p for p in path_to_id
            if p == normalized_target_path
        ]

        # 2. Exact path + .md match
        target_path_md = normalized_target_path if normalized_target_path.endswith(".md") else f"{normalized_target_path}.md"
        exact_md_match_candidates = [
            p for p in path_to_id
            if p == target_path_md
        ]

        # 3. Basename match
        basename = os.path.basename(target_path_md)
        basename_match_candidates = basename_to_paths.get(basename, [])

        # Resolution logic:
        if len(exact_match_candidates) == 1:
            return path_to_id[exact_match_candidates[0]]
        elif len(exact_match_candidates) > 1:
            candidates_str = ", ".join(exact_match_candidates)
            print(f"Warning: Ambiguous link '[[{target_raw}]]' in {norm_md_path}. Candidates: {candidates_str}. No edge created.", file=sys.stderr)
            return None
        elif len(exact_md_match_candidates) == 1:
            return path_to_id[exact_md_match_candidates[0]]
        elif len(exact_md_match_candidates) > 1:
            candidates_str = ", ".join(exact_md_match_candidates)
            print(f"Warning: Ambiguous link '[[{target_raw}]]' in {norm_md_path}. Candidates: {candidates_str}. No edge created.", file=sys.stderr)
            return None
        elif len(basename_match_candidates) == 1:
            return path_to_id[basename_match_candidates[0]]
        elif len(basename_match_candidates) > 1:
            candidates_str = ", ".join(basename_match_candidates)
            print(f"Warning: Ambiguous link '[[{target_raw}]]' in {norm_md_path}. Candidates: {candidates_str}. No edge created.", file=sys.stderr)
            return None

        return None

    for md_path, content in contents.items():
        norm_md_path = md_path.replace('\\', '/')
        if norm_md_path.startswith(vault_prefix):
            norm_md_path = norm_md_path[len(vault_prefix):]

        source_id = path_to_id.get(norm_md_path)
        if not source_id:
            continue

        # 1. Process Frontmatter relations
        fm = _parse_frontmatter(content)
        for fm_field, relation_type in frontmatter_relation_fields.items():
            targets = fm.get(fm_field, [])
            if targets:
                # If a single string is provided instead of a list, wrap it
                if isinstance(targets, str):
                    targets = [targets]
                if isinstance(targets, list):
                    for target in targets:
                        # Some frontmatters might include the [[ ]] syntax or quotes in lists, strip it
                        if isinstance(target, str):
                            # Remove surrounding brackets/whitespace
                            clean_target = target.strip("[] \t\"'")
                            # Handle cases where multiple links might be squished in a single string,
                            # though normally YAML parsing lists handles this.
                            target_id = resolve_target_id(clean_target, norm_md_path)
                            if target_id:
                                add_edge(source_id, target_id, relation_type)

        # 2. Process body links
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
                target_id = resolve_target_id(target_raw, norm_md_path)
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
