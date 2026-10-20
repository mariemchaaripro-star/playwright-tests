from playwright.sync_api import Page


class BasePage:
    path = "/"

    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self) -> None:
        self.page.goto(self.path)
