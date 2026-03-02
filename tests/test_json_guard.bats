#!/usr/bin/env bats

setup() {
  export PATH="$(pwd)/bin:$PATH"
  export FIXTURE_FILE="$(pwd)/tests/fixtures/noisy_cli_output.txt"

  cat << 'EOF' > "$FIXTURE_FILE"
Gtk-Message: 12:04:32.411: Failed to load module "canberra-gtk-module"
Warning: obsidian loaded a legacy extension

{
  "search": "test query",
  "results": [
    {
      "path": "test.md",
      "score": 0.95
    }
  ]
}

[OBSIDIAN_LOG] Finished search with 1 results
EOF
}

teardown() {
  rm -f "$FIXTURE_FILE"
}

@test "obsidian-json successfully extracts JSON from noisy output" {
  run bash -c "cat $FIXTURE_FILE | obsidian-json"
  [ "$status" -eq 0 ]

  # Validate JSON structure matches
  result=$(echo "$output" | jq -r '.search')
  [ "$result" = "test query" ]
}
