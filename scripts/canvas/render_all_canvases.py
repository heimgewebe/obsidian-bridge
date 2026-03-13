import os
import glob
import sys

# Ensure the scripts package can be found if executed directly
# Note: temporary bootstrap import path hack; replace with proper package/module execution later
# Preferred execution: python3 -m scripts.canvas.render_all_canvases
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scripts.canvas.render_canvas import render_canvas

def render_all_canvases(specs_dir: str, graph_path: str, layout_path: str) -> None:
    """
    Renders all defined Canvas classes by iterating through the specs directory.
    This generates System-Canvas, Chronik-Canvas, Observatorium-Canvas, Decision-Canvas, Knowledge-Canvas, and Index-Hubs.
    """
    specs = glob.glob(os.path.join(specs_dir, '*.yaml'))

    # Sort for determinism
    specs.sort()

    for spec_path in specs:
        print(f"Rendering canvas from spec: {spec_path}")
        render_canvas(spec_path, graph_path, layout_path)

if __name__ == '__main__':
    render_all_canvases(
        "config/canvas-specs",
        "vault-gewebe/obsidian-bridge/meta/graph/graph.v1.json",
        "vault-gewebe/obsidian-bridge/meta/graph/layout.v1.json"
    )
