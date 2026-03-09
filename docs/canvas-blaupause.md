# Blaupause: Automatische Canvas-Erzeugung in obsidian-bridge

## 1. Ziel

Dieses Dokument vertieft die allgemeine Bridge-Blaupause technisch um den automatischen Canvas-Renderpfad.
* `bridge-blaupause.md` beschreibt die funktionale Rolle der Bridge.
* `canvas-blaupause.md` beschreibt die technische Architektur der automatischen Canvas-Erzeugung.
Die Canvas-Blaupause fokussiert die automatisch generierten Bereiche; manuelle Räume wie `scratch/` werden hier nicht vertieft.

Die Obsidian-Bridge erzeugt künftig zwei deterministische Darstellungsarten aus denselben Heimgewebe-Artefakten:
1. Markdown-Notizen
2. `.canvas`-Dateien

Beide Ausgaben basieren auf derselben Wahrheitsschicht.
Canvas ist dabei keine freie Handzeichnung, sondern eine automatisch erzeugte Projektion eines kanonischen Artefakt-Graphen.

**Datenfluss:**
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

---

## 2. Leitannahme

Canvas wird als Build-Artefakt behandelt.

Das bedeutet:
* reproduzierbar
* überschreibbar
* diffbar
* nicht manuell als Wahrheit gepflegt

Canvas ist damit Renderer, nicht Denkraum.

---

## 3. Architekturentscheidung

Die automatische Canvas-Erzeugung wird auf drei Ebenen aufgebaut:

1. Artefakte
2. Graph-Modell
3. Render-Ausgaben

### 3.1 Artefakte

Quellen sind Heimgewebe-Artefakte aus z. B.:
* chronik
* observatorium
* decisions
* knowledge
* agents

### 3.2 Graph-Modell

Zwischenschicht, in der Knoten und Kanten kanonisch beschrieben werden.

### 3.3 Render-Ausgaben

Aus demselben Graph-Modell werden erzeugt:
* Markdown-Dateien
* `.canvas`-Dateien

Markdown und Canvas sind also zwei Ansichten desselben Erkenntnismaterials.

---

## 4. Zielstruktur im Vault

Alle Ausgaben liegen unter: `vault-gewebe/obsidian-bridge/`

**Erweiterte Struktur:**
```text
obsidian-bridge/
  index/
  chronik/
  observatorium/
  decisions/
  knowledge/
  agents/
  views/
  canvases/
    chronik/
    observatorium/
    decisions/
    knowledge/
    system/
    index/
  meta/
    graph/
    sync/
    diagnostics/
```

**Bedeutung:**
* `canvases/` enthält alle automatisch erzeugten `.canvas`-Dateien.
* `meta/graph/` enthält die kanonischen Zwischenartefakte für Graph und Layout.

---

## 5. Kanonischer Graph-Layer

### 5.1 Zweck

Der Graph-Layer ist die zentrale Wahrheitsschicht für alle Canvas.
Nicht Markdown ist die Quelle, sondern:
**Artefakte + Relationen**

### 5.2 Graph-Artefakt

Ein internes Bridge-Artefakt, z. B.: `graph.v1.json`
mit:
* nodes
* edges
* optional clusters
* optional topics

### 5.3 Knotenmodell

Jeder Knoten repräsentiert ein Artefakt oder Konzept.

**Beispiel:**
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

### 5.4 Kantenmodell

Jede Kante repräsentiert eine explizite Beziehung.

**Beispiel:**
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

## 6. Quellen der Relationen

Relationen werden aus strukturierten Artefakten extrahiert, insbesondere aus:
* chronik-Events
* policy.decision
* decision.preimage
* knowledge.observatory
* contradiction.report
* uncertainty.report

**Typische Relationstypen:**
* references
* causes
* informed
* contradicts
* derives_from
* clusters_with
* precedes
* belongs_to_topic

---

## 7. Canvas-Klassen

Da alle Canvas automatisch erzeugt werden sollen, braucht die Bridge feste Canvas-Klassen.

### 7.1 System-Canvas
**Datei:** `canvases/system/system-architecture.canvas`

**Inhalt:**
* Organe / Repos
* Hauptflüsse
* zentrale Artefaktadern

**Quelle:**
* Repo-Rollenmatrix
* bekannte Artefaktflüsse

### 7.2 Chronik-Canvas
**Dateien:**
* `canvases/chronik/events-latest.canvas`
* `canvases/chronik/events-2026-03.canvas`

**Inhalt:**
* Event-Ketten
* zeitliche Beziehungen
* Event → Insight → Decision

**Quelle:**
* Chronik-Artefakte
* zeitliche Kanten
* abgeleitete Relationen

### 7.3 Observatorium-Canvas
**Dateien:**
* `canvases/observatorium/insight-network.canvas`
* `canvases/observatorium/contradiction-network.canvas`

**Inhalt:**
* Erkenntniscluster
* Widerspruchsnetze
* Unsicherheitszonen

### 7.4 Decision-Canvas
**Dateien:**
* `canvases/decisions/decision-network.canvas`
* `canvases/decisions/decision--2026-03-08--dec-12.canvas`

**Inhalt:**
* Entscheidung
* Preimage
* Referenz-Ereignisse
* Outcomes

### 7.5 Knowledge-Canvas
**Dateien:**
* `canvases/knowledge/concept-network.canvas`
* `canvases/knowledge/entity-network.canvas`

**Inhalt:**
* Konzepte
* Entitäten
* Relationen

### 7.6 Index-Canvas
**Dateien:**
* `canvases/index/root.canvas`
* `canvases/index/latest.canvas`

**Inhalt:**
* Einstieg in alle Haupt-Canvas
* Links auf Sub-Canvas
* Start-Mindmap des Vault-Bereichs

---

## 8. Layout-Strategie

### 8.1 Grundsatz

Layout muss deterministisch sein.
Ein rein physikalisches Force-Layout ist ungeeignet, weil es bei jedem Rebuild Orientierung zerstören kann.

### 8.2 Layout-Typen pro Canvas-Klasse

* **chronik/*** (Timeline-Layout)
  * links → rechts = Zeit
  * oben / unten = Typgruppen
* **decisions/*** (Radial-Layout)
  * Zentrum = Entscheidung
  * innen = Inputs / Preimages
  * außen = Outcomes / Folgen
* **observatorium/*** (Cluster-Layout)
  * Cluster je Thema
  * Cluster je Unsicherheitsfeld
  * Cluster je Widerspruchsgruppe
* **knowledge/*** (Hierarchie-/Graph-Layout)
  * Konzepte oben
  * Entitäten mittig
  * konkrete Artefakte unten
* **system/*** (Organsystem-Layout)
  * Feste Positionen für: chronik, semantAH, hausKI, heimlern, heimgeist, leitstand, wgx, metarepo

---

## 9. Persistente Koordinaten

Layout darf nicht bei jedem Lauf blind neu berechnet werden.

**Stattdessen:**
```text
graph snapshot
    ↓
layout cache
    ↓
canvas render
```

Dafür ein zusätzliches Artefakt, z. B.: `layout.v1.json`
Enthält pro Knoten: `x`, `y`, `width`, `height`

**Regel:**
* bestehende Knoten behalten ihre Position
* neue Knoten werden deterministisch ergänzt
* gelöschte Knoten verschwinden kontrolliert

---

## 10. Interne Canvas-Repräsentation

Vor dem Schreiben der `.canvas`-Datei erzeugt die Bridge ein neutrales Canvas-Modell.

**Beispiel:**
```json
{
  "nodes": [...],
  "edges": [...],
  "viewport": {...}
}
```

### 10.1 Node-Typen
Mindestens:
* **file** → verweist auf Markdown-Datei
* **text** → erklärender Text
* **group** → logischer Clusterbereich

### 10.2 Edge-Typen
* Standardkante mit Relation
* optionale Beschriftung
* optional stilcodiert nach Relationstyp

---

## 11. Canvas-Specs als Build-Input

Um Wildwuchs zu verhindern, wird jede Canvas-Datei durch eine deklarative Spec definiert.

**Beispiel:**
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

**Nutzen:**
* deklarativ
* CI-prüfbar
* erweiterbar
* keine verteilte Logik im Code

---

## 12. Begrenzungsregeln gegen Graph-Spaghetti

Da alle Canvas automatisch erzeugt werden, braucht es harte Guards.

### 12.1 Maximalgrößen
Pro Canvas: `max_nodes`, `max_edges`, `max_depth`, `max_clusters`

### 12.2 Fokusregeln
Nur relevante Relationen rendern:
* stärkste Kanten
* jüngste Artefakte
* priorisierte Relationstypen

### 12.3 Rollup-Regeln
Statt eines Mega-Canvas:
* Monats-Canvas
* Themen-Canvas
* Decision-Canvas
* Insight-Canvas
* Hub-Canvas

---

## 13. Index- und Hub-Canvas

### 13.1 Root-Canvas
**Datei:** `canvases/index/root.canvas`

**Knoten:**
* System
* Chronik
* Observatorium
* Decisions
* Knowledge
* Latest

**Funktion:**
* Start-Mindmap
* zentraler Einstiegspunkt

### 13.2 Topic-Hubs
Automatisch erzeugte Hub-Canvas, z. B.:
* `canvases/index/topic--chronik.canvas`
* `canvases/index/topic--observatorium.canvas`

**Funktion:**
* thematische Navigation
* semantische Verdichtung
* Einstieg in Untergraphen

---

## 14. Renderer-Pipeline

**Gesamtpipeline:**
1. Artefakte lesen
2. Relationen extrahieren
3. Graph-Artefakt bauen
4. Canvas-Specs auswerten
5. Layout berechnen / stabilisieren
6. Markdown rendern
7. Canvas rendern
8. Manifest und Diagnostics aktualisieren

---

## 15. Umsetzung in Phasen

### Phase 1 – Graph-Fundament
**Ziel:**
* Graph-Artefakt definieren
* Relationsextraktion implementieren
* Markdown weiter wie bisher rendern

**Output:** `meta/graph/graph.v1.json`

### Phase 2 – Deterministische Canvas-Renderer
**Ziel:**
* Canvas-Writer implementieren
* Layout-Logik pro Canvas-Klasse
* erste automatische Canvas erzeugen: `system-architecture.canvas`, `events-latest.canvas`, `insight-network.canvas`

### Phase 3 – Spec-System
**Ziel:**
* deklarative Canvas-Specs
* Render-Build über Specs
* CI-Validierung

### Phase 4 – Vollständige Abdeckung
**Ziel:**
* alle definierten Canvas-Klassen erzeugen
* Hub-Canvas
* Topic-Canvas
* Monats-/Rollup-Canvas

---

## 16. Repositoriumserweiterungen

**Neue Contracts:**
```text
contracts/
  graph.v1.json
  canvas-spec.v1.json
  layout.v1.json
```

**Neue Skriptpfade:**
```text
scripts/
  graph/
    build_graph.py
    extract_relations.py
    stabilize_layout.py
  canvas/
    render_canvas.py
    render_all_canvases.py
```

**Konfiguration:**
```text
config/
  canvas-specs/
    system.yaml
    chronik-latest.yaml
    observatorium-insights.yaml
    decisions-network.yaml
```

**Tests:**
```text
tests/
  test_graph_build.py
  test_canvas_render.py
  test_layout_stability.py
  fixtures/
    graph/
    canvas/
```

---

## 17. Prämissencheck

Damit diese Architektur sinnvoll ist, müssen drei Bedingungen gelten:

### 17.1 Relationen sind ausreichend formalisierbar
Wenn Beziehungen nur implizit oder literarisch vorhanden sind, bleibt der Graph schwach.

### 17.2 Canvas wird als Build-Artefakt akzeptiert
Es darf keine manuelle Wahrheitspflege in `.canvas` geben.

### 17.3 Layout-Stabilität ist wichtiger als Schönheit
Orientierung schlägt visuelle Spielerei.

---

## 18. Alternativpfad

Falls sich zeigt, dass die Relationen noch zu schwach formalisiert sind:
```text
erst Graphqualität erhöhen
       ↓
danach vollständige Canvas-Erzeugung
```
Die Reihenfolge bleibt also: **Graph zuerst, Canvas danach**

---

## 19. Risiko-/Nutzenabschätzung

**Nutzen:**
* vollständige visuelle Wissensoberfläche
* mehrdimensionale Mindmaps aus Systemwissen
* keine manuelle Canvas-Pflege
* konsistenter Wissensgraph
* Obsidian wird semantischer Spiegel des Heimgewebes

**Risiken:**
* Graph-Spaghetti
* Layout-Drift
* zu schwache Relationen
* hoher initialer Implementierungsaufwand
* Gefahr dekorativer statt nützlicher Graphen

**Gegenmaßnahmen:**
* Canvas-Specs
* Layout-Cache
* Größenlimits
* Fokusregeln
* Rollups statt Vollgraphen

---

## 20. Empfehlung

Die automatische Erzeugung aller Canvas ist sinnvoll und realisierbar, wenn sie als deterministische Graph-Projektion gebaut wird.

**Empfohlene Reihenfolge:**
`Artefakte → Graph-Layer → Canvas-Specs → deterministische Renderer → vollständige Auto-Canvas-Erzeugung`

---

## 21. Essenz

Die Obsidian-Bridge soll künftig nicht nur Markdown rendern, sondern den kanonischen Graph des Heimgewebes in `.canvas` übersetzen.

Dafür braucht es:
* einen Graph-Layer als Wahrheit
* deklarative Canvas-Specs
* stabile Layout-Strategien
* automatische Renderer

Dann kann die Bridge tatsächlich alle Canvas selbst erzeugen, ohne in visuelle Beliebigkeit oder chaotische Schönfärberei abzugleiten.
