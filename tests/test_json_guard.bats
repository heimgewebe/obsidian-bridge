#!/usr/bin/env bats

setup() {
  export FIXTURE_DIR="$(pwd)/tests/fixtures"
  export FAKE_OBSIDIAN="$(pwd)/tests/helpers/fake-obsidian.sh"
  export FAKE_BIN="$(pwd)/tests/helpers/bin"

  # Temporarily override PATH to prioritize our fake obsidian
  export PATH="$FAKE_BIN:$(pwd)/bin:$PATH"

  export FIXTURE_OBJ="$FIXTURE_DIR/noisy_cli_output.txt"
  export FIXTURE_ARR="$FIXTURE_DIR/noisy_cli_array.txt"

  mkdir -p "$FIXTURE_DIR"
  mkdir -p "$FAKE_BIN"

  # Create fixture: object
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

  # Create fixture: array
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

  # Symlink it into a fake bin directory we placed in the PATH
  ln -s "$FAKE_OBSIDIAN" "$FAKE_BIN/obsidian"
}

teardown() {
  rm -rf "$FIXTURE_DIR"
  rm -rf "$(pwd)/tests/helpers"
}

@test "obsidian-json extracts JSON object from noisy output (stdin)" {
  run bash -c "cat $FIXTURE_OBJ | obsidian-json"
  [ "$status" -eq 0 ]

  result=$(echo "$output" | jq -r '.search')
  [ "$result" = "test query" ]
}

@test "obsidian-json extracts JSON array from noisy output (stdin)" {
  run bash -c "cat $FIXTURE_ARR | obsidian-json"
  [ "$status" -eq 0 ]

  result=$(echo "$output" | jq -r '.[1].name')
  [ "$result" = "work" ]
}

@test "obsidian-json clarifies jq parse failures with invalid JSON" {
  run bash -c "echo '{ nope }' | obsidian-json 2>&1"
  [ "$status" -eq 1 ]
  [[ "$output" =~ "Error: Extracted JSON failed to parse (jq exit" ]]
  [[ ! "$output" =~ "parse error:" ]]
}

@test "obsidian-json debug mode preserves jq diagnostics" {
  run bash -c "echo '{ nope }' | OBSIDIAN_JSON_DEBUG=1 obsidian-json 2>&1"
  [ "$status" -eq 1 ]
  [[ "$output" =~ "Error: Extracted JSON failed to parse (jq exit" ]]
  [[ "$output" =~ "parse error" ]]
}

@test "obsidian-json fails with non-zero exit code if no JSON is found" {
  run bash -c "echo 'Just some random text without json' | obsidian-json"
  [ "$status" -eq 1 ]
  [[ "$output" =~ "Error: No valid JSON object or array found in output." ]]
}

@test "obsidian-json extracts JSON object from noisy output (wrapper args)" {
  # Call obsidian-json with arguments, simulating obsidian obj
  run obsidian-json obj
  [ "$status" -eq 0 ]

  result=$(echo "$output" | jq -r '.search')
  [ "$result" = "test query" ]
}

@test "obsidian-json extracts JSON array from noisy output (wrapper args)" {
  # Call obsidian-json with arguments, simulating obsidian arr
  run obsidian-json arr
  [ "$status" -eq 0 ]

  result=$(echo "$output" | jq -r '.[1].name')
  [ "$result" = "work" ]
}
