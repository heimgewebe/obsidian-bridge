# Roadmap Assessment

## Befund: Ist-Zustand vs. Blaupause/Roadmap

Basierend auf einer systematischen Untersuchung des Repositories (Konfigurationen in `config/canvas-specs`, Pipeline `make build`, Tests in `tests/`, Python-Scripte unter `scripts/` und Ziel-Output unter `vault-gewebe/obsidian-bridge/`) ergibt sich folgendes Bild:

### 1. Bereits umgesetzt (Erledigt)
- **Vault-Struktur:** Komplett angelegt (`chronik/`, `observatorium/`, `decisions/`, `knowledge/`, `canvases/`, `meta/` existieren und entsprechen dem Zielbild).
- **Dateinamen-Schema & Frontmatter:** `render_markdown.py` generiert deterministische Pfade und konformes YAML-Frontmatter (`artifact_type`, `artifact_id`, `generated_at`).
- **Graph-Layer:** `build_graph.py` erzeugt `meta/graph/graph.v1.json` deterministisch aus Markdown-Artefakten (Idempotenz ist implementiert).
- **Canvas-Specs als Build-Input:** Ein ausgebautes YAML-Spec-System (`contracts/canvas-spec.v1.json`) samt CI-Integration und Pipeline-Integration (`make build` -> `validate_specs.py`) ist vorhanden und läuft stabil.
- **Interne Canvas-Repräsentation & Layout Cache:** `stabilize_layout.py` nutzt den Layout-Cache (`layout.v1.json`) deterministisch; Positionsverschiebungen werden vermieden.
- **Layout-Grundtypen:** Timeline, Radial, Cluster, Hierarchy und System sind implementiert und stabilisiert.

### 2. Teilweise umgesetzt (Teilweise)
- **Relationen extrahieren:** Scaffold und Basisfunktion (`extract_relations.py`) sind implementiert und lesen aus Markdown-Wikilinks. Komplexe semantische Ableitungen und vollständige Taxonomie-Abdeckung fehlen noch.
- **Phase 2 – Deterministische Canvas-Renderer:** Die Grundformen der Layout-Klassen sind implementiert und robuster geworden. Insbesondere das *Cluster*-Layout arbeitet deterministisch auf Basis von Tags. Tiefere semantische Gruppierungslogik fehlt jedoch.
- **Tests implementieren:** Eine Suite von Python-Tests (Smoke, Rendering, Layout-Stabilität) und BATS-Tests läuft. Es fehlen dezidierte Abdeckungen für komplexe Layout-Randfälle.
- **Phase 4 – Vollständige Abdeckung:** Topic-Hubs und Index sind über Specs implementiert. Bei den Rollup-Canvas ist ein 30-Tage-Fenster als Brücke umgesetzt, es fehlt aber ein echter Kalender-Monatsfilter für echte monatliche Chronik-Canvas.

### 3. Offen
- **Echter Kalender-Monatsfilter:** Ein deterministischer Filter (`calendar_month`) für monatsscharfe Rollups (z. B. `chronik-2026-03.canvas`) auf Basis der Dokumenten-Zeitstempel.
- **Risiko-/Nutzenabschätzung / Alternativpfad:** Konzeptionelle Phase; auf Code-Ebene nicht direkt darstellbar.

---

## Plan-Optimierung & Nächster Umsetzungsschritt

**Ursprüngliche Annahme / Reihenfolge:**
Die Roadmap forderte unter "Phase 4 - Vollständige Abdeckung" echte Monats-/Rollup-Canvas. Derzeit wurde sich mit `date_window_days: 30` beholfen.

**Optimiertes Vorgehen (Architekturwahrheit vor Aktionismus):**
Anstatt einfach blind hunderte Spezifikationsdateien zu erzeugen und die fehlende Filterfunktionalität zu ignorieren, ist es sinnvoller, den im Canvas-Renderer fehlenden `calendar_month`-Filter zu implementieren. Dies ist ein kleiner, robuster Hebel, der die Souveränitätsrichtung stärkt, sich nahtlos an die etablierte "Contracts-first" Architektur anlehnt (Update von `canvas-spec.v1.json`) und es erlaubt, deterministische, monatsbasierte Slices des Graphen zu extrahieren.

**Nächster Umsetzungsschritt:**
1. Erweiterung des Vertrags `contracts/canvas-spec.v1.json` um `calendar_month` unter `filters`.
2. Implementierung der deterministischen Filter-Logik nach `node.timestamp` in `scripts/canvas/render_canvas.py`.
3. Verifikation durch Hinzufügen von `test_render_canvas_calendar_month` in `tests/test_canvas_render.py`.
4. Anlage einer konkreten monatlichen Spec (`chronik-2026-03.yaml`) und Generierung des Artefakts (`chronik-2026-03.canvas`) als Proof-of-Concept.
