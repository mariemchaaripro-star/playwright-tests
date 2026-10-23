"""Configuration centralisée du projet.

Lit les variables d'environnement (fichier .env, puis .env.<TEST_ENV> qui le surcharge) et les
expose dans un objet unique `settings` : URL de l'application, URL de l'API, identifiants, etc.
Aucune URL ni aucun mot de passe ne doit être écrit en dur ailleurs dans le code :
on utilise toujours `from config.settings import settings`.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent

# Charge .env puis .env.<TEST_ENV> (ex : .env.staging) qui surcharge les valeurs
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / f".env.{os.getenv('TEST_ENV', 'dev')}", override=True)


def _get(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if not value:
        raise RuntimeError(f"Variable d'environnement manquante : {name}")
    return value


@dataclass(frozen=True)
class Settings:
    test_env: str = os.getenv("TEST_ENV", "dev")
    base_url: str = _get("BASE_URL", "https://www.saucedemo.com")
    api_url: str = _get("API_URL", "https://jsonplaceholder.typicode.com")
    standard_user: str = _get("STANDARD_USER", "standard_user")
    locked_user: str = _get("LOCKED_USER", "locked_out_user")
    password: str = _get("USER_PASSWORD", "secret_sauce")
    auth_file: Path = ROOT_DIR / "playwright" / ".auth" / "user.json"


settings = Settings()
