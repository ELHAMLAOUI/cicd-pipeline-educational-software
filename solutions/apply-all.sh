#!/usr/bin/env bash
# Démarre chaque lab et applique sa solution de référence (démonstration / auto-test).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WS="${PIPECTL_WORKSPACE_ROOT:-$ROOT/workspace}"
for n in 01 02 03 04 05 06; do
  rm -rf "$WS/lab$n"
  "$ROOT/pipectl" start "$n" >/dev/null
  (cd "$WS/lab$n" && bash "$ROOT/solutions/lab$n.sh" >/dev/null 2>&1)
done
