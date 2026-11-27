# Projet de tests automatisés : Playwright + pytest (Python)

Tests E2E (UI) de l'application de démo saucedemo.com et tests d'API sur jsonplaceholder.
Documentation détaillée : `README.md` et `docs/DOCUMENTATION_TECHNIQUE.md`.

## Commandes

| But | Commande |
|---|---|
| Installer | `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && playwright install chromium` |
| Lint | `ruff check . && ruff format --check .` |
| Tous les tests | `pytest` |
| Tests critiques | `pytest -m smoke` |
| Vérification complète (lint + collecte + connectivité + tests) | `bash scripts/verifier.sh` |
| Revue de code d'une branche | `/revue-code` (Claude Code) ou `bash scripts/revue_mr.sh --cible origin/main` |

## Structure

- `config/settings.py` : configuration lue depuis `.env` ; seul endroit pour URL, identifiants, chemins.
- `pages/` : Page Objects (sélecteurs + actions). `BasePage` est la classe parente.
- `tests/conftest.py` : fixtures partagées (connexion unique par session, Page Objects, client API).
- `tests/e2e/`, `tests/api/` : les tests. `data/` : données de test. `utils/` : utilitaires.
- `scripts/` : vérification et revue automatisées. `docs/revue/` : processus, modèle de rapport, recette.

## Conventions

- Python 3.10+, annotations de type sur les fonctions publiques, fixtures et méthodes de Page Object.
- Sélecteurs uniquement dans `pages/`, de préférence `get_by_test_id` (attribut `data-test`) ou `get_by_role`.
- Vérifications avec `expect(...)` (attente automatique) ; jamais `time.sleep()` ni `wait_for_timeout()`.
- Chaque test : un comportement, au moins un marker (`smoke`, `regression`, `api`), indépendant des autres.
- Aucun secret dans le code : `.env` (non versionné) en local, secrets CI en intégration continue.
- Chaque fichier commence par un en-tête qui décrit son rôle.

## Revue de code

Les règles de revue s'appliquent à toute revue sur ce projet :

@REVIEW.md
