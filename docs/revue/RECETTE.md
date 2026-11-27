# Recette fonctionnelle : tests automatisés et revue de code automatisée

Objectif : prouver que la configuration fonctionne, que **tous** les tests s'exécutent, et que chaque
erreur est **clairement identifiée** (défaut du code ou problème d'environnement).
À rejouer après toute modification de `scripts/`, `REVIEW.md`, `.claude/` ou de la CI.

## 1. Prérequis

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install --with-deps chromium
cp .env.example .env
```
Le poste doit accéder à `www.saucedemo.com` et `jsonplaceholder.typicode.com`.

## 2. Scénarios

| ID | Scénario | Commande | Résultat attendu |
|---|---|---|---|
| R01 | Lint et format | `bash scripts/verifier.sh` (lignes « Lint », « Format ») | ✅ OK |
| R02 | Collecte | idem, ligne « Collecte » | ✅ 11 tests collectés, aucune erreur d'import |
| R03 | Connectivité | idem, ligne « Connectivité » | ✅ OK pour UI et API ; sinon `INJOIGNABLE` avec la raison |
| R04 | **Exécution de toute la suite** | `bash scripts/verifier.sh` | ✅ 11 réussis, code de sortie 0 |
| R05 | Exécution parallèle | `bash scripts/verifier.sh -- -n auto` | ✅ 11 réussis (tests indépendants) |
| R06 | Stabilité | `bash scripts/verifier.sh --repetitions 3` | ✅ « Aucun test instable sur 3 exécutions » |
| R07 | Un test sait échouer | dans `tests/e2e/test_inventory.py`, remplacer `to_have_count(6)` par `to_have_count(7)`, relancer `bash scripts/verifier.sh`, puis annuler (`git checkout tests/`) | ❌ 1 « Échec » avec `tests/e2e/test_inventory.py:<ligne>` et le message attendu/obtenu |
| R08 | Erreur d'environnement identifiée | couper le réseau (ou `BASE_URL=https://site-inexistant.invalid bash scripts/verifier.sh`) | 🌐 tests classés « Environnement » avec la cause ; **pas** « Échec » |
| R09 | Configuration manquante identifiée | renommer `.env`, vider une variable (`USER_PASSWORD= bash scripts/verifier.sh`) | « CONFIGURATION INVALIDE » / « configuration manquante (.env) » |
| R10 | Contexte de revue | `bash scripts/revue_mr.sh --cible origin/main --sans-claude` sur une branche de MR | `reports/revue/contexte/` contient `infos.md`, `diff.patch`, `verification.md` |
| R11 | Revue complète | `bash scripts/revue_mr.sh --cible origin/main` | rapport `reports/revue/revue-<branche>.md` conforme au modèle, remarques avec `fichier:ligne` |
| R12 | Commande `/revue-code` | dans Claude Code (VS Code) : `/revue-code origin/main` | même rapport, synthèse affichée dans la conversation |
| R13 | CI GitLab | ouvrir une MR de test | job `verification` vert/rouge selon les tests ; commentaire de revue publié par `revue-claude` |

## 3. Procès-verbal de recette

Recette du 2026-11-27, conteneur Linux (Python 3.13), **sans accès réseau aux sites testés**
(proxy : 403) et avec des navigateurs Playwright d'une autre version que celle du projet.

| ID | Statut | Observations |
|---|---|---|
| R01 | ✅ Conforme | 16 fichiers, lint et format OK |
| R02 | ✅ Conforme | 11 tests collectés |
| R03 | ✅ Conforme | Les deux sites sont signalés `INJOIGNABLE`, avec la raison (403 du proxy) |
| R04 | ⚠️ Non concluant | 11/11 classés « Environnement » : `ENOTFOUND` (API), `Executable doesn't exist` (navigateur). **À rejouer sur un poste ayant accès aux sites.** |
| R05 | ⏸️ Non exécuté | Dépend de R04 |
| R06 | ✅ Mécanisme validé | Validé sur une suite témoin : un test qui alterne succès et échec est signalé `REUSSI → ECHEC`. À rejouer sur la vraie suite. |
| R07 | ✅ Mécanisme validé | Validé sur une suite témoin : l'échec est classé « Échec », avec `fichier:ligne` et `assert 13 == 30`. À rejouer sur la vraie suite. |
| R08 | ✅ Conforme | Aucun faux « Échec » : les 11 tests sont classés « Environnement », avec la cause |
| R09 | ✅ Conforme | `USER_PASSWORD=` donne « Variable d'environnement manquante : USER_PASSWORD » (collecte, connectivité) et « Les tests n'ont pas démarré » |
| R10 | ✅ Conforme | Contexte de la PR n°1 : 1 commit, 22 fichiers, aucun avertissement de copie de travail |
| R11 | ✅ Conforme | Rapport de 253 lignes (`docs/revue/exemples/revue-pr-1.md`) ; les 19 références `fichier:ligne` ont été vérifiées ; les anomalies S1 et A1 ont été reproduites |
| R12 | ⏸️ Non exécuté | VS Code n'est pas disponible dans l'environnement de recette |
| R13 | ⏸️ Non exécuté | Pas d'instance GitLab ; YAML validé syntaxiquement (2 étapes, 2 jobs) |

Défauts trouvés et corrigés pendant la recette :
- emplacement répété (« test → origine » identiques) ;
- message peu clair quand pytest ne démarre pas (aucun rapport JUnit).
