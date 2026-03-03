#!/usr/bin/env bats

setup() {
  export PATH="$(pwd)/bin:$PATH"

  # Setup temp directory for testing `obsidian-env` config override
  export TEMP_CONFIG_DIR="$(mktemp -d)"
  export OBSIDIAN_CONFIG_DIR="$TEMP_CONFIG_DIR"

  # Create a profile structure similar to repo root
  mkdir -p "$TEMP_CONFIG_DIR/profiles"
  cat << 'EOF' > "$TEMP_CONFIG_DIR/profiles/ci.env"
# CI profile test settings
VAULT_NAME="test-vault"
VAULT_PATH="/tmp/test-vault-path"
EOF

  export OBSIDIAN_PROFILE="ci"
}

teardown() {
  rm -rf "$TEMP_CONFIG_DIR"
}

@test "obsidian-json is executable and responds" {
  # It should complain about missing JSON/stdin instead of command not found
  run obsidian-json
  [ "$status" -ne 127 ]
}

@test "obsidian-env --print outputs valid export commands" {
  run obsidian-env --print
  [ "$status" -eq 0 ]

  # Check if VAULT_NAME export is present
  [[ "$output" =~ export\ VAULT_NAME=test-vault ]]

  # Check if VAULT_PATH export is present
  [[ "$output" =~ export\ VAULT_PATH=/tmp/test-vault-path ]]
}

@test "obsidian-doctor checks pass or warn correctly in headless mode" {
  run obsidian-doctor

  # The doctor might fail if obsidian flatpak isn't found in CI, which is expected.
  # But we just want to ensure it runs without syntax/runtime errors (exit 0 or 1).
  [ "$status" -eq 0 ] || [ "$status" -eq 1 ]

  # It should at least mention running diagnostics
  [[ "$output" =~ "Running Obsidian Doctor diagnostics" ]]
}
