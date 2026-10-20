"""Fixtures partagées : configuration Playwright, authentification, Page Objects, client API."""

from collections.abc import Callable, Generator

import pytest
from playwright.sync_api import (
    APIRequestContext,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)

from config.settings import settings
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage


# ---------- Configuration ----------
@pytest.fixture(scope="session")
def base_url() -> str:
    return settings.base_url


@pytest.fixture(scope="session", autouse=True)
def _test_id_attribute(playwright: Playwright) -> None:
    # get_by_test_id() cible l'attribut data-test utilisé par l'application
    playwright.selectors.set_test_id_attribute("data-test")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    return {**browser_context_args, "viewport": {"width": 1280, "height": 800}}


# ---------- Authentification ----------
@pytest.fixture(scope="session")
def auth_state(browser: Browser, browser_context_args: dict) -> str:
    """Connexion UNE seule fois par session, l'état (cookies/storage) est sauvegardé."""
    context = browser.new_context(**browser_context_args)
    page = context.new_page()
    login_page = LoginPage(page)
    login_page.goto()
    login_page.login(settings.standard_user, settings.password)
    InventoryPage(page).expect_loaded()

    settings.auth_file.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=settings.auth_file)
    context.close()
    return str(settings.auth_file)


@pytest.fixture
def auth_page(new_context: Callable[..., BrowserContext], auth_state: str) -> Page:
    """Page déjà connectée (screenshots/vidéos/traces gérés par pytest-playwright)."""
    context = new_context(storage_state=auth_state)
    return context.new_page()


# ---------- Page Objects ----------
@pytest.fixture
def login_page(page: Page) -> LoginPage:
    """Page NON connectée."""
    return LoginPage(page)


@pytest.fixture
def inventory_page(auth_page: Page) -> InventoryPage:
    return InventoryPage(auth_page)


# ---------- API ----------
@pytest.fixture(scope="session")
def api(playwright: Playwright) -> Generator[APIRequestContext, None, None]:
    context = playwright.request.new_context(
        base_url=settings.api_url,
        extra_http_headers={"Accept": "application/json"},
    )
    yield context
    context.dispose()
