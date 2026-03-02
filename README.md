# Zielbild des Repos obsidian

Mission: Obsidian als UI-Schicht für maschinelle Artefakte betreiben (Observatorium), mit deterministischen CLI-Schnittstellen und reproduzierbarem Betrieb.

## Prinzipien

- **Output-Klassen trennen:** human vs machine (obsidian-clean vs obsidian-json)
- **Idempotent:** alles mehrfach ausführbar ohne Nebenwirkungen
- **Keine Vault-Daten im Repo:** nur Tools + Doku + Schemas
- **Tests statt Hoffnung:** minimal, aber vorhanden

## Was ist „intelligent“ daran?

### 1) bin/ als stabile API
Alles, was andere Tools aufrufen, liegt in bin/:
- `obsidian-clean` (stderr → log)
- `obsidian-json` (JSON-Extraktor)
- `obsidian-env` (liest config, setzt VAULT/VAULT_PATH)
- `obsidian-doctor` (Diagnose: Flatpak, D-Bus, PATH, CLI enabled)

Damit ist das Repo nicht „Skript-Sammlung“, sondern Command Surface.

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
Minimal, aber gezielt:
- Smoke: create/read/append/prepend im Test-Vault
- JSON guard: noisy output → extrahiertes JSON parsebar
- Repo-Scope: harte Regeln (damit es nicht kippt)

## Verboten
- Vault-Content committen
- persönliche Notizen
- Attachments

## Erlaubt
- Doku über Struktur/Operation
- Schemas/Contracts
- generierte Beispiele unter docs/examples/ (synthetisch)
