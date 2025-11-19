#!/usr/bin/env bash
# Tests de bout en bout du simulateur (vrais dépôts Git, vrais hooks, vrais pipelines).
#  - « départ »    : sans travail de l'étudiant, chaque lab vaut 0 point (aucun point gratuit) ;
#  - « solutions » : les solutions de référence obtiennent 20/20 à chaque lab ;
#  - « erreurs »   : des erreurs et tricheries typiques sont détectées (note < 20).
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
export NO_COLOR=1 PIPECTL="$ROOT/pipectl"
git config --global user.email >/dev/null 2>&1 || export GIT_AUTHOR_NAME=CI GIT_AUTHOR_EMAIL=ci@example.com \
  GIT_COMMITTER_NAME=CI GIT_COMMITTER_EMAIL=ci@example.com

# Solutions : dossier local, sinon branche « solutions » du dépôt.
if [ -d "$ROOT/solutions" ]; then SOL="$ROOT/solutions"; else
  git -C "$ROOT" fetch -q --depth=1 origin solutions 2>/dev/null
  git -C "$ROOT" archive FETCH_HEAD solutions 2>/dev/null | tar -x -C "$TMP" || { echo "Branche solutions inaccessible" >&2; exit 1; }
  SOL="$TMP/solutions"
fi

fail=0
note() { grep "^$1;" "$2/rapport.csv" | cut -d';' -f5; }
scenario() { # scenario NOM SCRIPT_DIR
  local name=$1 dir=$2
  export PIPECTL_WORKSPACE_ROOT="$TMP/ws-$name" RESULTS_DIR="$TMP/res-$name"
  for n in 01 02 03 04 05 06; do
    "$ROOT/pipectl" start "$n" >/dev/null 2>&1 || { echo "FAIL start $n"; fail=1; }
    if [ -n "$dir" ]; then
      (cd "$PIPECTL_WORKSPACE_ROOT/lab$n" && bash "$dir/lab$n.sh" >/dev/null 2>&1)
    fi
  done
  "$ROOT/pipectl" report >"$TMP/$name.log" 2>&1
}

scenario depart ""
for n in 01 02 03 04 05 06; do
  v=$(note "$n" "$TMP/res-depart")
  if [ "$v" = "0.0" ]; then echo "OK   départ     lab $n : 0 point"; else echo "FAIL départ     lab $n : $v/20 gratuits"; fail=1; fi
done

scenario solutions "$SOL"
for n in 01 02 03 04 05 06; do
  v=$(note "$n" "$TMP/res-solutions")
  if [ "$v" = "20.0" ]; then echo "OK   solutions  lab $n : 20/20"; else echo "FAIL solutions  lab $n : $v/20"; fail=1; fi
done

# Rendu étudiant (pack) puis notation par l'enseignant (grade) sur l'archive.
( cd "$TMP" && PIPECTL_WORKSPACE_ROOT="$TMP/ws-solutions" "$ROOT/pipectl" pack -o rendu.zip >/dev/null \
  && env -u PIPECTL_WORKSPACE_ROOT "$ROOT/pipectl" grade rendu.zip --results "$TMP/res-grade" >/dev/null 2>&1 )
if grep -q '^TOTAL;;90;90;20.0' "$TMP/res-grade/rapport.csv" 2>/dev/null; then echo "OK   rendu      pack + grade : 90/90"
else echo "FAIL rendu      pack + grade"; fail=1; fi

scenario erreurs "$ROOT/tests/wrong"
for n in 01 02 03 04 05 06; do
  v=$(note "$n" "$TMP/res-erreurs")
  if awk "BEGIN{exit !($v < 20)}"; then echo "OK   erreurs    lab $n : détectées ($v/20)"; else echo "FAIL erreurs    lab $n : non détectées"; fail=1; fi
done

if grep -h "Traceback" "$TMP"/*.log; then fail=1; fi
[ "$fail" = 0 ] && echo "Tous les tests passent." || { echo "Des tests échouent."; cat "$TMP/erreurs.log" | tail -40; }
exit "$fail"
