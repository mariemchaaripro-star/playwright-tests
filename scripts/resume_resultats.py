"""Résume un ou plusieurs rapports JUnit de pytest en Markdown, pour un humain et pour la revue.

- Compte les tests réussis, en échec, en erreur, ignorés.
- Classe chaque problème : ÉCHEC (une vérification a échoué), ERREUR (préparation ou nettoyage
  en échec) ou ENVIRONNEMENT (site injoignable, navigateur absent, configuration manquante :
  pas un défaut du code).
- Donne l'emplacement dans le projet (fichier:ligne du test et de l'origine de l'erreur).
- Avec plusieurs rapports (scripts/verifier.sh --repetitions N), signale les tests instables.

Usage : python scripts/resume_resultats.py reports/verification/junit-1.xml [junit-2.xml ...]
Code de sortie : 0 si tous les tests du dernier rapport ont réussi, 1 sinon, 2 si aucun rapport.
"""

import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

# Motif -> cause lisible. Un problème qui correspond à l'un d'eux est classé ENVIRONNEMENT.
CAUSES_ENVIRONNEMENT = {
    r"ERR_TUNNEL_CONNECTION_FAILED|ERR_PROXY_CONNECTION_FAILED": "site injoignable (proxy)",
    r"ERR_NAME_NOT_RESOLVED|ENOTFOUND|getaddrinfo": "site injoignable (nom de domaine non résolu)",
    r"ERR_CONNECTION_REFUSED|ECONNREFUSED": "site injoignable (connexion refusée)",
    r"ERR_INTERNET_DISCONNECTED|ERR_NETWORK_CHANGED": "pas de connexion réseau",
    r"ERR_CONNECTION_TIMED_OUT|ETIMEDOUT": "site injoignable (délai de connexion dépassé)",
    r"Executable doesn't exist": "navigateur Playwright non installé (playwright install)",
    r"Variable d'environnement manquante": "configuration manquante (.env)",
}
# Emplacement d'un cadre de pile appartenant au projet (et non à une bibliothèque).
CADRE_PROJET = re.compile(r"^((?:tests|pages|config|data|utils)/[\w/.-]+\.py):(\d+)", re.MULTILINE)


@dataclass
class Resultat:
    identifiant: str
    statut: str  # REUSSI, ECHEC, ERREUR, IGNORE, ENVIRONNEMENT
    message: str = ""
    cause: str = ""
    emplacement_test: str = ""
    origine: str = ""


def identifiant(cas: ET.Element) -> str:
    chemin = cas.get("classname", "").replace(".", "/")
    return f"{chemin}.py::{cas.get('name', '?')}" if chemin else cas.get("name", "?")


def analyser_cas(cas: ET.Element) -> Resultat:
    ident = identifiant(cas)
    probleme = cas.find("failure")
    statut = "ECHEC"
    if probleme is None:
        probleme = cas.find("error")
        statut = "ERREUR"
    if probleme is None:
        statut = "IGNORE" if cas.find("skipped") is not None else "REUSSI"
        return Resultat(ident, statut)

    texte = f"{probleme.get('message', '')}\n{probleme.text or ''}"
    message = next((ligne.strip() for ligne in texte.splitlines() if ligne.strip()), "")
    cadres = CADRE_PROJET.findall(probleme.text or "")
    resultat = Resultat(
        ident,
        statut,
        message=message[:220],
        emplacement_test=next((f"{f}:{n}" for f, n in cadres if f.startswith("tests/")), ""),
        origine=f"{cadres[-1][0]}:{cadres[-1][1]}" if cadres else "",
    )
    for motif, cause in CAUSES_ENVIRONNEMENT.items():
        if re.search(motif, texte):
            resultat.statut, resultat.cause = "ENVIRONNEMENT", cause
            break
    return resultat


def lire(fichier: Path) -> list[Resultat]:
    racine = ET.parse(fichier).getroot()
    return [analyser_cas(cas) for cas in racine.iter("testcase")]


def tableau_problemes(resultats: list[Resultat]) -> list[str]:
    lignes = [
        "| # | Test | Catégorie | Emplacement (test → origine) | Message |",
        "|---|---|---|---|---|",
    ]
    libelles = {"ECHEC": "❌ Échec", "ERREUR": "💥 Erreur", "ENVIRONNEMENT": "🌐 Environnement"}
    for numero, r in enumerate(resultats, 1):
        # dict.fromkeys : ne pas répéter l'emplacement quand le test est lui-même l'origine
        emplacements = dict.fromkeys(e for e in (r.emplacement_test, r.origine) if e)
        emplacement = " → ".join(emplacements) or "préparation du test (fixture)"
        categorie = libelles[r.statut] + (f" ({r.cause})" if r.cause else "")
        message = r.message.replace("|", "\\|").replace("`", "'")
        lignes.append(
            f"| {numero} | `{r.identifiant}` | {categorie} | `{emplacement}` | {message} |"
        )
    return lignes


def main(fichiers: list[str]) -> int:
    executions = []
    for nom in fichiers:
        try:
            executions.append(lire(Path(nom)))
        except (OSError, ET.ParseError) as erreur:
            print(f"⚠️ Rapport illisible : {nom} ({erreur})")
    if not executions:
        print("## Exécution des tests\n")
        print(
            "❌ **Les tests n'ont pas démarré** : pytest s'est arrêté avant le premier test "
            "(erreur d'import ou de configuration). "
            "Voir le journal « Exécution des tests » ci-dessus."
        )
        return 2

    dernier = executions[-1]
    compte = Counter(r.statut for r in dernier)
    problemes = [r for r in dernier if r.statut in ("ECHEC", "ERREUR", "ENVIRONNEMENT")]

    print("## Exécution des tests\n")
    if len(executions) > 1:
        print(f"Suite exécutée {len(executions)} fois ; chiffres de la dernière exécution.\n")
    print("| Indicateur | Nombre |\n|---|---|")
    print(f"| Tests exécutés | {len(dernier)} |")
    print(f"| ✅ Réussis | {compte['REUSSI']} |")
    print(f"| ❌ Échecs (vérification en échec) | {compte['ECHEC']} |")
    print(f"| 💥 Erreurs (préparation / nettoyage) | {compte['ERREUR']} |")
    print(f"| 🌐 Non concluants (environnement) | {compte['ENVIRONNEMENT']} |")
    print(f"| ⏭️ Ignorés | {compte['IGNORE']} |\n")

    if not problemes:
        print("**Verdict : ✅ tous les tests exécutés ont réussi.**")
    elif all(r.statut == "ENVIRONNEMENT" for r in problemes):
        causes = sorted({r.cause for r in problemes})
        print(
            f"**Verdict : ⚠️ non concluant.** {len(problemes)} test(s) n'ont pas pu "
            f"s'exécuter pour une raison d'environnement ({', '.join(causes)}). "
            "Ce ne sont pas des défauts du code : relancer dans un environnement "
            "qui accède aux sites testés."
        )
    else:
        defauts = sum(1 for r in problemes if r.statut != "ENVIRONNEMENT")
        print(f"**Verdict : ❌ {defauts} test(s) en échec ou en erreur à analyser.**")

    if problemes:
        print("\n### Détail des tests en échec ou non concluants\n")
        print("\n".join(tableau_problemes(problemes)))

    if len(executions) > 1:
        historique = defaultdict(list)
        for execution in executions:
            for r in execution:
                historique[r.identifiant].append(r.statut)
        instables = {i: s for i, s in historique.items() if len(set(s)) > 1}
        print("\n### Stabilité\n")
        if instables:
            print(
                f"⚠️ {len(instables)} test(s) instable(s) "
                "(résultat différent d'une exécution à l'autre) :\n"
            )
            for ident, statuts in sorted(instables.items()):
                print(f"- `{ident}` : {' → '.join(statuts)}")
        else:
            print(f"✅ Aucun test instable sur {len(executions)} exécutions.")

    return 0 if not problemes else 1


if __name__ == "__main__":
    if any(option in sys.argv[1:] for option in ("-h", "--help")):
        print(__doc__)
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))
