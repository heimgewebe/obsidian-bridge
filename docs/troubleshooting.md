# Troubleshooting & Operations

## `obsidian-json`
**Why it exists:** When interacting with the Obsidian CLI (especially via plugins), the standard output often contains noisy messages (like GTK or DBus warnings, legacy extension notices, etc.). `obsidian-json` strips this noise out deterministically and extracts only the relevant JSON payload (whether formatted as an object `{...}` or an array `[...]`). It works by counting braces to determine the depth of the JSON structure.

**Extraction Limits & Debugging:**
- **Standard Behavior:** `jq` error output is suppressed by default to prevent leaking it into pipelines.
- **Debug Mode:** If you need to see `jq` diagnostics (e.g. for a parse error), you can set `OBSIDIAN_JSON_DEBUG=1`.
- **Edge Cases:** Because `obsidian-json` relies on simple brace-counting (`{`, `[`), stray brace characters in the noisy output outside of the actual JSON payload might occasionally confuse the depth calculation.

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
