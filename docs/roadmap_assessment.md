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
- **Automatisch generierte Canvas-Klassen:** Die grundlegenden Klassen für System, Chronik, Observatorium, Decisions, Knowledge und Index sind implementiert.
- **Verzeichnis-Erweiterungen (Verträge, Skripte, Tests):** Basis-Erweiterungen wie Skripte, Verträge (Contracts) und einige Tests sind vorhanden.

### 2. Teilweise umgesetzt (Teilweise)
- **Relationen extrahieren:** Scaffold und Basisfunktion (`extract_relations.py`) sind implementiert und lesen aus Markdown-Wikilinks. Komplexe semantische Ableitungen und vollständige Taxonomie-Abdeckung fehlen noch.
- **Phase 2 – Deterministische Canvas-Renderer:** Die Grundformen der Layout-Klassen sind implementiert und robuster geworden. Insbesondere das *Cluster*-Layout arbeitet deterministisch auf Basis von Tags. Tiefere semantische Gruppierungslogik fehlt jedoch.
- **Tests implementieren:** Eine Suite von Python-Tests (Smoke, Rendering, Layout-Stabilität) und BATS-Tests läuft. Dedizierte Basistests für die derzeit implementierten Layout-Typen existieren. Es fehlt jedoch weiterhin Testtiefe für komplexere Layout-Randfälle und Algorithmus-Schwächen.
- **Phase 4 – Vollständige Abdeckung:** Topic-Hubs und Index sind über Specs implementiert. Echte Kalender-Monatsfilter (`calendar_month`) sind implementiert. Offen bleibt der breite Ausbau weiterer Specs (z. B. `investigations`).

### 3. Offen
- **Risiko-/Nutzenabschätzung / Alternativpfad:** Konzeptionelle Phase; auf Code-Ebene nicht direkt darstellbar.

---

## Jüngster Umsetzungsschritt: Canvas-Spec für Investigations

Die Roadmap listete "Phase 4 – Vollständige Abdeckung" als teilweise offen, insbesondere in Bezug auf die fehlende Implementierung spezifischer explorativer Canvas-Modelle.
Um diesen Punkt voranzutreiben, wurde der konkrete nächste Schritt durchgeführt:
1. Erstellung der deklarativen Spec `config/canvas-specs/investigations-topic-analysis.yaml`.
2. Diese Spec generiert deterministisch eine visuelle Repräsentation (Cluster-Layout) für den Bereich `investigations`, welche Events, Insights, Decisions und Hypothesen sowie deren ursächliche (`causes`), ableitende (`derives_from`), informierende (`informed`) und widersprechende (`contradicts`) Kanten zusammenführt.

Durch diesen Schritt wurde die Lücke in den "Automatisch generierten Canvas-Klassen" bezüglich `investigations` geschlossen und die Souveränität des Canvas-Renderings gestärkt, ohne tiefgreifende Architekturänderungen vorzunehmen.
