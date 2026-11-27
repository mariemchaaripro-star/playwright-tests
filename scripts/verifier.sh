#!/usr/bin/env bash
# Vérification automatique du projet : lint, format, collecte, connectivité, exécution des tests.
# Écrit reports/verification/resume.md (lu par la revue de code) et les journaux de chaque contrôle.
# Code de sortie : 0 = tout est vert ; 1 = au moins un contrôle en échec ; 2 = erreur d'utilisation.
#
# Usage : bash scripts/verifier.sh [--repetitions N] [-- options pytest...]
#   --repetitions N   exécute la suite N fois pour détecter les tests instables (défaut : 1)
#   -- ...            options passées à pytest (ex. : -- -m smoke -n auto)

set -uo pipefail

RACINE="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$RACINE" || exit 2

SORTIE="reports/verification"
REPETITIONS=1
OPTIONS_PYTEST=()

while [ $# -gt 0 ]; do
  case "$1" in
    --repetitions) REPETITIONS="${2:-}"; shift 2 ;;
    --) shift; OPTIONS_PYTEST=("$@"); break ;;
    -h | --help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Option inconnue : $1 (voir --help)" >&2; exit 2 ;;
  esac
done

if ! [[ "$REPETITIONS" =~ ^[1-9][0-9]*$ ]]; then
  echo "--repetitions attend un entier >= 1" >&2
  exit 2
fi

# Python du projet : l'environnement virtuel s'il existe, sinon celui du système.
if [ -x .venv/bin/python ]; then PYTHON=".venv/bin/python"; else PYTHON="python3"; fi

rm -rf "$SORTIE"
mkdir -p "$SORTIE"

STATUT_GLOBAL=0
LIGNES=()

# controle <nom> <fichier-journal> <commande...> : exécute la commande, journalise, note le statut.
controle() {
  local nom="$1" journal="$SORTIE/$2"
  shift 2
  echo "▶ $nom"
  if "$@" >"$journal" 2>&1; then
    LIGNES+=("| $nom | ✅ OK | $(resume_journal "$journal") | \`$journal\` |")
  else
    STATUT_GLOBAL=1
    LIGNES+=("| $nom | ❌ Échec | $(resume_journal "$journal") | \`$journal\` |")
  fi
}

# Dernière ligne non vide du journal, nettoyée pour un tableau Markdown.
resume_journal() {
  grep -v '^[[:space:]]*$' "$1" | tail -n 1 | tr -d '`|' | sed 's/=\{3,\}//g; s/^ *//; s/ *$//' | cut -c1-160
}

controle "Lint (ruff check)" lint.log "$PYTHON" -m ruff check .
controle "Format (ruff format --check)" format.log "$PYTHON" -m ruff format --check .
controle "Collecte des tests (pytest --collect-only)" collecte.log \
  "$PYTHON" -m pytest --collect-only -q -p no:cacheprovider \
  --junitxml="$SORTIE/collecte-junit.xml" --html="$SORTIE/collecte.html"
controle "Connectivité des environnements testés" connectivite.log "$PYTHON" scripts/connectivite.py

for ((i = 1; i <= REPETITIONS; i++)); do
  libelle="Exécution des tests"
  [ "$REPETITIONS" -gt 1 ] && libelle="Exécution des tests ($i/$REPETITIONS)"
  controle "$libelle" "tests-$i.log" \
    "$PYTHON" -m pytest -p no:cacheprovider \
    --junitxml="$SORTIE/junit-$i.xml" --html="$SORTIE/rapport-$i.html" --self-contained-html \
    "${OPTIONS_PYTEST[@]}"
done

# nullglob : aucun rapport JUnit si pytest n'a pas pu démarrer (erreur d'import, de configuration…)
shopt -s nullglob
RAPPORTS_JUNIT=("$SORTIE"/junit-*.xml)
shopt -u nullglob
"$PYTHON" scripts/resume_resultats.py "${RAPPORTS_JUNIT[@]}" >"$SORTIE/resume-tests.md" 2>&1 \
  || STATUT_GLOBAL=1

{
  echo "# Résultat de la vérification automatique"
  echo
  echo "- Date : $(date '+%Y-%m-%d %H:%M')"
  echo "- Commit : \`$(git rev-parse --short HEAD 2>/dev/null || echo inconnu)\` sur \`$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo inconnu)\`"
  echo "- Python : $("$PYTHON" --version 2>&1)"
  echo "- Statut global : $([ "$STATUT_GLOBAL" -eq 0 ] && echo '✅ tous les contrôles sont verts' || echo '❌ au moins un contrôle en échec')"
  echo
  echo "## Contrôles"
  echo
  echo "| Contrôle | Statut | Détail | Journal |"
  echo "|---|---|---|---|"
  printf '%s\n' "${LIGNES[@]}"
  echo
  if [ -s "$SORTIE/connectivite.log" ]; then
    echo "## Connectivité"
    echo
    sed 's/^/    /' "$SORTIE/connectivite.log"
    echo
  fi
  cat "$SORTIE/resume-tests.md"
} >"$SORTIE/resume.md"

echo
cat "$SORTIE/resume.md"
exit "$STATUT_GLOBAL"
