# Tests automatisés : Playwright + Python (pytest)

Tests E2E (UI) et API pour l'application de démo [saucedemo.com](https://www.saucedemo.com),
avec l'API [jsonplaceholder](https://jsonplaceholder.typicode.com).

## Prérequis
- Python 3.11 ou plus
- Git

## Installation
```bash
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium firefox
cp .env.example .env               # puis adapter les valeurs
```

## Lancer les tests
| Commande | Rôle |
|---|---|
| `pytest` | toute la suite (Chromium, headless) |
| `pytest -m smoke` | tests critiques uniquement |
| `pytest -m regression` | régression |
| `pytest -m api` | tests API uniquement |
| `pytest -m "not api"` | tests UI uniquement |
| `pytest --headed --slowmo 500` | voir le navigateur |
| `pytest --browser firefox --browser chromium` | multi-navigateurs |
| `pytest -n auto` | exécution parallèle |
| `pytest --reruns 1` | 1 retry (CI uniquement) |
| `PWDEBUG=1 pytest -k login` | mode debug (Playwright Inspector) |
| `TEST_ENV=staging pytest` | charge `.env.staging` |
| `playwright codegen https://www.saucedemo.com` | enregistrer des sélecteurs |

## Rapports
- HTML : `reports/report.html`
- JUnit (CI) : `reports/junit.xml`
- En cas d'échec : captures d'écran, vidéos et traces dans `test-results/`
  (ouvrir une trace : `playwright show-trace test-results/<test>/trace.zip`)

## Structure
```
config/settings.py     configuration et variables d'environnement
pages/                 Page Object Model (sélecteurs + actions)
data/                  données de test (JSON, constantes)
utils/                 helpers réutilisables
tests/conftest.py      fixtures : auth, Page Objects, client API
tests/e2e/             tests UI
tests/api/             tests API
.github/workflows/     pipeline CI
```

## Conventions
- Un test = un comportement, nommé `test_<comportement_attendu>`, structure Arrange / Act / Assert.
- Les sélecteurs vivent **uniquement** dans `pages/`. Préférer `get_by_test_id`, `get_by_role`, `get_by_label`.
- Jamais de `time.sleep()` ni de `wait_for_timeout()` : utiliser `expect(...)` (attente automatique).
- Tests indépendants : aucun ne dépend d'un autre ni de l'ordre d'exécution.
- La connexion se fait une seule fois par session (`auth_state`), pas via l'UI dans chaque test.
- Chaque test porte au moins un marker : `smoke`, `regression` ou `api`.
- Aucun secret dans le code : `.env` en local, *secrets* GitHub en CI.
- Avant de pousser : `ruff check . && ruff format .`
