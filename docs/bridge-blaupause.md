# Blaupause: Obsidian-Bridge im Heimgewebe (inkl. Canvas-Ebene)

## 1. Ziel

Die Obsidian-Bridge stellt eine epistemische Oberfläche für Heimgewebe-Artefakte bereit.
Die Obsidian-Bridge übersetzt Heimgewebe-Artefakte in strukturierte Markdown-Notizen und generiert automatisch Canvas-Modelle zur visuellen Exploration des zugrunde liegenden Artefakt-Graphen.
Die Bridge erzeugt keine Wahrheitsschicht, sondern einen explorativen Wissensraum.

**Datenfluss:**
`Heimgewebe → obsidian-bridge → Obsidian Vault`

**Keine automatische Rückkopplung:**
`Obsidian Vault ↛ Heimgewebe`

---

## 2. Rolle im System

| Ebene | Funktion |
| :--- | :--- |
| **Heimgewebe** | Artefakte erzeugen |
| **Leitstand** | Systemzustand darstellen |
| **Obsidian-Bridge** | Artefakte in Wissensraum überführen |
| **Obsidian** | semantische Exploration |

* **Leitstand** ist operativ.
* **Obsidian** ist epistemisch.

---

## 3. Vault-Struktur

Alle Inhalte liegen unter: `vault-gewebe/obsidian-bridge/`

**Struktur:**
```text
obsidian-bridge/
  index/
  chronik/
  observatorium/
  decisions/
  knowledge/
  agents/
  scratch/
  views/
  canvases/
  meta/
```

---

## 4. index/

Einstiegspunkt in den Wissensraum.

```text
index/
  start.md
  navigation.md
  latest.md
```

**Funktion:**
* Übersicht über aktuelle Artefakte
* Navigation in zentrale Bereiche
* Einstieg für Exploration

---

## 5. chronik/

Zeitliche Systemgeschichte.

```text
chronik/
  events/
    YEAR/
      MONTH/
        event--<date>--<id>.md
  timelines/
    weekly.md
    monthly.md
  rollups/
    system-history.md
```

**Funktion:**
* chronologische Rekonstruktion
* Systemhistorie
* zeitliche Muster

---

## 6. observatorium/

Analytische Ebene.

```text
observatorium/
  insights/
  contradictions/
  uncertainty/
  daily/
```

**Artefakte:**
* Erkenntnisse
* Widerspruchsberichte
* Unsicherheitsanalysen
* tägliche Systembeobachtungen

---

## 7. decisions/

Entscheidungsarchiv.

```text
decisions/
  policy/
  preimages/
  outcomes/
```

**Diese Struktur ermöglicht:**
* Entscheidungsrekonstruktion
* Alternativenanalyse
* Folgenbeobachtung

---

## 8. knowledge/

Stabile Wissensstruktur.

```text
knowledge/
  entities/
  concepts/
  relations/
  snapshots/
```

**Zweck:**
* langfristige Wissensobjekte
* semantische Systembeschreibung
* strukturelle Zusammenhänge

---

## 9. agents/

Agentische Aktivitäten.

```text
agents/
  runs/
  prompts/
  reviews/
```

**Zweck:**
* Transparenz automatisierter Prozesse
* Nachvollziehbarkeit von Agententscheidungen

---

## 10. scratch/

Freier Denkraum.

```text
scratch/
  hypotheses/
  analyses/
  maps/
```

**Eigenschaften:**
* manuell
* experimentell
* nicht automatisch synchronisiert

---

## 11. views/

Kuratiertes Lesen.

```text
views/
  dashboards/
  clusters/
  narratives/
```

**Funktion:**
* thematische Perspektiven
* Synthese-Seiten
* langfristige Interpretationen

---

## 12. meta/

Dieser Ordner enthält Metadaten der Obsidian-Bridge selbst (z. B. Synchronisationsstatus oder Export-Manifeste).
Er gehört nicht zum epistemischen Wissensraum, sondern zur technischen Infrastruktur der Bridge.

```text
meta/
  sync/
  manifests/
  exports/
  diagnostics/
```

**Inhalt:**
* Synchronisationsstatus
* Export-Manifeste
* Diagnosedaten
* technische Bridge-Metadaten

---

## 13. canvases/

Mehrdimensionale Wissensmodelle.

```text
canvases/
  system/
  decisions/
  observatorium/
  investigations/
```

**Dateiformat:**
`*.canvas`

Canvas-Dateien stellen graphische Wissensmodelle dar.

---

## 14. Rolle von Canvas

Markdown bildet lineare Wissensrepräsentation.
Canvas ergänzt dies durch graphische Wissensräume.

**Canvas ermöglicht:**
* multidimensionale Mindmaps
* visuelle Argumentationsketten
* explorative Strukturmodelle
* semantische Netzwerke

---

## 15. Canvas-Typen

### System-Maps
`canvases/system/system-architecture.canvas`

**Visualisiert:**
* Heimgewebe-Organe
* Artefaktflüsse
* Systemstruktur

### Entscheidungs-Maps
`canvases/decisions/decision--2026-03-08--dec-12.canvas`

**Visualisiert:**
* Kontext
* Alternativen
* Konsequenzen
* beteiligte Artefakte

### Observatorium-Maps
`canvases/observatorium/insight-network.canvas`

**Visualisiert:**
* Erkenntniscluster
* Widerspruchsnetze
* Unsicherheitsbereiche

### Investigation-Maps
`canvases/investigations/topic-analysis.canvas`

Dienen der explorativen Analyse.

**Beispiel:**
* Ereignisketten
* Hypothesenräume
* Ursache-Wirkungs-Netze

---

## 16. Canvas-Strukturprinzip

Canvas-Knoten verlinken direkt auf Artefaktseiten.

**Beispiel:**
```text
node → [[chronik/events/2026/03/event--2026-03-08--evt-123]]
node → [[decisions/policy/decision--2026-03-08--dec-12]]
node → [[observatorium/insights/insight--2026-03-08--ins-44]]
```

Dadurch entsteht ein mehrdimensionaler Wissensgraph.

---

## 17. Artefakt-Rendering

Markdown-Notizen und Canvas-Modelle werden aus denselben Heimgewebe-Artefakten erzeugt; die Canvas-Generierung basiert dabei auf dem zugrunde liegenden Artefakt-Graphen.

**Pipeline (Markdown):**
`artifact → renderer → markdown note`

**Exportierte Artefakte:**
* Chronik-Events
* Observatorium-Erkenntnisse
* Widerspruchsberichte
* Entscheidungen
* Wissensartefakte

Canvas-Modelle werden automatisch generiert, um eine visuelle Exploration zu ermöglichen.

---

## 18. Dateinamen-Schema

**Empfohlen:**
`<artifact-type>--<date>--<id>.md`

**Beispiele:**
* `event--2026-03-08--evt-123.md`
* `insight--2026-03-08--ins-44.md`
* `decision--2026-03-08--dec-12.md`

---

## 19. Frontmatter

Jede generierte Notiz enthält Metadaten.

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

---

## 20. Synchronisationsprinzip

Die Bridge arbeitet deterministisch.

**Eigenschaften:**
* read-only
* idempotent
* artifact-driven

Vault-Aktualisierungen verändern keine bestehenden Inhalte inkonsistent.

---

## 21. Erweiterbarkeit

Neue Wissensebenen können ergänzt werden.

**Beispiele:**
* `observatorium/models/`
* `knowledge/ontologies/`
* `canvases/strategy/`

Die Struktur bleibt stabil.

---

## 22. Essenz

Die Obsidian-Bridge erzeugt einen explorativen Wissensraum über Heimgewebe-Artefakte.

* **Markdown** bildet lineare Wissensseiten.
* **Canvas** ergänzt mehrdimensionale Wissensnetze.

**Leitstand** zeigt, was im System geschieht.
**Obsidian** ermöglicht zu verstehen, wie Ereignisse, Erkenntnisse und Entscheidungen zusammenhängen.

Beide Interfaces bilden gemeinsam die vollständige kognitive Oberfläche des Heimgewebe-Systems.
