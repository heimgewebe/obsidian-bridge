# Roadmap: Obsidian-Bridge & Automatische Canvas-Erzeugung

*Dieses Dokument vereint alle strukturellen Details, Konzepte und Architekturvorgaben der ursprünglichen `bridge-blaupause.md` und `canvas-blaupause.md` in einer abhakbaren Umsetzungs-Roadmap. Ziel ist es, die gesamte Logik verlustfrei in Implementierungsschritte zu übersetzen.*

## 1. Ziel & Rolle im System
- [ ] **Rollenverständnis etablieren:**
  - **Heimgewebe**: Artefakte erzeugen.
  - **Leitstand**: Systemzustand darstellen (operativ).
  - **Obsidian-Bridge**: Artefakte in Wissensraum überführen (erzeugt explorativen Wissensraum, keine Wahrheitsschicht).
  - **Obsidian**: Semantische Exploration (epistemisch).
- [ ] **Datenfluss sicherstellen:** `Heimgewebe → obsidian-bridge → Obsidian Vault` (Keine automatische Rückkopplung: `Obsidian Vault ↛ Heimgewebe`).
- [ ] **Kernprinzip Markdown:** Markdown bildet lineare Wissensrepräsentation (generierte Notizen).
- [ ] **Kernprinzip Canvas:** Canvas wird als reproduzierbares, überschreibbares und diffbares Build-Artefakt behandelt (keine manuelle Handzeichnung).

## 2. Vault-Struktur (`vault-gewebe/obsidian-bridge/`)
- [ ] Ordner `index/` (Einstieg: `start.md`, `navigation.md`, `latest.md`).
- [ ] Ordner `chronik/` (Systemgeschichte: `events/YEAR/MONTH/event--<date>--<id>.md`, `timelines/`, `rollups/`).
- [ ] Ordner `observatorium/` (Analytik: `insights/`, `contradictions/`, `uncertainty/`, `daily/`).
- [ ] Ordner `decisions/` (Entscheidungen: `policy/`, `preimages/`, `outcomes/`).
- [ ] Ordner `knowledge/` (Wissen: `entities/`, `concepts/`, `relations/`, `snapshots/`).
- [ ] Ordner `agents/` (Agentik: `runs/`, `prompts/`, `reviews/`).
- [ ] Ordner `scratch/` (Manuell/Experimentell: `hypotheses/`, `analyses/`, `maps/` - nicht automatisch überschrieben).
- [ ] Ordner `views/` (Kuratiert: `dashboards/`, `clusters/`, `narratives/`).
- [ ] Ordner `canvases/` (Auto-Canvas: `system/`, `chronik/`, `observatorium/`, `decisions/`, `knowledge/`, `index/`).
- [ ] Ordner `meta/` (Technisch: `sync/`, `manifests/`, `exports/`, `diagnostics/`, `graph/`).

## 3. Artefakt-Rendering (Markdown) & Synchronisation
- [ ] Dateinamen-Schema anwenden: `<artifact-type>--<date>--<id>.md` (z.B. `event--2026-03-08--evt-123.md`).
- [ ] Pipeline implementieren: `artifact → renderer → markdown note`.
- [ ] Frontmatter-Generierung umsetzen:
  ```yaml
  ---
  artifact_type: [Typ]
  artifact_id: [ID]
  source_repo: [Repo]
  generated_by: obsidian-bridge
  generated_at: TIMESTAMP
  origin_path: SOURCE_PATH
  confidence: medium
  ---
  ```
- [ ] Deterministische Synchronisation sicherstellen (read-only, idempotent, artifact-driven, Vault-Inhalte werden nicht inkonsistent überschrieben).

## 4. Architektur: Kanonischer Graph-Layer
- [ ] Datenfluss aufbauen: `Artefakte → Relationsextraktion → kanonischer Graph-Layer → Renderer (Markdown & Canvas)`.
- [ ] Graph-Artefakt definieren und ausgeben (`meta/graph/graph.v1.json`):
  - **Knotenmodell**: Repräsentation mit `id`, `kind`, `title`, `file_path`, `source_repo`, `timestamp`, `tags`.
  - **Kantenmodell**: Repräsentation mit `id`, `from`, `to`, `relation`, `weight`.
- [ ] Relationsextraktion implementieren: Extraktion aus strukturierten Artefakten (Events, Decisions, Insights etc.).
- [ ] Relationstypen unterstützen: `references`, `causes`, `informed`, `contradicts`, `derives_from`, `clusters_with`, `precedes`, `belongs_to_topic`.

## 5. Canvas-Klassen & Generierung
- [ ] Canvas-Knoten-Verlinkung sicherstellen (z.B. `node → [[chronik/events/2026/03/event...]]`).
- [ ] **System-Canvas** (`canvases/system/system-architecture.canvas`): Organe, Hauptflüsse.
- [ ] **Chronik-Canvas** (`canvases/chronik/events-latest.canvas`): Event-Ketten, zeitliche Relationen.
- [ ] **Observatorium-Canvas** (`canvases/observatorium/insight-network.canvas`): Erkenntniscluster, Widerspruchsnetze.
- [ ] **Decision-Canvas** (`canvases/decisions/decision-network.canvas`): Entscheidung, Preimage, Outcomes.
- [ ] **Knowledge-Canvas** (`canvases/knowledge/concept-network.canvas`): Konzepte, Entitäten.
- [ ] **Index-/Hub-Canvas** (`canvases/index/root.canvas`, `latest.canvas`, Themen-Hubs): Einstiegs-Mindmaps.

## 6. Canvas-Specs als Build-Input
- [ ] Deklaratives Spec-Format entwickeln (z.B. YAML in `config/canvas-specs/`): Spezifikation von `id`, `type`, `source.artifact_types`, `layout`, `filters`, `relations`, `output`.
- [ ] Begrenzungsregeln (Guards) gegen "Graph-Spaghetti" implementieren:
  - Maximalgrößen: `max_nodes`, `max_edges`, `max_depth`, `max_clusters`.
  - Fokusregeln: Stärkste Kanten, jüngste Artefakte priorisieren.
  - Rollup-Regeln: Hubs und Monats-Canvas statt unübersichtlicher Mega-Graphen.

## 7. Layout-Strategie & Persistenz
- [ ] Deterministisches Layout sicherstellen (kein destruktives Force-Layout bei Rebuilds).
- [ ] Layout-Typen pro Canvas-Klasse anwenden:
  - *Chronik*: Timeline (x=Zeit, y=Typ).
  - *Decisions*: Radial (Zentrum=Entscheidung, außen=Folgen).
  - *Observatorium*: Cluster (nach Thema/Unsicherheit).
  - *Knowledge*: Hierarchie (Konzepte oben, Artefakte unten).
  - *System*: Organsystem (Feste Positionen für Repos).
- [ ] Persistente Koordinaten umsetzen (`graph snapshot → layout cache → canvas render`).
- [ ] Layout-Artefakt erzeugen (`meta/graph/layout.v1.json` mit `x`, `y`, `width`, `height`).
- [ ] Layout-Regeln anwenden: Bestehende Knoten behalten Position, neue deterministisch anfügen, alte verschwinden.
- [ ] Neutrales Canvas-Modell (Zwischenstufe) erzeugen: `nodes` (`file`, `text`, `group`), `edges`, `viewport`.

## 8. Verzeichnis-Erweiterungen (Verträge, Skripte, Tests)
- [ ] Neue Contracts definieren:
  - `contracts/graph.v1.json`
  - `contracts/canvas-spec.v1.json`
  - `contracts/layout.v1.json`
- [ ] Graph-Skripte erstellen:
  - `scripts/graph/build_graph.py`
  - `scripts/graph/extract_relations.py`
  - `scripts/graph/stabilize_layout.py`
- [ ] Canvas-Skripte erstellen:
  - `scripts/canvas/render_canvas.py`
  - `scripts/canvas/render_all_canvases.py`
- [ ] Konfigurationen ablegen:
  - `config/canvas-specs/system.yaml`
  - `config/canvas-specs/chronik-latest.yaml`
  - etc.
- [ ] Test-Suites implementieren:
  - `tests/test_graph_build.py`
  - `tests/test_canvas_render.py`
  - `tests/test_layout_stability.py`

## 9. Phasen der Umsetzung (Renderer-Pipeline)

- [ ] **Phase 1 – Graph-Fundament**
  - Graph-Artefakt definieren.
  - Relationsextraktion implementieren.
  - Markdown weiter wie bisher rendern.
  - Output: `meta/graph/graph.v1.json`.

- [ ] **Phase 2 – Deterministische Canvas-Renderer**
  - Canvas-Writer implementieren.
  - Layout-Logik pro Canvas-Klasse implementieren.
  - Erste Canvas erzeugen: `system-architecture.canvas`, `events-latest.canvas`, `insight-network.canvas`.

- [ ] **Phase 3 – Spec-System**
  - Deklarative Canvas-Specs auslesen.
  - Render-Build über Specs aufbauen.
  - CI-Validierung umsetzen.

- [ ] **Phase 4 – Vollständige Abdeckung**
  - Alle restlichen Canvas-Klassen erzeugen (Hubs, Topics, Rollups).
  - Vollständiger Durchlauf: Artefakte → Relationen → Graph → Specs → Layout → Markdown/Canvas → Manifest/Diagnostics.

## 10. Prämissencheck & Risikomanagement
- [ ] Graph-Qualität vor Canvas-Generierung priorisieren (falls Relationen schwach sind, erst Graph-Modell härten).
- [ ] Layout-Stabilität über Schönfärberei setzen (Orientierung ist wichtiger).
- [ ] Strict enforcement: Keine manuelle Bearbeitung der erzeugten `.canvas`-Dateien im Vault.
