---
name: revue-code
description: Revue de code de niveau senior de la branche courante (MR/PR) par rapport à sa branche cible, avec exécution des tests automatisés et rapport structuré selon REVIEW.md. À utiliser quand on demande une revue de code, de MR ou de PR sur ce projet.
argument-hint: "[branche-cible] (par défaut : origin/main)"
---

Réalise une revue de code de la branche courante. **Ne modifie aucun fichier du projet** (seul `reports/` est écrit)
et ne corrige rien sans demande explicite de l'utilisateur.

1. **Branche cible :** utilise celle indiquée par l'utilisateur ($ARGUMENTS) ; à défaut, `origin/main`.
2. **Préparer le contexte et exécuter les vérifications** (lint, collecte, connectivité, tous les tests) :
   ```bash
   bash scripts/revue_mr.sh --cible <branche-cible> --sans-claude
   ```
   La commande écrit `reports/revue/contexte/` (infos, diff, résultats de vérification).
   Une vérification en échec ne stoppe pas la revue : elle en fait partie.
3. **Analyser** en suivant intégralement `.claude/prompts/revue-mr.md` (passes 1 à 5), avec les règles de `REVIEW.md`.
4. **Écrire le rapport** au format `docs/revue/MODELE_RAPPORT_REVUE.md` dans
   `reports/revue/revue-<nom-de-branche>.md`.
5. **Répondre** à l'utilisateur avec : le verdict, le tableau des gravités, les remarques Bloquantes et Majeures
   en une ligne chacune, le résultat des tests, et le chemin du rapport complet.
