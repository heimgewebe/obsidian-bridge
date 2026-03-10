# Zielbild des Repos obsidian-bridge

Mission: Obsidian als UI-Schicht für maschinelle Artefakte betreiben (Observatorium), mit deterministischen CLI-Schnittstellen und reproduzierbarem Betrieb.

## Prinzipien

- **Output-Klassen trennen:** human vs machine (obsidian-clean vs obsidian-json)
- **Idempotent:** alles mehrfach ausführbar ohne Nebenwirkungen
- **Keine Vault-Daten im Repo:** nur Tools + Doku + Schemas
- **Tests statt Hoffnung:** minimal, aber vorhanden

## Aktueller Umfang

Das Repository stellt vier Kernwerkzeuge unter `bin/` als stabile Schnittstelle bereit:
- `obsidian-clean`: Leitet den gesamten `stderr`-Müll der Obsidian-Ausgabe in ein tägliches Logfile um.
- `obsidian-json`: Extrahiert deterministisch gültiges JSON aus sonstiger CLI-Geräuschkulisse.
- `obsidian-env`: Lädt das korrekte Obsidian-Profil und stellt Umgebungsvariablen bereit.
- `obsidian-doctor`: Prüft unaufgeregt, ob alle nötigen Befehle (wie `jq`, `awk`, Obsidian) im Pfad existieren.

## Was ist „intelligent“ daran?

### 1) bin/ als v1 Command Surface (minimal, kompatibel gehalten)
Alles, was andere Tools aufrufen, liegt in `bin/` und verändert sich in seinen Contracts nicht leichtfertig. Damit ist das Repo nicht „Skript-Sammlung“, sondern eine verlässliche Brücke.

**Contract für `obsidian-json`:**
- **`stdout`:** Liefert ausschließlich gültiges JSON.
- **`stderr`:** Liefert bei Fehlern in der JSON-Extraktion deterministische Meldungen:
  - `"Error: No valid JSON object or array found in output."`
  - `"Error: Extracted JSON failed to parse (jq exit X)."`

  *Hinweis (Wrapper-Modus):* Wenn `obsidian-json` über Wrapper wie `obsidian-clean` oder `obsidian` aufgerufen wird und diese selbst fehlschlagen (z.B. fehlende Executables), können zusätzliche Fehlermeldungen dieser Befehle auf stderr erscheinen. Diese werden unverändert durchgereicht.
- **Exit Codes:** Beendet sich mit `1` im Fehlerfall, sonst `0`.
- **Debug-Modus:** Durch Setzen von `OBSIDIAN_JSON_DEBUG=1` werden die nativen (und sonst unterdrückten) `jq`-Parse-Fehler zusätzlich ausgegeben.

### 2) contracts/ als Wahrheitsschicht
Wir standardisieren Artefakte, z.B.:
- Search-Ergebnis (Liste + Metadaten)
- Daily Insights Stub

So kannst du später heimgeist/leitstand sauber anbinden.

### 3) scripts/ getrennt nach Domänen
- `observatorium/*` schreibt Artefakte in Vault
- `daily/*` macht Tageslogik
- `util/*` ist Infrastruktur

### 4) systemd/user/ für Betrieb
User-Timer sind sauberer als Cron im Desktop-Kontext.

### 5) Tests als Guardrail
Zur Nutzung der Generierungs-Skripte wird Python 3 und das Paket `PyYAML` benötigt.
Eine Installation der Abhängigkeiten erfolgt per `make install-deps` oder automatisch via `make install`.
Die Python-Skripte sollten idealerweise als Modul aus dem Repo-Root aufgerufen werden (z.B. `python3 -m scripts.canvas.render_all_canvases`).

Derzeit implementiert:
- Smoke: Basic CLI Executability (headless-safe)
- JSON guard: noisy output → extrahiertes JSON parsebar (sowohl Array als auch Object)

Geplant:
- Smoke: create/read/append/prepend im Test-Vault
- Repo-Scope: harte Regeln (damit es nicht kippt)

## Verboten
- Vault-Content committen
- persönliche Notizen
- Attachments

## Erlaubt
- Doku über Struktur/Operation
- Schemas/Contracts
- generierte Beispiele unter docs/examples/ (synthetisch)
