import re

import pytest
from playwright.sync_api import Page, expect

from config.settings import settings
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage
from utils.helpers import load_json

LOGIN_CASES = load_json("data/login_cases.json")


@pytest.fixture(autouse=True)
def open_login_page(login_page: LoginPage) -> None:
    login_page.goto()


@pytest.mark.smoke
def test_utilisateur_valide_accede_au_catalogue(login_page: LoginPage, page: Page) -> None:
    login_page.login(settings.standard_user, settings.password)

    InventoryPage(page).expect_loaded()


@pytest.mark.regression
def test_utilisateur_bloque_voit_une_erreur(login_page: LoginPage) -> None:
    login_page.login(settings.locked_user, settings.password)

    login_page.expect_error("Sorry, this user has been locked out")


# Data-driven : un test généré par ligne du fichier JSON
@pytest.mark.regression
@pytest.mark.parametrize("case", LOGIN_CASES, ids=[c["id"] for c in LOGIN_CASES])
def test_connexion_refusee(login_page: LoginPage, page: Page, case: dict) -> None:
    login_page.login(case["username"], case["password"])

    login_page.expect_error(case["error"])
    expect(page).not_to_have_url(re.compile("inventory"))
