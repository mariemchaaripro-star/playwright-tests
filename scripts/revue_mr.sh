#!/usr/bin/env bash
# Revue de code automatisée d'une branche (MR) par rapport à sa branche cible.
#   1. prépare le contexte : commits, fichiers modifiés, diff (reports/revue/contexte/) ;
#   2. lance la vérification complète : lint, collecte, connectivité, tous les tests (scripts/verifier.sh) ;
#   3. demande à Claude Code une revue selon REVIEW.md et écrit le rapport Markdown.
#
# Usage : bash scripts/revue_mr.sh [options]
#   --cible REF          branche cible de la MR (défaut : origin/main)
#   --source REF         branche relue (défaut : HEAD, la branche courante)
#   --sortie FICHIER     chemin du rapport (défaut : reports/revue/revue-<branche>.md)
#   --repetitions N      exécute la suite N fois pour détecter les tests instables (défaut : 1)
#   --sans-tests         ne lance pas les tests ; réutilise reports/verification/resume.md s'il existe (CI)
#   --sans-claude        prépare seulement le contexte et la vérification (utilisé par /revue-code)
# Code de sortie : 0 si le rapport (ou le contexte) est produit, 1 en cas d'erreur, 2 si mauvaise utilisation.

set -euo pipefail

RACINE="$(git rev-parse --show-toplevel)"
cd "$RACINE"

CIBLE="origin/main"
SOURCE="HEAD"
SORTIE=""
REPETITIONS=1
SANS_TESTS=0
SANS_CLAUDE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --cible) CIBLE="${2:?--cible attend une branche}"; shift 2 ;;
    --source) SOURCE="${2:?--source attend une branche}"; shift 2 ;;
    --sortie) SORTIE="${2:?--sortie attend un chemin}"; shift 2 ;;
    --repetitions) REPETITIONS="${2:?--repetitions attend un nombre}"; shift 2 ;;
    --sans-tests) SANS_TESTS=1; shift ;;
    --sans-claude) SANS_CLAUDE=1; shift ;;
    -h | --help) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Option inconnue : $1 (voir --help)" >&2; exit 2 ;;
  esac
done

# Résout une référence ; tente un « git fetch » pour les branches distantes absentes en local.
resoudre() {
  local ref="$1"
  if ! git rev-parse --verify --quiet "${ref}^{commit}" >/dev/null && [[ "$ref" == origin/* ]]; then
    git fetch --quiet origin "${ref#origin/}" || true
  fi
  git rev-parse --verify --quiet "${ref}^{commit}" || {
    echo "Référence introuvable : $ref" >&2
    exit 2
  }
}

SHA_CIBLE="$(resoudre "$CIBLE")"
SHA_SOURCE="$(resoudre "$SOURCE")"
BASE="$(git merge-base "$SHA_CIBLE" "$SHA_SOURCE")"

NOM_SOURCE="$SOURCE"
[ "$SOURCE" = "HEAD" ] && NOM_SOURCE="$(git rev-parse --abbrev-ref HEAD)"
SLUG="$(printf '%s' "$NOM_SOURCE" | tr -c 'A-Za-z0-9._-' '-')"
SORTIE="${SORTIE:-reports/revue/revue-$SLUG.md}"

CONTEXTE="reports/revue/contexte"
rm -rf "$CONTEXTE"
mkdir -p "$CONTEXTE" "$(dirname "$SORTIE")"

if git diff --quiet "$BASE" "$SHA_SOURCE"; then
  echo "Aucune modification entre $CIBLE et $SOURCE : rien à relire."
  exit 0
fi

# ---------- 1. Contexte de la MR ----------
git diff --unified=10 "$BASE" "$SHA_SOURCE" >"$CONTEXTE/diff.patch"
FICHIERS_MODIFIES="$(git diff --name-only --diff-filter=d "$BASE" "$SHA_SOURCE")"
{
  echo "# Contexte de la merge request"
  echo
  echo "| Élément | Valeur |"
  echo "|---|---|"
  echo "| Branche source | \`$NOM_SOURCE\` (\`$(git rev-parse --short "$SHA_SOURCE")\`) |"
  echo "| Branche cible | \`$CIBLE\` (\`$(git rev-parse --short "$SHA_CIBLE")\`) |"
  echo "| Base commune | \`$(git rev-parse --short "$BASE")\` |"
  echo "| Commits relus | $(git rev-list --count "$BASE..$SHA_SOURCE") |"
  echo "| Bilan | $(git diff --shortstat "$BASE" "$SHA_SOURCE" | sed 's/^ *//') |"
  echo
  echo "## Commits"
  echo
  git log --reverse --format='- `%h` %s (%an, %ad)' --date=short "$BASE..$SHA_SOURCE"
  echo
  echo "## Fichiers modifiés"
  echo
  git diff --name-status "$BASE" "$SHA_SOURCE" | sed 's/^/    /'
  echo
  # Les fichiers sont lus et les tests exécutés sur la copie de travail : elle doit correspondre à la source.
  if [ -n "$FICHIERS_MODIFIES" ] && ! git diff --quiet "$SHA_SOURCE" -- $FICHIERS_MODIFIES; then
    echo "> ⚠️ La copie de travail diffère de \`$NOM_SOURCE\` sur des fichiers de la MR :"
    echo "> les numéros de ligne et les tests peuvent ne pas correspondre. Faire \`git checkout $NOM_SOURCE\`."
  fi
} >"$CONTEXTE/infos.md"

# ---------- 2. Vérification et tests ----------
if [ "$SANS_TESTS" -eq 0 ]; then
  echo "▶ Vérification complète (lint, collecte, connectivité, tests)…"
  bash scripts/verifier.sh --repetitions "$REPETITIONS" >/dev/null || true
fi
if [ -f reports/verification/resume.md ]; then
  cp reports/verification/resume.md "$CONTEXTE/verification.md"
else
  echo "Aucune vérification disponible : les tests n'ont pas été exécutés pour cette revue." >"$CONTEXTE/verification.md"
fi

echo "✔ Contexte prêt : $CONTEXTE/ (infos.md, diff.patch, verification.md)"
if [ "$SANS_CLAUDE" -eq 1 ]; then
  exit 0
fi

# ---------- 3. Revue par Claude Code (lecture seule) ----------
if ! command -v claude >/dev/null; then
  echo "Claude Code (commande « claude ») est introuvable : https://code.claude.com/docs" >&2
  exit 1
fi

echo "▶ Revue de code par Claude…"
# Outils limités à la lecture : Claude ne peut ni modifier un fichier ni lancer de commande.
claude -p "$(cat .claude/prompts/revue-mr.md)" \
  --allowedTools "Read Grep Glob" \
  --max-turns 80 >"$SORTIE.tmp"
mv "$SORTIE.tmp" "$SORTIE"
echo "✔ Rapport de revue : $SORTIE"
