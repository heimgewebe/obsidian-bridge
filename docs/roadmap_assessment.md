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
- **Phase 2 – Deterministische Canvas-Renderer:** Die Grundformen der Layout-Klassen sind implementiert. *Timeline* und *Radial* wirken robust und verwenden Sortierungen/Ringe deterministisch. Es gibt inzwischen eine dedizierte *Cluster*-Implementierung, die deterministisch und "incrementally stable" im Basissinn arbeitet (Knoten werden anhand primärer Tags gruppiert). Eine tiefere semantische Gruppierungslogik für komplexere Sub-Cluster-Szenarien fehlt jedoch noch. Auch *System* ist momentan noch eher elementar.
- **Tests implementieren:** Eine wachsende Suite von Python-Tests (z.B. `test_layout_timeline.py`, `test_validate_specs.py`, `test_layout_cluster.py`) und BATS-Tests laufen durch. Es fehlen jedoch dezidierte Testabdeckungen für alle komplexeren Layout-Randfälle.

### 3. Offen
- **Phase 4 – Vollständige Abdeckung (Monats-/Rollup-Canvas):** Es fehlen noch deklarative Spezifikationen für periodische Rollups. Die Roadmap fordert z.B. "Monats-Canvas". Ein solcher Spec-Vertrag existiert in `config/canvas-specs/` bisher nicht.
- **Risiko-/Nutzenabschätzung / Alternativpfad:** Konzeptionelle Phase; auf Code-Ebene nicht direkt darstellbar.

---

## Plan-Optimierung & Nächster Umsetzungsschritt

**Ursprüngliche Annahme / Reihenfolge:**
Der nächste implizite Schritt gemäß Roadmap wäre vermutlich der restlose Ausbau von "Phase 4 - Vollständige Abdeckung", indem wir direkt hunderte Specs anlegen.

**Optimiertes Vorgehen (Architekturwahrheit vor Aktionismus):**
Einfach nur YAML-Dateien (Monats-Rollups) anzulegen, hätte eine neue Baustelle geöffnet, solange die Darstellungslogik für die zugrundeliegenden Layouts (insbesondere das *Cluster-Layout*, das in Observatorium-Rollups massiv genutzt werden wird) noch auf einem rudimentären Grid-Fallback basierte. Ein solches Vorpreschen in Phase 4 ohne stabile Cluster-Darstellung hätte unweigerlich zu unlesbarem "Graph Spaghetti" geführt, dem in der Blaupause explizit entgegengewirkt werden soll.

**Jüngster Umsetzungsschritt:**
Nachdem die **Cluster-Layout-Stabilisierungslogik** in `scripts/graph/stabilize_layout.py` implementiert und über `tests/test_layout_cluster.py` abgesichert wurde, ist die Basis für Cluster-Layouts (Phase 2) belastbar.
Daraufhin wurde diese Architektur in **Phase 4** angewendet: Als ein erster periodik-ähnlicher Rollup für das Observatorium wurde eine neue deklarative Spec (`config/canvas-specs/observatorium-rollup-last-30-days.yaml`) eingeführt.
Dieser Rollup testet das `cluster`-Layout an realen Artefakten. Er ist aktuell als rollierendes 30-Tage-Fenster umgesetzt (`date_window_days: 30`) und dient als verlässliche Brücke. Ein echter Kalender-Monatsfilter bleibt weiterhin offen.
