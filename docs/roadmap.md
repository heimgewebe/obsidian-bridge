# Roadmap: Obsidian-Bridge & Automatische Canvas-Erzeugung

*Dieses Dokument vereint alle Details, Architekturentscheidungen, Code-Blöcke und Rationale der Blaupausen. Ziel ist es, die Obsidian-Bridge so zu bauen, dass sie Heimgewebe-Artefakte deterministisch in einen explorativen Wissensraum (Markdown & Canvas) übersetzt.*

*Dieses Dokument dient als umsetzungsorientierte Roadmap.*

*Die konzeptionellen Referenzdokumente bleiben:*
- *[docs/bridge-blaupause.md](./bridge-blaupause.md)*
- *[docs/canvas-blaupause.md](./canvas-blaupause.md)*

*Bei Architekturfragen oder konzeptionellen Zweifeln gelten die Blaupausen als primäre Referenz.*

---

## 1. Zielbild & Systemarchitektur

Die Obsidian-Bridge übersetzt Heimgewebe-Artefakte in strukturierte Markdown-Notizen und generiert automatisch Canvas-Modelle zur visuellen Exploration des zugrunde liegenden Artefakt-Graphen.

- [x] **Rollen im System trennen:**
  - **Heimgewebe:** Artefakte erzeugen.
  - **Leitstand:** Systemzustand darstellen (operativ).
  - **Obsidian-Bridge:** Artefakte in Wissensraum überführen.
  - **Obsidian:** Semantische Exploration (epistemisch).
  - *Rationale:* Die Bridge erzeugt keine Wahrheitsschicht, sondern einen explorativen Wissensraum. Leitstand = operativ, Obsidian = epistemisch.
- [x] **Datenfluss & Rückkopplung sicherstellen:**
  - Datenfluss: `Heimgewebe → obsidian-bridge → Obsidian Vault`
  - Keine automatische Rückkopplung: `Obsidian Vault ↛ Heimgewebe`
- [x] **Render-Ausgaben aus kanonischem Graph-Modell erzeugen:**
  - Markdown-Notizen (lineare Wissensrepräsentation)
  - `.canvas`-Dateien (graphische Wissensräume / multidimensionale Mindmaps, visuelle Argumentationsketten, explorative Strukturmodelle, semantische Netzwerke)
  - *Pipeline:*
    ```text
    Heimgewebe-Artefakte
            ↓
    Relationsextraktion
            ↓
    kanonischer Graph-Layer
            ↓
    Renderer
       ↙         ↘
    Markdown     Canvas
    ```
- [x] **Canvas-Leitannahme durchsetzen:** Canvas wird als Build-Artefakt behandelt (reproduzierbar, überschreibbar, diffbar, nicht manuell als Wahrheit gepflegt). Canvas ist Renderer, nicht Denkraum.

---

## 2. Vault-Struktur umsetzen

Alle Inhalte liegen unter: `vault-gewebe/obsidian-bridge/`.
Erstelle die Verzeichnisstruktur mit folgenden Zielen und Eigenschaften:

- [x] **`index/`** (Einstiegspunkt)
  - `start.md`, `navigation.md`, `latest.md`
  - *Funktion:* Übersicht aktueller Artefakte, Navigation, Einstieg.
- [x] **`chronik/`** (Zeitliche Systemgeschichte)
  - `events/YEAR/MONTH/event--<date>--<id>.md`, `timelines/weekly.md`, `timelines/monthly.md`, `rollups/system-history.md`
  - *Funktion:* Rekonstruktion, Historie, Muster.
- [x] **`observatorium/`** (Analytische Ebene)
  - `insights/`, `contradictions/`, `uncertainty/`, `daily/`
  - *Funktion:* Erkenntnisse, Widerspruchsberichte, Unsicherheitsanalysen, tägliche Beobachtungen.
- [x] **`decisions/`** (Entscheidungsarchiv)
  - `policy/`, `preimages/`, `outcomes/`
  - *Funktion:* Entscheidungsrekonstruktion, Alternativenanalyse, Folgenbeobachtung.
- [x] **`knowledge/`** (Stabile Wissensstruktur)
  - `entities/`, `concepts/`, `relations/`, `snapshots/`
  - *Funktion:* Langfristige Wissensobjekte, semantische Systembeschreibung, strukturelle Zusammenhänge.
- [x] **`agents/`** (Agentische Aktivitäten)
  - `runs/`, `prompts/`, `reviews/`
  - *Funktion:* Transparenz automatisierter Prozesse, Nachvollziehbarkeit von Agententscheidungen.
- [x] **`scratch/`** (Freier Denkraum)
  - `hypotheses/`, `analyses/`, `maps/`
  - *Funktion:* manuell, experimentell, nicht automatisch synchronisiert.
- [x] **`views/`** (Kuratiertes Lesen)
  - `dashboards/`, `clusters/`, `narratives/`
  - *Funktion:* thematische Perspektiven, Synthese-Seiten, langfristige Interpretationen.
- [x] **`canvases/`** (Mehrdimensionale Wissensmodelle - *Dateiformat: *.canvas*)
  - `system/`, `chronik/`, `observatorium/`, `decisions/`, `knowledge/`, `investigations/`, `index/`
  - *Funktion:* Automatisch erzeugte grafische Wissensmodelle.
- [x] **`meta/`** (Infrastruktur der Bridge, nicht epistemisch)
  - `graph/` (kanonische Zwischenartefakte für Graph/Layout), `sync/` (Synchronisationsstatus), `manifests/` (Export-Manifeste), `exports/`, `diagnostics/` (Diagnosedaten).
- [x] **Erweiterbarkeit ermöglichen:** Neue Ebenen (z.B. `observatorium/models/`, `knowledge/ontologies/`, `canvases/strategy/`) müssen integrierbar bleiben, die Struktur bleibt stabil.

---

## 3. Artefakt-Rendering & Markdown-Generierung

Die Bridge arbeitet deterministisch: **read-only, idempotent, artifact-driven.** Vault-Aktualisierungen dürfen bestehende Inhalte nicht inkonsistent verändern.

- [x] **Dateinamen-Schema implementieren:**
  - *Regel:* `<artifact-type>--<date>--<id>.md`
  - *Beispiele:* `event--2026-03-08--evt-123.md`, `insight--2026-03-08--ins-44.md`, `decision--2026-03-08--dec-12.md`
- [x] **Frontmatter-Generierung integrieren:**
  ```yaml
  ---
  artifact_type: event
  artifact_id: evt-123
  source_repo: chronik
  generated_by: obsidian-bridge
  generated_at: TIMESTAMP
  origin_path: SOURCE_PATH
  confidence: medium
  ---
  ```
- [x] **Canvas-Strukturprinzip (Knotenverlinkung):** Canvas-Knoten müssen direkt auf Artefaktseiten verlinken.
  - *Beispiel:*
    ```text
    node → [[chronik/events/2026/03/event--2026-03-08--evt-123]]
    node → [[decisions/policy/decision--2026-03-08--dec-12]]
    node → [[observatorium/insights/insight--2026-03-08--ins-44]]
    ```

---

## 4. Graph-Layer & Relationsextraktion

Der Graph-Layer ist die kanonische interne Render-Grundlage für Canvas. Er stellt keine neue systemische Wahrheitsschicht neben Heimgewebe dar, sondern dient ausschließlich der deterministischen Ableitung von Canvas-Strukturen. **Artefakte + Relationen** sind die Quelle, nicht Markdown.

- [ ] **Relationen extrahieren:** (teilweise / Scaffold angelegt - Basisfunktion da, keine vollständige Taxonomie-Abdeckung)
  - Quellen: chronik-Events, policy.decision, decision.preimage, knowledge.observatory, contradiction.report, uncertainty.report.
  - *Relationstypen:* references, causes, informed, contradicts, derives_from, clusters_with, precedes, belongs_to_topic.
  - *Auflösung:* Deterministische Link-Auflösung mit Priorität (exakter Pfad > basename). Mehrdeutigkeiten erzeugen Warnungen statt stiller Fehler.
- [x] **Internes Graph-Artefakt erzeugen (`meta/graph/graph.v1.json`):** (Scaffold angelegt)
  - Soll `nodes`, `edges`, optional `clusters`, optional `topics` enthalten.
- [x] **Knotenmodell definieren (Artefakt/Konzept):**
  ```json
  {
    "id": "event:evt-123",
    "kind": "event",
    "title": "Event 2026-03-08",
    "file_path": "chronik/events/2026/03/event--2026-03-08--evt-123.md",
    "source_repo": "chronik",
    "timestamp": "2026-03-08T12:00:00Z",
    "tags": ["chronik", "event"]
  }
  ```
- [x] **Kantenmodell definieren (Beziehung):**
  ```json
  {
    "id": "edge:event:evt-123->decision:dec-12",
    "from": "event:evt-123",
    "to": "decision:dec-12",
    "relation": "informed",
    "weight": 0.8
  }
  ```

---

## 5. Canvas-Specs als Build-Input

Jede Canvas-Datei muss durch eine deklarative Spec definiert werden (keine verteilte Logik, CI-prüfbar).

- [x] **Spec-Format implementieren:** (Scaffold angelegt)
  ```yaml
  id: observatorium-insight-network
  type: observatorium
  source:
    artifact_types:
      - insight
      - contradiction
      - uncertainty
  layout: cluster
  filters:
    max_nodes: 80
    date_window_days: 30
  relations:
    - references
    - contradicts
    - clusters_with
  output: canvases/observatorium/insight-network.canvas
  ```
- [x] **Begrenzungsregeln (Guards) gegen Graph-Spaghetti:** (Teilweise in Render-Engine vorhanden)
  - Maximalgrößen pro Canvas: `max_nodes`, `max_edges`, `date_window_days`, `max_depth`, `max_clusters` als Basis-Guards implementiert.
  - Fokusregeln:
    - priorisierte Relationstypen bei der deterministischen Kanten-Auswahl unter max_edges implementiert.
    - stärkste Kanten: Basisheuristiken implementiert (`prioritize_strongest`).
    - jüngste Artefakte als eigene Fokusheuristik: Basisheuristiken implementiert (`prioritize_recent`).
  - Rollup-Regeln (Statt eines Mega-Canvas): echte periodische Rollups ausstehend (z. B. echter Monats-Filter).

---

## 6. Layout-Strategie & Persistenz

Layout muss deterministisch sein. Ein rein physikalisches Force-Layout ist ungeeignet, da es Orientierung zerstört.
*Pipeline:* `graph snapshot → layout cache → canvas render`

- [ ] **Layout-Typen pro Canvas-Klasse implementieren:** (teilweise implementiert)
  - `chronik/*` (Timeline-Layout): links → rechts = Zeit, oben / unten = Typgruppen (deterministisch implementiert).
  - `decisions/*` (Radial-Layout): Zentrum = Entscheidung, innen = Inputs / Preimages, außen = Outcomes / Folgen (deterministisch implementiert mit Golden Angle).
  - `observatorium/*` (Cluster-Layout): Cluster je Thema / Unsicherheitsfeld / Widerspruchsgruppe (Basis deterministisch implementiert, tiefere Semantik offen).
  - `knowledge/*` (Hierarchie-/Graph-Layout): Konzepte oben, Entitäten mittig, konkrete Artefakte unten (deterministisch implementiert).
  - `system/*` (Organsystem-Layout): Feste Positionen für Organe (Grundform/Scaffold angelegt).
- [x] **Persistentes Layout-Artefakt erzeugen (`layout.v1.json`):** (Scaffold angelegt)
  - Enthält pro Knoten: `x`, `y`, `width`, `height`.
  - *Regel:* Bestehende Knoten behalten Position, neue werden deterministisch ergänzt, gelöschte verschwinden kontrolliert.
- [x] **Interne Canvas-Repräsentation erzeugen:** (Scaffold angelegt)
  ```json
  {
    "nodes": [...],
    "edges": [...],
    "viewport": {...}
  }
  ```
  - *Node-Typen:* `file` (verweist auf Markdown), `text` (erklärender Text), `group` (logischer Clusterbereich).
  - *Edge-Typen:* Standardkante mit Relation, optional beschriftet, optional stilcodiert nach Typ.

---

## 7. Automatisch generierte Canvas-Klassen

Alle definierten Canvas-Klassen müssen automatisch durch die Bridge generiert werden.

- [x] **System-Canvas** (`canvases/system/system-architecture.canvas`)
  - *Inhalt:* Organe / Repos, Hauptflüsse, zentrale Artefaktadern.
  - *Quelle:* Repo-Rollenmatrix, bekannte Artefaktflüsse.
- [x] **Chronik-Canvas** (`events-latest.canvas`, `events-2026-03.canvas`)
  - *Inhalt:* Event-Ketten, zeitliche Beziehungen (Event → Insight → Decision).
  - *Quelle:* Chronik-Artefakte, zeitliche Kanten.
- [x] **Observatorium-Canvas** (`insight-network.canvas`, `contradiction-network.canvas`)
  - *Inhalt:* Erkenntniscluster, Widerspruchsnetze, Unsicherheitszonen.
- [x] **Decision-Canvas** (`decision-network.canvas`, `decision--2026-03-08--dec-12.canvas`)
  - *Inhalt:* Entscheidung, Preimage, Referenz-Ereignisse, Outcomes.
- [x] **Knowledge-Canvas** (`concept-network.canvas`, `entity-network.canvas`) (Basisimplementierung vorhanden, Generierung aktiv)
  - *Inhalt:* Konzepte, Entitäten, Relationen.
- [x] **Index- und Hub-Canvas** (Basisimplementierung vorhanden, Generierung aktiv)
  - **Root-Canvas** (`canvases/index/root.canvas`): Knoten für System, Chronik, Observatorium, Decisions, Knowledge, Latest. Dient als Start-Mindmap.
  - **Topic-Hubs** (`topic--chronik.canvas`, `topic--observatorium.canvas`): Thematische Navigation, Einstieg in Untergraphen.
  - **Latest-Canvas** (`canvases/index/latest.canvas`).

---

## 8. Verzeichnis-Erweiterungen (Verträge, Skripte, Tests)

- [x] **Neue Contracts erstellen:**
  - `contracts/graph.v1.json`
  - `contracts/canvas-spec.v1.json`
  - `contracts/layout.v1.json`
- [x] **Neue Python Skripte schreiben:** (Scaffold angelegt)
  - `scripts/graph/build_graph.py`
  - `scripts/graph/extract_relations.py`
  - `scripts/graph/stabilize_layout.py`
  - `scripts/canvas/render_canvas.py`
  - `scripts/canvas/render_all_canvases.py`
- [x] **Spezifikationen (YAML) anlegen:**
  - `config/canvas-specs/system.yaml`
  - `config/canvas-specs/chronik-latest.yaml`
  - `config/canvas-specs/observatorium-insights.yaml`
  - `config/canvas-specs/decisions-network.yaml`
- [ ] **Tests implementieren:** (teilweise / Basisimplementierung vorhanden, lückenhaft für diverse Canvas-Klassen, Timeline/Cluster/Radial/Layout-Stabilität getestet)
  - `tests/test_graph_build.py`
  - `tests/test_canvas_render.py`
  - `tests/test_layout_stability.py`
  - Ordner: `tests/fixtures/graph/`, `tests/fixtures/canvas/`

---

## 9. Renderer-Pipeline & Umsetzungsphasen

Die Umsetzung erfolgt iterativ in 4 Phasen und durchläuft eine feste Render-Pipeline (1. Artefakte lesen → 2. Relationen extrahieren → 3. Graph bauen → 4. Specs auswerten → 5. Layout stabilisieren → 6. Markdown rendern → 7. Canvas rendern → 8. Manifest/Diagnostics).

- [x] **Phase 1 – Graph-Fundament**
  - Graph-Artefakt definieren.
  - Relationsextraktion implementieren.
  - Markdown weiter wie bisher rendern.
  - *Output:* `meta/graph/graph.v1.json`
- [ ] **Phase 2 – Deterministische Canvas-Renderer** (teilweise - Grundformen der Layout-Klassen implementiert, z.B. Timeline, Radial & Cluster robuster; System noch ausbaufähig)
  - Canvas-Writer implementieren.
  - Layout-Logik pro Canvas-Klasse bauen.
  - *Erste Canvas erzeugen:* `system-architecture.canvas`, `events-latest.canvas`, `insight-network.canvas`.
- [x] **Phase 3 – Spec-System** (Basisimplementierung und CI/Build-Integration vorhanden)
  - Deklarative Canvas-Specs.
  - Render-Build über Specs.
  - CI-Validierung (Schema-Validierung in build pipeline integriert).
- [ ] **Phase 4 – Vollständige Abdeckung**
  - Alle definierten Canvas-Klassen erzeugen (Hub-Canvas, Topic-Canvas, Monats-/Rollup-Canvas teilweise).

---

## 10. Prämissencheck & Risiko-/Nutzenabschätzung

Die Architektur basiert auf der Annahme, dass Relationen ausreichend formalisierbar sind und Canvas als Build-Artefakt akzeptiert wird.

- [ ] **Alternativpfad berücksichtigen:** Wenn Beziehungen zu schwach formalisiert sind, muss **erst die Graphqualität erhöht werden**, bevor die Canvas-Erzeugung erfolgt.
- [ ] **Nutzen realisieren:** Vollständige visuelle Wissensoberfläche, konsistenter Wissensgraph, keine manuelle Pflege. Obsidian wird semantischer Spiegel.
- [ ] **Risiken mit Gegenmaßnahmen mindern:**
  - *Graph-Spaghetti / Layout-Drift:* Canvas-Specs, Layout-Cache, Größenlimits, Fokusregeln, Rollups einsetzen.
  - *Gefahr dekorativer statt nützlicher Graphen:* Layout-Stabilität ist wichtiger als Schönheit (Orientierung schlägt visuelle Spielerei).
  - *Empfohlene Reihenfolge:* `Artefakte → Graph-Layer → Canvas-Specs → deterministische Renderer → vollständige Auto-Canvas-Erzeugung`.
