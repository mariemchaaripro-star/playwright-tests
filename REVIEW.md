# Règles de revue de code

Ce fichier est la **référence unique** des règles de revue du projet. Il est utilisé :
- par la commande Claude Code `/revue-code` (poste du développeur, VS Code ou terminal) ;
- par le script `scripts/revue_mr.sh` (revue automatisée en CI sur chaque MR) ;
- par le service Code Review de Claude sur GitHub, qui lit ce fichier à la racine du dépôt ;
- par les relecteurs humains.

Pour faire évoluer une règle : modifier ce fichier **par une MR**, relue et fusionnée comme du code.

---

## 1. Posture attendue

Tu relis comme un **développeur senior en automatisation de tests** qui engage sa responsabilité sur
la fusion de la MR. Ton objectif n'est pas de commenter beaucoup, mais de **trouver ce qui ferait
échouer, mentir ou coûter cher** la suite de tests : régressions, faux positifs, tests instables,
failles de sécurité, dette de conception.

- Rédige **en français**, de façon factuelle, précise et respectueuse : on commente le code, jamais la personne.
- Chaque remarque doit être **vérifiable** : `fichier:ligne`, extrait de code cité, raisonnement.
- **N'invente aucun problème.** Si tu as un doute, classe la remarque en « Question » et dis ce qu'il faudrait vérifier.
- Regroupe une même erreur répétée en **une seule remarque** qui liste toutes les occurrences.
- Signale aussi ce qui est **bien fait** : c'est ce qui doit être reproduit.

## 2. Périmètre

1. **Priorité absolue : les lignes ajoutées ou modifiées par la MR** (le diff source / cible).
2. Le code existant des fichiers touchés n'est commenté que s'il présente un risque **Bloquant ou Majeur** ;
   il est alors classé dans la section « Hors périmètre de la MR » du rapport (dette existante).
3. Les résultats des vérifications automatiques (lint, collecte, exécution des tests) font partie de la revue :
   un test en échec ou une erreur de collecte introduits par la MR sont **Bloquants**.

## 3. Niveaux de gravité

| Niveau | Définition | Effet sur la MR | Exemples |
|---|---|---|---|
| 🔴 **Bloquant** | Bug, régression, faille de sécurité, test qui ne vérifie rien ou qui ment | Fusion refusée | secret dans le code ; `expect` absent ; test cassé ; exception avalée |
| 🟠 **Majeur** | Problème de conception, de fiabilité ou de performance qui coûtera cher | À corriger dans la MR, sauf accord explicite | `sleep` ; sélecteur fragile ; tests dépendants ; duplication de logique |
| 🟡 **Mineur** | Lisibilité, nommage, documentation, typage | Corriger si simple | nom ambigu ; docstring obsolète ; annotation manquante |
| 💡 **Suggestion** | Amélioration optionnelle, l'auteur décide | Aucun | refactoring possible, simplification |
| ❓ **Question** | Besoin de comprendre l'intention | Réponse attendue | choix d'un scope de fixture, valeur d'un timeout |

Verdict de la revue :
- ✅ **Approuvée** : aucun Bloquant ni Majeur.
- ⚠️ **Approuvée avec réserves** : aucun Bloquant, des Majeurs acceptés et tracés (ticket).
- ❌ **Modifications demandées** : au moins un Bloquant, ou des Majeurs non justifiés.

## 4. Ce qu'il ne faut PAS signaler

- La mise en forme, l'ordre des imports, la longueur des lignes : c'est contrôlé par `ruff` (voir le résultat de la vérification automatique ; ne le signale que s'il est en échec).
- Les préférences de style personnelles qui ne violent aucune règle de ce document.
- Les fichiers générés : `reports/`, `test-results/`, `playwright/.auth/`, `requirements.txt` produit par `pip freeze`.
- Des « améliorations » sans gain démontrable (pas d'optimisation prématurée, pas d'abstraction spéculative).

---

## 5. Critères de revue

### 5.1 Architecture et respect des couches

Couches du projet et sens autorisé des dépendances :

```
tests/  ──▶  tests/conftest.py (fixtures)  ──▶  pages/ (Page Objects)  ──▶  Playwright
   │                    │                           │
   └──────────▶ data/, utils/, config/settings.py ◀─┘
```

- **[Bloquant]** Une couche basse importe une couche haute (`pages/` qui importe `tests/`, `config/` qui importe `pages/`…).
- **[Majeur]** Un test utilise directement `page.locator(...)` / `page.get_by_...(...)` : les sélecteurs vivent **uniquement** dans `pages/`.
- **[Majeur]** Un test instancie lui-même ses Page Objects ou sa préparation alors qu'une fixture existe (`login_page`, `inventory_page`, `auth_page`, `api`).
- **[Majeur]** URL, identifiants, timeouts ou chemins écrits en dur hors de `config/settings.py` / `pytest.ini`.
- **[Majeur]** Logique métier dupliquée : indiquer où la logique existe déjà (`fichier:ligne`).
- **[Mineur]** Nouveau fichier sans en-tête (docstring ou commentaire) décrivant son rôle.

### 5.2 Principes SOLID appliqués à l'automatisation

| Principe | Ce qu'on vérifie dans ce projet |
|---|---|
| **S** – Responsabilité unique | Un Page Object = une page ; une méthode = une action métier ; un test = un comportement. Signaler une méthode qui navigue, agit **et** vérifie. |
| **O** – Ouvert / fermé | Les nouvelles pages **étendent** `BasePage` sans la modifier pour un cas particulier ; pas de `if page == ...` dans une classe commune. |
| **L** – Substitution de Liskov | Une sous-classe de `BasePage` respecte le contrat de `goto()` et de `path` (même signature, même effet). |
| **I** – Ségrégation des interfaces | Fixtures petites et ciblées ; pas de « fixture fourre-tout » qui prépare tout pour tous les tests. |
| **D** – Inversion des dépendances | Les tests dépendent d'abstractions fournies par les fixtures (Page Objects, client `api`), pas de la construction concrète du navigateur ou du client HTTP. |

Compléter par **DRY** (pas de duplication), **KISS** (solution la plus simple qui marche) et
**YAGNI** (pas de code « pour plus tard »). Ne signaler un principe que si sa violation a un coût concret : l'expliquer.

### 5.3 Fiabilité des tests (le cœur de la revue)

- **[Bloquant]** Test sans vérification (`expect`/`assert`), ou dont la vérification ne peut pas échouer
  (`assert True`, comparaison d'une valeur avec elle-même, `assert response` sur un objet toujours vrai).
- **[Bloquant]** Vérification masquée : `try/except` autour d'un `expect`, `pytest.skip` conditionnel qui cache un échec.
- **[Majeur]** `time.sleep()` ou `page.wait_for_timeout()` : utiliser les assertions web-first `expect(...)` qui attendent automatiquement.
- **[Majeur]** `assert` Python sur une valeur lue dans la page à un instant T (`assert locator.inner_text() == ...`) au lieu de `expect(locator).to_have_text(...)`.
- **[Majeur]** Tests dépendants : ordre d'exécution, état laissé par un autre test, données partagées modifiées.
  Les tests doivent passer avec `pytest -n auto` et dans n'importe quel ordre.
- **[Majeur]** Données créées non uniques (risque de collision en parallèle) : utiliser `utils.helpers.unique_id()`.
- **[Majeur]** Relances (`--reruns`) utilisées pour masquer un test instable au lieu de le corriger.
- **[Mineur]** Test sans marker (`smoke`, `regression`, `api`) ou nom qui ne décrit pas le comportement attendu
  (`test_1`, `test_login` → `test_un_utilisateur_bloque_voit_une_erreur`).
- **[Mineur]** `parametrize` sans `ids` lisibles.

### 5.4 Sélecteurs

Ordre de préférence : `get_by_test_id` (attribut `data-test`) → `get_by_role(..., name=...)` → `get_by_label` /
`get_by_placeholder` / `get_by_text` → CSS simple.

- **[Majeur]** XPath absolu, classes CSS générées, sélecteur par index (`nth()`, `first` sans filtre), texte susceptible de changer sans raison.
- **[Mineur]** Sélecteur CSS brut (`locator("[data-test='x']")`) alors que `get_by_test_id("x")` est disponible.

### 5.5 Gestion des exceptions et des erreurs

- **[Bloquant]** `except:` nu, `except Exception: pass`, ou exception attrapée sans être relancée ni journalisée.
- **[Majeur]** Exception attrapée trop largement (`Exception`) alors qu'un type précis est attendu.
- **[Majeur]** Message d'erreur inexploitable : un échec doit dire **ce qui était attendu et ce qui a été obtenu**
  (`pytest.fail("...")`, message d'`assert`, message d'`expect`).
- **[Majeur]** Ressource non libérée en cas d'échec : contexte navigateur, client API, fichier.
  Utiliser une fixture avec `yield` (nettoyage garanti) ou `try/finally`.
- **[Majeur]** Configuration absente détectée trop tard : la règle du projet est « **échouer tôt** » (`config/settings.py`).

### 5.6 Sécurité

- **[Bloquant]** Secret dans le code, les données de test, les logs, les captures ou la CI en clair :
  mot de passe, jeton, clé d'API, cookie, `storage_state`. Seuls `.env` (non versionné) et les secrets CI sont autorisés.
- **[Bloquant]** Fichier sensible versionné : `.env`, `playwright/.auth/*.json` (contient des cookies de session).
- **[Majeur]** `.env.example` non mis à jour quand une variable est ajoutée.
- **[Majeur]** `ignore_https_errors=True`, vérification TLS désactivée, ou URL `http://` vers un environnement réel sans justification.
- **[Majeur]** Script shell / CI : variable non protégée par des guillemets (`$VAR` au lieu de `"$VAR"`),
  entrée externe (nom de branche, titre de MR) injectée dans une commande, `curl | bash` vers une source non officielle.
- **[Majeur]** CI : permissions plus larges que nécessaire, secrets exposés aux MR venant de forks, variable non masquée.
- **[Mineur]** Dépendance ajoutée sans version figée (`==`) ou non justifiée.

### 5.7 Performances et coût d'exécution

- **[Majeur]** Connexion par l'interface répétée dans chaque test alors que l'état de session peut être réutilisé (`auth_state`).
- **[Majeur]** Préparation de données par l'UI alors qu'elle est possible par l'API (plus rapide, moins fragile).
- **[Majeur]** Fixture de scope `session`/`module` qui partage un état **modifiable** entre tests (gain de vitesse au prix de l'isolation).
- **[Mineur]** Navigation inutile (`goto` répété), timeouts allongés « au cas où », vidéo ou trace activées sur tous les tests au lieu de « en cas d'échec ».

### 5.8 Maintenabilité et lisibilité

- **[Majeur]** Fonction de plus de ~40 lignes ou à plusieurs responsabilités ; complexité qui oblige à relire trois fois.
- **[Mineur]** Annotations de type manquantes sur une fonction publique, une fixture ou une méthode de Page Object.
- **[Mineur]** Nommage incohérent (mélange de langues dans un même module, abréviations obscures).
- **[Mineur]** Commentaire qui décrit **ce que fait** le code au lieu d'expliquer **pourquoi** ; code commenté laissé en place ; `print` de débogage.
- **[Mineur]** Documentation (`README.md`, `docs/`) non mise à jour alors que la MR change une commande, une variable ou un comportement.

### 5.9 Configuration, CI et dépendances

- **[Majeur]** Version de Python, de Playwright ou des dépendances incohérente entre `requirements.txt`, `pyproject.toml`, la CI et la documentation.
- **[Majeur]** Nouveau marker non déclaré dans `pytest.ini` (`--strict-markers` le refusera).
- **[Mineur]** Rapports ou artefacts CI non publiés en cas d'échec.

---

## 6. Rédaction d'une remarque

Chaque remarque suit ce format :

```
[GRAVITÉ][Catégorie] fichier:ligne — Titre court

Constat : ce qui est écrit (extrait de code cité).
Pourquoi : la conséquence concrète (bug, échec aléatoire, fuite, coût…).
Correction recommandée : le code ou la démarche exacte.
```

Le format complet du rapport est défini dans `docs/revue/MODELE_RAPPORT_REVUE.md`.
