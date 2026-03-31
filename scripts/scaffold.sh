#!/bin/sh
set -eu

usage() {
  cat <<'EOF'
Usage:
  scaffold.sh <minimal|default> <target-repo> [--force]

Examples:
  scaffold.sh minimal /path/to/repo
  scaffold.sh default /path/to/repo
  scaffold.sh default /path/to/repo --force
EOF
}

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
  usage
  exit 1
fi

PROFILE=$1
TARGET=$2
FORCE=${3-}

if [ ! -d "$TARGET" ]; then
  echo "Target repository does not exist: $TARGET" >&2
  exit 1
fi

if [ -n "$FORCE" ] && [ "$FORCE" != "--force" ]; then
  echo "Unknown option: $FORCE" >&2
  usage
  exit 1
fi

KIT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
COPY_PLAN=$(mktemp)
trap 'rm -f "$COPY_PLAN"' EXIT HUP INT TERM

add_copy() {
  printf '%s\t%s\n' "$1" "$2" >> "$COPY_PLAN"
}

plan_profile() {
  add_copy "$KIT_ROOT/templates/repo/AGENTS.md" "$TARGET/AGENTS.md"
  add_copy "$KIT_ROOT/templates/repo/docs/verification-plan.md" "$TARGET/docs/verification-plan.md"
  add_copy "$KIT_ROOT/templates/repo/docs/tasks/README.md" "$TARGET/docs/tasks/README.md"

  case "$PROFILE" in
    minimal)
      ;;
    default)
      add_copy "$KIT_ROOT/templates/repo/docs/escalation-rules.md" "$TARGET/docs/escalation-rules.md"
      ;;
    *)
      echo "Unknown profile: $PROFILE" >&2
      usage
      exit 1
      ;;
  esac
}

preflight() {
  failed=0
  while IFS='	' read -r src dest; do
    if [ -e "$dest" ] && [ "$FORCE" != "--force" ]; then
      echo "Refusing to overwrite existing file: $dest" >&2
      failed=1
    fi
  done < "$COPY_PLAN"

  if [ "$failed" -ne 0 ]; then
    echo "No files were copied. Re-run with --force to overwrite." >&2
    exit 1
  fi
}

apply_plan() {
  while IFS='	' read -r src dest; do
    mkdir -p "$(dirname "$dest")"
    cp "$src" "$dest"
    echo "copied $src -> $dest"
  done < "$COPY_PLAN"
}

plan_profile
preflight
apply_plan
