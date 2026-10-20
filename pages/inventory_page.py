import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class InventoryPage(BasePage):
    path = "/inventory.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.title = page.get_by_test_id("title")
        self.items = page.get_by_test_id("inventory-item")
        self.cart_badge = page.get_by_test_id("shopping-cart-badge")
        self.sort_select = page.get_by_test_id("product-sort-container")

    def expect_loaded(self) -> None:
        expect(self.page).to_have_url(re.compile(r"inventory\.html"))
        expect(self.title).to_have_text("Products")

    def add_to_cart(self, product_name: str) -> None:
        self.items.filter(has_text=product_name).get_by_role("button", name="Add to cart").click()

    def sort_by(self, option: str) -> None:
        """option : 'az', 'za', 'lohi' ou 'hilo'."""
        self.sort_select.select_option(option)

    def get_prices(self) -> list[float]:
        texts = self.page.get_by_test_id("inventory-item-price").all_text_contents()
        return [float(t.replace("$", "")) for t in texts]
