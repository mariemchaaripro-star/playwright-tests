"""Vérifie que les environnements testés (BASE_URL, API_URL) sont joignables avant les tests.

Sert à distinguer immédiatement « le site est injoignable » (problème d'environnement : réseau,
proxy, VPN, site arrêté) de « un test échoue » (problème de code). Toute réponse HTTP, même une
erreur 4xx/5xx, prouve que le site est joignable. Code de sortie : 0 si tout est joignable, 1 sinon.
"""

import sys
import urllib.error
import urllib.request
from pathlib import Path

# Permet « python scripts/connectivite.py » depuis la racine : config/ doit être importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DELAI_SECONDES = 15


def tester(nom: str, url: str) -> bool:
    entetes = {"User-Agent": "verification-tests"}
    requete = urllib.request.Request(url, method="GET", headers=entetes)
    try:
        with urllib.request.urlopen(requete, timeout=DELAI_SECONDES) as reponse:
            print(f"OK          {nom:<8} {url} (HTTP {reponse.status})")
    except urllib.error.HTTPError as erreur:
        print(f"OK          {nom:<8} {url} (HTTP {erreur.code} : le serveur répond)")
    except (urllib.error.URLError, TimeoutError, OSError) as erreur:
        raison = getattr(erreur, "reason", erreur)
        print(f"INJOIGNABLE {nom:<8} {url} : {raison}")
        return False
    return True


def main() -> int:
    try:
        from config.settings import settings
    except RuntimeError as erreur:  # variable d'environnement manquante (config/settings.py)
        print(f"CONFIGURATION INVALIDE : {erreur}")
        return 1

    cibles = {"UI": settings.base_url, "API": settings.api_url}
    resultats = [tester(nom, url) for nom, url in cibles.items()]
    if not all(resultats):
        print(
            "→ Les tests qui utilisent un environnement injoignable échoueront pour une raison "
            "d'environnement (réseau, proxy, VPN), pas à cause du code."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
