# Troubleshooting & Operations

## `obsidian-json`
**Why it exists:** When interacting with the Obsidian CLI (especially via plugins), the standard output often contains noisy messages (like GTK or DBus warnings, legacy extension notices, etc.). `obsidian-json` strips this noise out deterministically and extracts only the relevant JSON payload (whether formatted as an object `{...}` or an array `[...]`).

**Usage:** Use it exactly like the `obsidian` binary:
```bash
obsidian-json vault="vault-gewebe" search "query" format=json
```

## `obsidian-clean`
**Why it exists:** Similar to `obsidian-json`, but for human-readable outputs. It redirects `stderr` (which contains most UI noise and warnings) directly into a daily log file, leaving `stdout` perfectly clean for the console or a pipeline.

**Where do the logs go?**
By default, logs are written to `$HOME/logs/obsidian-cli/obsidian-stderr-YYYY-MM-DD.log`. You can override this by setting the `OBSIDIAN_LOG_FILE` environment variable.

**Usage:** Use it exactly like the `obsidian` binary:
```bash
obsidian-clean vault="vault-gewebe" search "my query"
```
