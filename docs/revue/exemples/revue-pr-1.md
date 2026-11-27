# Revue de code : docs/commentaires-documentation

| Élément | Valeur |
|---|---|
| Branche source | `origin/docs/commentaires-documentation` (`7b33a3b`) |
| Branche cible | `8191565^1` (`c371291`) |
| Commits relus | 1 |
| Fichiers modifiés | 22 (+486 / -3) |
| Date de la revue | 2026-11-27 |
| Relecteur | Claude (revue automatisée) |
| **Verdict** | ❌ Modifications demandées |

## 1. Synthèse

La MR ajoute un en-tête à chaque fichier (docstring ou commentaire) et crée `docs/DOCUMENTATION_TECHNIQUE.md` (381 lignes). Elle ne change aucune logique : le diff Python ne contient que des docstrings. Elle répond donc à son objectif sans aller au-delà.

La documentation est globalement juste et de bonne qualité. Le tableau des fixtures correspond à `tests/conftest.py`, et les commandes et les rapports sont exacts.

Un point Majeur conditionne la fusion. La MR demande de créer des fichiers `.env.staging` et `.env.preprod`, qui peuvent contenir des mots de passe, mais `.gitignore` ne les exclut pas. Ces fichiers risquent donc d'être commités (S1).

Le § 4.1 de la documentation décrit un ordre de priorité des variables qui n'est pas celui du code (A1).

Les tests n'ont pas pu s'exécuter (environnement). Même une fois S1 corrigé, le verdict restera au mieux « ⚠️ Approuvée avec réserves » tant que la suite n'aura pas été relancée.

Le commit `8191565` (« Merge pull request #1 ») montre que la MR est déjà fusionnée : les corrections devront passer par une MR de suivi.

| Gravité | Nombre |
|---|---|
| 🔴 Bloquant | 0 |
| 🟠 Majeur | 1 |
| 🟡 Mineur | 2 |
| 💡 Suggestion | 0 |
| ❓ Question | 3 |

*(Les 4 points de dette existante de la section 7 ne sont pas comptés : ils ne sont pas introduits par la MR.)*

## 2. Vérifications automatiques et tests exécutés

| Contrôle | Statut | Détail |
|---|---|---|
| Lint (`ruff check`) | ✅ | All checks passed! |
| Format (`ruff format --check`) | ✅ | 16 files already formatted |
| Collecte (`pytest --collect-only`) | ✅ | 11 tests collectés |
| Connectivité | ❌ | `saucedemo.com` et `jsonplaceholder.typicode.com` injoignables (proxy : 403 Forbidden) |
| Exécution des tests | ⚠️ Non concluant | 11/11 non concluants : 0 réussi, 0 échec imputable au code |
| Stabilité (relance) | ⚠️ Non exécutée | Sans objet, aucun test n'a pu s'exécuter |

**Interprétation :**
- **Ce qui est prouvé :** la MR ne casse ni le lint, ni le format, ni la collecte. Les 11 tests sont toujours découverts, avec leurs markers et leurs `ids`. C'est cohérent avec un diff qui ne touche que des docstrings et des commentaires.
- **Ce qui ne l'est pas :** aucun test n'a été exécuté. Les 3 tests d'API échouent sur `getaddrinfo ENOTFOUND jsonplaceholder.typicode.com`, un problème de réseau. Les 8 tests E2E échouent dès la préparation sur `BrowserType.launch: Executable doesn't exist`, car le navigateur n'est pas installé.
- **Origine des échecs :** ils viennent tous de l'environnement. Aucun n'est causé par la MR et aucun n'est préexistant dans le code. **Aucun test n'est à considérer comme réussi.**
- **Commit vérifié :** la vérification a tourné sur `8191565`, le commit de fusion de cette MR sur sa cible `c371291`, et non directement sur `7b33a3b`. Son contenu correspond au code de la MR.
- **Commande à relancer** dans un environnement qui a accès à Internet et aux navigateurs :
  ```bash
  playwright install chromium && bash scripts/verifier.sh
  ```

## 3. Anomalies détectées

### A1 — 🟡 Mineur — Le § 4.1 décrit un ordre de résolution des variables faux
- **Fichier :** `docs/DOCUMENTATION_TECHNIQUE.md:113-119`, à comparer avec `config/settings.py:18-26`
- **Constat :**
  ```markdown
  1. Variables d'environnement déjà définies (shell, CI)
  2. `.env.<TEST_ENV>` (par exemple `.env.staging`) : **surcharge** les valeurs de `.env`
  ...
  Si une variable n'a aucune valeur (absente ou vide), `RuntimeError(...)` est levée
  ```
  Ce que fait réellement le code :
  ```python
  load_dotenv(ROOT_DIR / f".env.{os.getenv('TEST_ENV', 'dev')}", override=True)
  ...
  value = os.getenv(name, default)
  if not value:
      raise RuntimeError(...)
  ```
- **Pourquoi c'est un problème :**
  - **Priorité :** avec `override=True`, `.env.<TEST_ENV>` écrase **aussi** les variables du shell et de la CI. Il passe donc en 1ʳᵉ position, et non en 2ᵉ.
  - **Exemple :** `BASE_URL=https://autre pytest` est ignoré si un `.env.dev` définit `BASE_URL`. `TEST_ENV` vaut `dev` par défaut, donc ce fichier est chargé s'il existe.
  - **Variable absente :** elle prend la valeur par défaut (`os.getenv(name, default)`) et ne lève **pas** d'erreur. Seule une variable définie mais **vide** déclenche le `RuntimeError`.
  - **Conséquence :** un testeur qui suit la documentation pour surcharger une valeur en ligne de commande obtiendra un autre résultat que celui attendu.
- **Correction recommandée :** aligner le code sur la documentation (option préférable, car le shell et la CI doivent primer), ou bien corriger la documentation.
  ```python
  # config/settings.py — le shell/CI prime, puis .env.<TEST_ENV>, puis .env
  from dotenv import dotenv_values, load_dotenv

  _env_name = os.getenv("TEST_ENV") or dotenv_values(ROOT_DIR / ".env").get("TEST_ENV") or "dev"
  load_dotenv(ROOT_DIR / f".env.{_env_name}")  # sans override
  load_dotenv(ROOT_DIR / ".env")               # sans override
  ```
  Remplacer aussi la phrase de la ligne 118 par :
  > « Si une variable est définie mais vide (cas d'un secret CI inexistant), `RuntimeError(...)` est levée ; une variable absente prend la valeur par défaut. »

## 4. Problèmes de conception et mauvaises pratiques

### C1 — 🟡 Mineur — L'exemple de test de référence n'a pas d'annotations de type
- **Fichier :** `docs/DOCUMENTATION_TECHNIQUE.md:260`
- **Constat :**
  ```python
  def test_produit_ajoute_apparait_dans_le_panier(inventory_page, cart_page) -> None:
  ```
- **Pourquoi c'est un problème :** CLAUDE.md exige des annotations de type sur les fonctions publiques et les fixtures. Les tests existants les respectent (`inventory_page: InventoryPage`). Or c'est cet exemple qui sera copié pour écrire les prochains tests.
- **Correction recommandée :**
  ```python
  from pages.cart_page import CartPage
  from pages.inventory_page import InventoryPage


  @pytest.mark.regression
  def test_produit_ajoute_apparait_dans_le_panier(
      inventory_page: InventoryPage, cart_page: CartPage
  ) -> None:
  ```

## 5. Risques de sécurité

### S1 — 🟠 Majeur — Les fichiers `.env.<TEST_ENV>` recommandés par la MR ne sont pas ignorés par Git
- **Fichiers :** `.env.example:4`, `.gitignore:2` et `:9`, `docs/DOCUMENTATION_TECHNIQUE.md:114`
- **Constat :** la MR ajoute cette consigne :
  ```
  # Pour un autre environnement, créer .env.staging, .env.preprod..., puis lancer : TEST_ENV=staging pytest
  ```
  Mais `.gitignore` ne contient que :
  ```
  .env
  ```
  Sans caractère joker, ce motif ne correspond qu'au fichier nommé exactement `.env`. `.env.staging` et `.env.preprod` restent donc suivis par Git. Le commentaire ajouté (« secrets (.env) ») laisse penser le contraire.
- **Pourquoi c'est un problème :**
  - **Fuite de secrets :** un `.env.staging` contient par construction `USER_PASSWORD` et les identifiants d'un environnement réel. Un `git add .` le commite, et le secret est exposé dans l'historique.
  - **CI faussée :** à cause de `override=True` (voir A1), un `.env.dev` versionné écraserait silencieusement les secrets CI.
  - La MR introduit ce risque en documentant la pratique sans protéger les fichiers.
- **Correction recommandée :**
  ```gitignore
  .env
  .env.*
  !.env.example
  ```
  Ensuite, vérifier avec `git check-ignore -v .env.staging`.

## 6. Risques de performance et de coût d'exécution

Aucun point. La MR ne modifie aucun code exécuté.

## 7. Hors périmètre de la MR (dette existante)

Ces points étaient déjà présents dans les fichiers touchés : la MR les documente sans les introduire. Un ticket séparé est recommandé pour chacun.

### H1 — 🔴 Bloquant (règle 5.6), impact réel faible — Mot de passe écrit en dur dans le code et les données
- **Fichiers :**
  - `config/settings.py:36` : `password: str = _get("USER_PASSWORD", "secret_sauce")`
  - `data/login_cases.json:3`
  - `.env.example:12`
- **Pourquoi c'est un problème :**
  - REVIEW.md interdit tout mot de passe dans le code. Ici, c'est le mot de passe public de l'application de démo, donc l'impact actuel est nul.
  - Mais le modèle sera reproduit tel quel pour une vraie application.
  - La documentation est incohérente sur ce point : elle présente ce mot de passe comme *(secret)* (`DOCUMENTATION_TECHNIQUE.md:133`) et exige « jamais un vrai secret » dans `.env.example` (`DOCUMENTATION_TECHNIQUE.md:137`).
- **Correction recommandée :**
  - Ne pas donner de valeur par défaut au mot de passe : `password: str = _get("USER_PASSWORD")`.
  - Mettre `USER_PASSWORD=` (vide, à renseigner) dans `.env.example`.
  - Dans `login_cases.json`, injecter le mot de passe valide au moment de la paramétrisation, par exemple avec une valeur sentinelle `"<valid>"` remplacée par `settings.password`.

### H2 — 🟠 Majeur — `auth_state` : fichier de session partagé entre les workers `-n auto`, et contexte non fermé en cas d'échec
- **Fichier :** `tests/conftest.py:44-57`
- **Constat :**
  ```python
  context.storage_state(path=settings.auth_file)
  context.close()
  return str(settings.auth_file)
  ```
- **Pourquoi c'est un problème :**
  - **Écritures concurrentes :** la documentation le confirme (`DOCUMENTATION_TECHNIQUE.md:183`), chaque worker xdist se connecte. Or tous écrivent dans le **même** `playwright/.auth/user.json`.
  - **Échecs aléatoires :** l'écriture n'est pas atomique (le fichier est vidé puis réécrit). Un worker qui lit le fichier pendant qu'un autre l'écrit (`new_context(storage_state=...)`) peut lire un JSON vide ou tronqué. Cela peut arriver en CI, qui lance `-n auto`.
  - **Contexte non libéré :** si la connexion échoue, `context.close()` n'est jamais appelé (règle 5.5).
- **Correction recommandée :** garder l'état en mémoire, propre à chaque worker. Cela supprime aussi le fichier de cookies sur disque. Penser à mettre à jour le § 5 de la documentation.
  ```python
  @pytest.fixture(scope="session")
  def auth_state(browser: Browser, browser_context_args: dict) -> dict:
      """Connexion UNE seule fois par worker ; l'état reste en mémoire."""
      context = browser.new_context(**browser_context_args)
      try:
          page = context.new_page()
          login_page = LoginPage(page)
          login_page.goto()
          login_page.login(settings.standard_user, settings.password)
          InventoryPage(page).expect_loaded()
          return context.storage_state()
      finally:
          context.close()


  @pytest.fixture
  def auth_page(new_context: Callable[..., BrowserContext], auth_state: dict) -> Page:
      return new_context(storage_state=auth_state).new_page()
  ```

### H3 — 🟠 Majeur — Le test de tri vérifie une valeur lue à un instant T, et passe si la liste est vide
- **Fichiers :** `tests/e2e/test_inventory.py:37-38`, `pages/inventory_page.py:35-37`
- **Constat :**
  ```python
  prices = inventory_page.get_prices()
  assert prices == sorted(prices)
  ```
  `get_prices()` repose sur `all_text_contents()`, qui n'attend rien.
- **Pourquoi c'est un problème :**
  - La lecture peut avoir lieu avant que le tri soit appliqué (règle 5.3, `assert` sur une valeur lue dans la page).
  - Si aucun prix n'est rendu, `[] == sorted([])` est vrai et le test passe sans rien vérifier.
- **Correction recommandée :**
  ```python
  # pages/inventory_page.py, dans __init__
  self.prices = page.get_by_test_id("inventory-item-price")

  # tests/e2e/test_inventory.py
  inventory_page.sort_by("lohi")
  expect(inventory_page.prices).to_have_text(
      ["$7.99", "$9.99", "$15.99", "$15.99", "$29.99", "$49.99"]
  )
  ```

### H4 — 🟠 Majeur — Le workflow CI ne restreint pas les permissions du jeton
- **Fichier :** `.github/workflows/playwright.yml:8-18`
- **Constat :** il n'y a aucun bloc `permissions:`, donc le `GITHUB_TOKEN` garde les permissions par défaut du dépôt. Selon la configuration, elles peuvent inclure l'écriture.
- **Pourquoi c'est un problème :** une action compromise, ou une dépendance installée par `pip install`, s'exécute avec ce jeton (règle 5.6, permissions plus larges que nécessaire). Le job n'a besoin que de lire le code.
- **Correction recommandée :**
  ```yaml
  permissions:
    contents: read
  ```
  À placer au niveau racine, sous `on:`.

## 8. Points positifs

- **En-têtes :** chaque fichier touché a maintenant un en-tête qui décrit son rôle, comme l'exige CLAUDE.md. L'exception de `login_cases.json` (le JSON n'accepte pas de commentaires) est justifiée et renvoie vers son format (§ 8.1).
- **Le pourquoi plutôt que le quoi :** les commentaires expliquent les raisons des choix, par exemple `playwright/.auth` « contient des cookies de session », les versions figées « pour que tout le monde exécute exactement les mêmes versions », `--strict-markers` « refuse un tag inconnu ou mal orthographié ».
- **Documentation fidèle au code :** le tableau des fixtures (§ 5) correspond exactement à `tests/conftest.py` (noms, portées, dépendances). La note du § 7.2 sur le partage de `auth_page` au sein d'un même test est correcte. La table de dépannage (§ 13) reprend les vrais messages d'erreur (`Executable doesn't exist`, `ENOTFOUND`).
- **Règles de qualité visibles pour les nouveaux contributeurs :** la stratégie de sélecteurs, l'interdiction de `sleep` et l'exigence de données uniques (`unique_id()`) sont rappelées.
- **Périmètre maîtrisé :** aucune modification de logique n'est glissée dans une MR de documentation. Le lint, le format et la collecte restent verts.

## 9. Plan d'action

- [ ] S1 : ajouter `.env.*` et `!.env.example` à `.gitignore` (condition de fusion, via une MR de suivi puisque `8191565` est déjà fusionné).
- [ ] A1 : aligner `config/settings.py` et le § 4.1 de la documentation sur l'ordre réel de résolution des variables et sur le comportement d'une variable absente ou vide.
- [ ] C1 : annoter les paramètres de l'exemple `test_produit_ajoute_apparait_dans_le_panier`.
- [ ] Relancer `playwright install chromium && bash scripts/verifier.sh` dans un environnement qui a accès aux sites testés.
- [ ] H2 (ticket) : supprimer le fichier de session partagé entre workers et garantir la fermeture du contexte dans `auth_state`.
- [ ] H3 (ticket) : remplacer l'`assert` sur `get_prices()` par `expect(...).to_have_text([...])`.
- [ ] H4 (ticket) : ajouter `permissions: contents: read` au workflow.
- [ ] H1 (ticket) : retirer le mot de passe par défaut du code, des données et de `.env.example`.

## 10. Questions à l'auteur

1. ❓ **Relances systématiques en CI.** `--reruns 1` est appliqué en CI à toutes les exécutions (`playwright.yml:41,44`), et le § 1 de la documentation le présente comme la norme. Un test qui ne passe qu'à la relance est-il suivi quelque part (rapport, ticket) ? Si ce n'est pas le cas, la relance masque l'instabilité (règle 5.3). À vérifier : la présence des tests « rerun » dans `reports/report.html` et leur suivi.
2. ❓ **Mots de passe dans les traces publiées.** Les traces conservées en cas d'échec (`--tracing retain-on-failure`) enregistrent les valeurs saisies par `fill()`, dont le mot de passe des tests de `test_login.py`. Elles sont publiées dans l'artifact `test-reports`. Est-ce acceptable pour les environnements réels visés par `.env.<TEST_ENV>` ? À vérifier en ouvrant une trace d'échec avec `playwright show-trace`.
3. ❓ **Version minimale de Python.** La documentation et le README indiquent « Python 3.11+ » (cohérent avec `target-version = "py311"`), alors que CLAUDE.md indique « Python 3.10+ ». Quelle est la version de référence, pour aligner les deux ?
