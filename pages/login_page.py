"""Page Object de la page de connexion.

Regroupe les sélecteurs (champs identifiant / mot de passe, bouton, message d'erreur) et les
actions de la page (`login`, `expect_error`). Si l'interface change, seul ce fichier est à modifier.
"""

import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.username_input = page.get_by_test_id("username")
        self.password_input = page.get_by_test_id("password")
        self.login_button = page.get_by_test_id("login-button")
        self.error_message = page.get_by_test_id("error")

    def login(self, username: str, password: str) -> None:
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def expect_error(self, message: str | re.Pattern[str]) -> None:
        expect(self.error_message).to_contain_text(message)
