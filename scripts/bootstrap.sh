#!/usr/bin/env bash
# bootstrap.sh
# Idempotently sets up the local environment (e.g., config profiles)

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
REPO_ROOT=$(pwd)

echo "Bootstrapping obsidian-bridge repo..."

# Create necessary directories
mkdir -p "$REPO_ROOT/config/profiles"
mkdir -p "$REPO_ROOT/vault"

# Ensure environment profile structure
if [ ! -f "$REPO_ROOT/config/obsidian-bridge.env.example" ]; then
  cat << 'EOF' > "$REPO_ROOT/config/obsidian-bridge.env.example"
# Base settings for obsidian scripts
VAULT_PATH="$HOME/Documents/Obsidian"
OBSIDIAN_LOG_FILE="/tmp/obsidian-bridge.log"
EOF
fi

if [ ! -f "$REPO_ROOT/config/profiles/home.env" ]; then
  cp "$REPO_ROOT/config/obsidian-bridge.env.example" "$REPO_ROOT/config/profiles/home.env"
  echo "Created home profile: config/profiles/home.env"
fi

if [ ! -f "$REPO_ROOT/config/profiles/work.env" ]; then
  cp "$REPO_ROOT/config/obsidian-bridge.env.example" "$REPO_ROOT/config/profiles/work.env"
  echo "Created work profile: config/profiles/work.env"
fi

echo "Checking dependencies..."
for cmd in jq awk bats shellcheck flatpak; do
  if command -v "$cmd" &> /dev/null; then
    echo "  [OK] $cmd"
  else
    echo "  [WARN] $cmd is missing."
  fi
done

echo "Bootstrap complete."