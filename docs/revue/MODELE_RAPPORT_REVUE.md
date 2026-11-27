# Modèle de rapport de revue de code

Ce modèle est **obligatoire** pour toute revue (Claude ou humaine). Les sections sont toutes présentes ;
une section sans contenu indique « Aucun point. ». Les remarques suivent les règles de `REVIEW.md`.

---

```markdown
# Revue de code — <titre ou branche de la MR>

| Élément | Valeur |
|---|---|
| Branche source | `<branche>` (`<sha court>`) |
| Branche cible | `<branche>` (`<sha court>`) |
| Commits relus | <n> |
| Fichiers modifiés | <n> (+<ajouts> / -<suppressions>) |
| Date de la revue | <AAAA-MM-JJ> |
| Relecteur | <Claude (revue automatisée) / nom> |
| **Verdict** | ✅ Approuvée / ⚠️ Approuvée avec réserves / ❌ Modifications demandées |

## 1. Synthèse

<3 à 6 phrases : objectif de la MR, appréciation générale, principaux risques, ce qui conditionne la fusion.>

| Gravité | Nombre |
|---|---|
| 🔴 Bloquant | <n> |
| 🟠 Majeur | <n> |
| 🟡 Mineur | <n> |
| 💡 Suggestion | <n> |
| ❓ Question | <n> |

## 2. Vérifications automatiques et tests exécutés

<Reprendre le tableau des contrôles de reports/revue/contexte/verification.md : lint, format, collecte,
connectivité, exécution des tests, stabilité.>

| Contrôle | Statut | Détail |
|---|---|---|
| ... | ✅ / ❌ / ⚠️ | ... |

**Interprétation :** <ce que les résultats prouvent et ne prouvent pas. Distinguer clairement :
échec causé par la MR / échec préexistant / test non exécutable à cause de l'environnement.
Ne jamais présenter un test non exécuté comme réussi.>

## 3. Anomalies détectées

<Bugs, régressions, tests qui ne vérifient rien, erreurs de logique. Une sous-section par remarque.>

### A1 — 🔴 Bloquant — <titre court>
- **Fichier :** `chemin/fichier.py:ligne`
- **Constat :**
  ```python
  <extrait de code concerné>
  ```
- **Pourquoi c'est un problème :** <conséquence concrète>
- **Correction recommandée :**
  ```python
  <code corrigé ou démarche précise>
  ```

## 4. Problèmes de conception et mauvaises pratiques

<Architecture, SOLID, DRY, fiabilité des tests, sélecteurs, gestion des exceptions, maintenabilité.
Même format, identifiants C1, C2…>

## 5. Risques de sécurité

<Identifiants S1, S2… Même format. Indiquer l'exploitation possible et l'impact.>

## 6. Risques de performance et de coût d'exécution

<Identifiants P1, P2… Même format. Quantifier si possible (temps, nombre de connexions, requêtes).>

## 7. Hors périmètre de la MR (dette existante)

<Problèmes Bloquants ou Majeurs dans le code existant des fichiers touchés, non introduits par la MR.
Identifiants H1, H2… Recommander un ticket séparé.>

## 8. Points positifs

<Ce qui est bien fait et doit être conservé ou généralisé.>

## 9. Plan d'action

<Liste ordonnée par priorité, une case par correction, avec l'identifiant de la remarque.>

- [ ] A1 — <action>
- [ ] C1 — <action>

## 10. Questions à l'auteur

<Questions ouvertes (❓), ou « Aucune. ».>
```
