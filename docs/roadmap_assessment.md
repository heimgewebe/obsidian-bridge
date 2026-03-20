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
- **Tests implementieren:** Eine Suite von Python-Tests (Smoke, Rendering, Layout-Stabilität) und BATS-Tests läuft. Dedizierte Basistests für die derzeit implementierten Layout-Typen (Hierarchy, Organsystem, Cluster, Timeline, Radial) existieren nun, um grundlegende Invarianten abzusichern. Es fehlt jedoch weiterhin Testtiefe für komplexere Layout-Randfälle und Algorithmus-Schwächen.
- **Phase 4 – Vollständige Abdeckung:** Topic-Hubs und Index sind über Specs implementiert. Echte Kalender-Monatsfilter (`calendar_month`) sind implementiert und arbeiten in UTC deterministisch. Rollierende Fenster (`date_window_days: 30`) existieren weiterhin für relative Zeitbezüge. Offen bleibt der breite Ausbau weiterer Specs.
- **Echter Kalender-Monatsfilter:** Ein deterministischer Filter (`calendar_month`) für monatsscharfe Rollups (z. B. `events-2026-03.canvas`) auf Basis der Dokumenten-Zeitstempel wurde implementiert, inklusive Contracts-first Schema-Validation und Runtime-Schutz gegen ungültige Monate.

### 3. Offen
- **Vollständige Spec-Abdeckung (Phase 4):** Die breite Anlage aller weiteren Monats- oder Themen-Specs (obwohl die Filter-Maschinerie dafür jetzt bereitsteht).
- **Risiko-/Nutzenabschätzung / Alternativpfad:** Konzeptionelle Phase; auf Code-Ebene nicht direkt darstellbar.

---

## Jüngster Umsetzungsschritt: Layout-Tests (Hierarchy & Organsystem)

Die Roadmap listete "Tests implementieren" als teilweise offen, insbesondere in Bezug auf lückenhafte Layout-Testabdeckung für diverse Canvas-Klassen.
Es wurden dedizierte Basistests für die noch fehlenden Layout-Typen implementiert:
1. `test_layout_hierarchy.py`: Prüft deterministisches Gruppieren nach `kind` (`concept`, `entity`, `other`) sowie X-Positionsinkremente zur Vermeidung von Overlaps in den Layern.
2. `test_layout_organsystem.py`: Verifiziert Invarianten wie die Positionierung bekannter Repos (`chronik`, `hausKI`, etc.) an fixierten (x, y) Koordinaten sowie das Fallback-Grid-Verhalten für unbekannte Knoten. Dabei wurde bewusst darauf geachtet, bekannte Schwächen (wie Überlappungen von Knoten desselben Typs) nicht als hartes Soll-Verhalten einzufrieren.

Durch diese Ergänzungen wurde die Basisabdeckung für die derzeit implementierten Layout-Typen auf eine breite Basis gestellt, auch wenn Randfall-Validierungen weiterhin ausbaufähig bleiben.
