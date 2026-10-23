"""Classe parente de tous les Page Objects.

Contient ce qui est commun à toutes les pages : la référence vers l'objet `page` de Playwright
et la navigation vers l'URL de la page (`goto`). Chaque page fille définit son `path`.
"""

from playwright.sync_api import Page


class BasePage:
    path = "/"

    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self) -> None:
        self.page.goto(self.path)
