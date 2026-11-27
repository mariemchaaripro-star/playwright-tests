# Processus de revue de code automatisée

Ce document explique comment la revue de code automatisée fonctionne, comment la lancer
(sur le poste ou en CI) et comment la faire évoluer.

## 1. Vue d'ensemble

```
                     ┌───────────────────────────── scripts/revue_mr.sh ─────────────────────────────┐
 Branche de la MR ──▶│ 1. Contexte            2. Vérification             3. Revue par Claude        │──▶ Rapport
 Branche cible    ──▶│  commits, fichiers,     scripts/verifier.sh :        lecture seule,            │    Markdown
                     │  diff (git)             lint, format, collecte,      règles REVIEW.md,         │
                     │                         connectivité, tous les tests modèle de rapport         │
                     └───────────────────────────────────────────────────────────────────────────────┘
```

| Fichier | Rôle |
|---|---|
| `REVIEW.md` | **Règles de revue** : posture, périmètre, gravités, critères (architecture, SOLID, fiabilité des tests, exceptions, sécurité, performances, maintenabilité). Référence unique. |
| `CLAUDE.md` | Conventions du projet ; importe `REVIEW.md` pour toute session Claude Code sur le projet. |
| `.claude/prompts/revue-mr.md` | Méthode de revue en 5 passes et consignes de rendu (utilisée en CI et par `/revue-code`). |
| `.claude/skills/revue-code/SKILL.md` | Commande `/revue-code` dans Claude Code (VS Code ou terminal). |
| `docs/revue/MODELE_RAPPORT_REVUE.md` | Format obligatoire du rapport. |
| `scripts/verifier.sh` | Vérification complète, utilisable seule : `bash scripts/verifier.sh`. |
| `scripts/connectivite.py` | Contrôle que les sites testés sont joignables (sépare « environnement » et « code »). |
| `scripts/resume_resultats.py` | Résumé des résultats JUnit : catégorie de chaque échec, fichier:ligne, tests instables. |
| `scripts/revue_mr.sh` | Orchestration de la revue d'une branche par rapport à sa cible. |
| `ci/gitlab-ci.revue.yml` | Jobs GitLab CI : `verification` (bloquant) et `revue-claude` (commentaire sur la MR). |
| `.gitlab/merge_request_templates/Default.md`, `.github/pull_request_template.md` | Liste de contrôle de l'auteur. |

## 2. Lancer une revue sur son poste

Prérequis : environnement Python du projet installé, `playwright install chromium`, fichier `.env`,
Claude Code installé et connecté (extension VS Code ou commande `claude`).

```bash
git fetch origin
git checkout <branche-de-la-MR>
```

**Option A, dans Claude Code (VS Code ou terminal)** : interactive, vous pouvez poser des questions ensuite.
```
/revue-code origin/main
```

**Option B, en une commande** : non interactive, identique à la CI.
```bash
bash scripts/revue_mr.sh --cible origin/main
```

Le rapport est écrit dans `reports/revue/revue-<branche>.md` (dossier non versionné).

Options utiles :

| Option | Usage |
|---|---|
| `--cible origin/develop` | MR qui vise une autre branche que `main` |
| `--repetitions 3` | exécute la suite 3 fois pour détecter les tests instables |
| `--sans-claude` | prépare seulement le contexte et les résultats de tests |
| `--sans-tests` | ne relance pas les tests (réutilise `reports/verification/resume.md`) |

Pour seulement vérifier le projet, sans revue : `bash scripts/verifier.sh` (code de sortie 0 = tout est vert).

## 3. Revue automatique sur chaque MR (GitLab CI)

1. Ajouter dans le `.gitlab-ci.yml` du projet :
   ```yaml
   include:
     - local: ci/gitlab-ci.revue.yml
   ```
2. Créer les variables CI/CD masquées listées en tête de `ci/gitlab-ci.revue.yml`
   (`ANTHROPIC_API_KEY`, `GITLAB_ACCESS_TOKEN`, identifiants de l'application).
3. Dans **Settings → Merge requests**, cocher « Pipelines must succeed » : le job `verification` devient bloquant.
4. À chaque MR : `verification` exécute lint et tests ; `revue-claude` publie le rapport en commentaire.

Points d'attention :
- Les runners doivent pouvoir joindre les sites testés, `claude.ai` (installation) et l'API Claude.
- L'image `mcr.microsoft.com/playwright/python` doit avoir la même version que `playwright` dans `requirements.txt`.
- L'accès à l'API Claude (clé d'API, Bedrock ou Vertex) est à valider avec l'administrateur Claude de l'organisation.

Sur **GitHub**, le service Code Review de Claude (offres Team / Enterprise) lit directement `REVIEW.md` et
`CLAUDE.md` : aucun job n'est nécessaire.

## 4. Lire un rapport

- **Verdict** : ✅ Approuvée / ⚠️ Approuvée avec réserves / ❌ Modifications demandées (règles dans `REVIEW.md` §3).
- **Section 2** : les tests exécutés et leur interprétation. Catégories : ❌ Échec (vérification),
  💥 Erreur (préparation), 🌐 Environnement (site injoignable, navigateur absent, `.env` manquant).
  Une catégorie 🌐 n'est **pas** un défaut du code : relancer dans un environnement correct.
- **Sections 3 à 7** : chaque remarque a un identifiant, un `fichier:ligne`, le constat, la raison et la correction.
- **Section 9** : plan d'action à cocher dans la MR.

La revue automatisée **ne remplace pas** la revue humaine : elle la prépare. Le relecteur humain valide
ou écarte chaque remarque et reste responsable de l'approbation.

## 5. Faire évoluer les règles

| Constat | Action |
|---|---|
| Claude signale souvent un point inutile | l'ajouter à « Ce qu'il ne faut PAS signaler » (`REVIEW.md` §4) |
| Un relecteur humain fait souvent la même remarque | en faire un critère (`REVIEW.md` §5) |
| Une règle peut être vérifiée par un outil | l'automatiser (règle `ruff`, contrôle dans `scripts/verifier.sh`) plutôt que de la confier à la revue |
| Le rapport manque d'une information | modifier `docs/revue/MODELE_RAPPORT_REVUE.md` |

Toute modification de ces fichiers passe par une MR relue. Sur GitHub, `REVIEW.md` n'est pris en compte
qu'une fois fusionné dans la branche par défaut.
