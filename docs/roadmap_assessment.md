# Roadmap Assessment

## Befund: Ist-Zustand vs. Blaupause/Roadmap

Basierend auf einer systematischen Untersuchung des Repositories (Konfigurationen in `config/canvas-specs`, Pipeline `make build`, Tests in `tests/`, Python-Scripte unter `scripts/` und Ziel-Output unter `vault-gewebe/obsidian-bridge/`) ergibt sich folgendes Bild:

### 1. Bereits umgesetzt (Erledigt)
- **Vault-Struktur:** Komplett angelegt (`chronik/`, `observatorium/`, `decisions/`, `knowledge/`, `canvases/`, `meta/` existieren und entsprechen dem Zielbild).
- **Dateinamen-Schema & Frontmatter:** `render_markdown.py` generiert deterministische Pfade und konformes YAML-Frontmatter (`artifact_type`, `artifact_id`, `generated_at`).
- **Graph-Layer:** `build_graph.py` erzeugt `meta/graph/graph.v1.json` deterministisch aus Markdown-Artefakten (Idempotenz ist implementiert).
- **Canvas-Specs als Build-Input:** Ein ausgebautes YAML-Spec-System (`contracts/canvas-spec.v1.json`) samt CI-Integration und Pipeline-Integration (`make build` -> `validate_specs.py`) ist vorhanden und läuft stabil.
- **Interne Canvas-Repräsentation & Layout Cache:** `stabilize_layout.py` nutzt den Layout-Cache (`layout.v1.json`) deterministisch; Positionsverschiebungen werden vermieden.

### 2. Teilweise umgesetzt (Teilweise)
- **Relationen extrahieren:** Scaffold und Basisfunktion (`extract_relations.py`) sind implementiert und lesen aus Markdown-Wikilinks. Allerdings ist keine vollständige Taxonomie-Abdeckung nachgewiesen (z. B. komplexe Graph-Ableitungen über einfache Links hinaus fehlen).
- **Phase 2 – Deterministische Canvas-Renderer:** Die Grundformen der Layout-Klassen sind implementiert. *Timeline* und *Radial* wirken robust und verwenden Sortierungen/Ringe deterministisch. *Cluster* und *System* sind aber noch zu einfach (reines Grid ohne tiefere semantische Gruppierung; "Grundform/Scaffold angelegt" trifft zu).
- **Tests implementieren:** 8 Python-Tests (z.B. `test_layout_timeline.py`, `test_validate_specs.py`) und BATS-Tests laufen durch. Es fehlen jedoch dezidierte Testabdeckungen für komplexere Layout-Randfälle (wie z.B. exakte Koordinatenprüfung bei tiefen *Cluster*-Layouts).

### 3. Offen
- **Phase 4 – Vollständige Abdeckung (Monats-/Rollup-Canvas):** Es fehlen noch deklarative Spezifikationen für periodische Rollups. Die Roadmap fordert z.B. "Monats-Canvas". Ein solcher Spec-Vertrag existiert in `config/canvas-specs/` bisher nicht.
- **Risiko-/Nutzenabschätzung / Alternativpfad:** Konzeptionelle Phase; auf Code-Ebene nicht direkt darstellbar.

---

## Plan-Optimierung & Nächster Umsetzungsschritt

**Ursprüngliche Annahme / Reihenfolge:**
Der nächste implizite Schritt gemäß Roadmap wäre vermutlich der restlose Ausbau von "Phase 4 - Vollständige Abdeckung", indem wir direkt hunderte Specs anlegen.

**Optimiertes Vorgehen (Architekturwahrheit vor Aktionismus):**
Einfach nur YAML-Dateien (Monats-Rollups) anzulegen, öffnet eine neue Baustelle, solange die Darstellungslogik für die zugrundeliegenden Layouts (insbesondere das *Cluster-Layout*, das in Observatorium-Rollups massiv genutzt werden wird) noch rudimentär ist. Derzeit verarbeitet das *Cluster-Layout* in `stabilize_layout.py` neue Knoten nur extrem simpel via `grid_cols = 5` bzw. einem simplen linearen y-Offset pro Tag. Eine robuste Gruppierungslogik für Cluster fehlt.

Ein Vorpreschen in Phase 4 ohne stabiles *Cluster-Layout* führt zu "Graph Spaghetti", dem in der Blaupause explizit entgegengewirkt werden soll.

**Ausgewählter nächster Schritt:**
Wir implementieren die fehlende **Cluster-Layout-Stabilisierungslogik** in `scripts/graph/stabilize_layout.py` robuster aus und ergänzen einen expliziten Unit-Test (`tests/test_layout_cluster.py`) als Beweis.
Das stärkt die architektonische Basis (Souveränitätsrichtung), bleibt im Scope sauber (ein PR) und füllt exakt die Leerstelle "Cluster & System noch ausbaufähig" aus Phase 2. Danach sind Observatorium-Rollups (Phase 4) gefahrlos machbar.
