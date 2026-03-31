#!/bin/sh
set -eu

usage() {
  cat <<'EOF'
Usage:
  new-task.sh <general|web|backend|research|dependency> <target-repo> <task-slug> [flags]

Flags:
  --with-plan
  --with-review
  --with-qa
  --with-roles
  --with-topology
  --with-loop-contract
  --only-missing
  --force

Examples:
  new-task.sh general /path/to/repo feature-x
  new-task.sh web /path/to/repo checkout-redesign --with-plan
  new-task.sh general /path/to/repo feature-x --with-plan --only-missing
  new-task.sh general /path/to/repo migration-audit --with-roles --with-topology
EOF
}

if [ "$#" -lt 3 ]; then
  usage
  exit 1
fi

PROFILE=$1
TARGET=$2
TASK_SLUG=$3
shift 3

if [ ! -d "$TARGET" ]; then
  echo "Target repository does not exist: $TARGET" >&2
  exit 1
fi

case "$TASK_SLUG" in
  ""|/*|*..*)
    echo "Unsafe task slug: $TASK_SLUG" >&2
    exit 1
    ;;
esac

FORCE=
WITH_PLAN=0
WITH_REVIEW=0
WITH_QA=0
WITH_ROLES=0
WITH_TOPOLOGY=0
WITH_LOOP=0
ONLY_MISSING=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --with-plan)
      WITH_PLAN=1
      ;;
    --with-review)
      WITH_REVIEW=1
      ;;
    --with-qa)
      WITH_QA=1
      ;;
    --with-roles)
      WITH_ROLES=1
      ;;
    --with-topology)
      WITH_TOPOLOGY=1
      ;;
    --with-loop-contract)
      WITH_LOOP=1
      ;;
    --only-missing)
      ONLY_MISSING=1
      ;;
    --force)
      FORCE=--force
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

case "$PROFILE" in
  general)
    ;;
  web)
    WITH_REVIEW=1
    WITH_QA=1
    ;;
  backend)
    WITH_REVIEW=1
    ;;
  research)
    WITH_REVIEW=1
    ;;
  dependency)
    WITH_PLAN=1
    WITH_REVIEW=1
    ;;
  *)
    echo "Unknown profile: $PROFILE" >&2
    usage
    exit 1
    ;;
esac

KIT_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
TASK_DIR="$TARGET/docs/tasks/$TASK_SLUG"
COPY_PLAN=$(mktemp)
EFFECTIVE_PLAN=$(mktemp)
trap 'rm -f "$COPY_PLAN" "$EFFECTIVE_PLAN"' EXIT HUP INT TERM

add_copy() {
  printf '%s\t%s\n' "$1" "$2" >> "$COPY_PLAN"
}

plan_task() {
  add_copy "$KIT_ROOT/templates/task/contract.md" "$TASK_DIR/contract.md"
  add_copy "$KIT_ROOT/templates/task/handoff.md" "$TASK_DIR/handoff.md"

  if [ "$WITH_PLAN" -eq 1 ]; then
    add_copy "$KIT_ROOT/templates/task/plan.md" "$TASK_DIR/plan.md"
  fi
  if [ "$WITH_REVIEW" -eq 1 ]; then
    add_copy "$KIT_ROOT/templates/task/review.md" "$TASK_DIR/review.md"
  fi
  if [ "$WITH_QA" -eq 1 ]; then
    add_copy "$KIT_ROOT/templates/task/qa.md" "$TASK_DIR/qa.md"
  fi
  if [ "$WITH_ROLES" -eq 1 ]; then
    add_copy "$KIT_ROOT/templates/task/roles.md" "$TASK_DIR/roles.md"
  fi
  if [ "$WITH_TOPOLOGY" -eq 1 ]; then
    add_copy "$KIT_ROOT/templates/task/topology.md" "$TASK_DIR/topology.md"
  fi
  if [ "$WITH_LOOP" -eq 1 ]; then
    add_copy "$KIT_ROOT/templates/task/loop_contract.md" "$TASK_DIR/loop_contract.md"
  fi
}

preflight() {
  failed=0
  while IFS='	' read -r src dest; do
    if [ -e "$dest" ] && [ "$FORCE" != "--force" ]; then
      if [ "$ONLY_MISSING" -eq 1 ]; then
        echo "skipping existing file: $dest"
      else
        echo "Refusing to overwrite existing file: $dest" >&2
        failed=1
      fi
    else
      printf '%s\t%s\n' "$src" "$dest" >> "$EFFECTIVE_PLAN"
    fi
  done < "$COPY_PLAN"

  if [ "$failed" -ne 0 ]; then
    echo "No files were copied. Re-run with --force to overwrite." >&2
    exit 1
  fi
}

apply_plan() {
  if [ ! -s "$EFFECTIVE_PLAN" ]; then
    echo "No missing files to copy."
    exit 0
  fi

  while IFS='	' read -r src dest; do
    mkdir -p "$(dirname "$dest")"
    cp "$src" "$dest"
    echo "copied $src -> $dest"
  done < "$EFFECTIVE_PLAN"
}

plan_task
preflight
apply_plan
