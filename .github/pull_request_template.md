## Objectif
<!-- Ce que change cette MR, en une ou deux phrases, et pourquoi (ticket, bug, besoin). -->

## Comment vérifier
<!-- Commande(s) à lancer, ex. : pytest -v -k panier -->

## Liste de contrôle de l'auteur
- [ ] `bash scripts/verifier.sh` est vert en local (lint, collecte, tests)
- [ ] J'ai vu chaque nouveau test **échouer** au moins une fois (en cassant le comportement testé)
- [ ] Les sélecteurs sont dans `pages/`, les vérifications utilisent `expect(...)`, aucun `sleep`
- [ ] Aucun secret dans le code ; `.env.example` est à jour si j'ai ajouté une variable
- [ ] La documentation est à jour si une commande ou un comportement change
- [ ] La MR traite un seul sujet (idéalement moins de 300 lignes modifiées)

<!-- La revue automatisée (service Code Review de Claude ou commande `/revue-code`) publie son rapport en commentaire.
     Elle ne remplace pas la revue humaine : au moins une approbation est requise. -->
