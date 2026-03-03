#!/usr/bin/env bats

setup() {
  export PATH="$(pwd)/bin:$PATH"
  export FIXTURE_DIR="$(pwd)/tests/fixtures"
  export FAKE_OBSIDIAN="$(pwd)/bin/obsidian"

  export FIXTURE_OBJ="$FIXTURE_DIR/noisy_cli_output.txt"
  export FIXTURE_ARR="$FIXTURE_DIR/noisy_cli_array.txt"

  mkdir -p "$FIXTURE_DIR"

  cat << 'EOF' > "$FIXTURE_OBJ"
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

  cat << 'EOF' > "$FIXTURE_ARR"
Loading vault...
[
  {
    "id": 1,
    "name": "daily"
  },
  {
    "id": 2,
    "name": "work"
  }
]
Vault loaded successfully.
EOF

  # Create a fake obsidian executable to simulate noisy output
  cat << 'EOF' > "$FAKE_OBSIDIAN"
#!/usr/bin/env bash
if [ "$1" = "obj" ]; then
    cat "$FIXTURE_OBJ"
elif [ "$1" = "arr" ]; then
    cat "$FIXTURE_ARR"
fi
EOF
  chmod +x "$FAKE_OBSIDIAN"
}

teardown() {
  rm -rf "$FIXTURE_DIR"
  rm -f "$FAKE_OBSIDIAN"
}

@test "obsidian-json extracts JSON object from noisy output" {
  run obsidian-json obj
  [ "$status" -eq 0 ]

  result=$(echo "$output" | jq -r '.search')
  [ "$result" = "test query" ]
}

@test "obsidian-json extracts JSON array from noisy output" {
  run obsidian-json arr
  [ "$status" -eq 0 ]

  result=$(echo "$output" | jq -r '.[1].name')
  [ "$result" = "work" ]
}
