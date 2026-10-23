"""Tests E2E de la page catalogue.

Vérifient l'affichage des produits, l'ajout au panier et le tri par prix.
La connexion est déjà faite grâce à la fixture inventory_page (session réutilisée).
"""

import pytest
from playwright.sync_api import expect

from data import products
from pages.inventory_page import InventoryPage


@pytest.fixture(autouse=True)
def open_inventory(inventory_page: InventoryPage) -> None:
    # Session déjà ouverte via la fixture auth_state (pas de login UI à chaque test)
    inventory_page.goto()


@pytest.mark.smoke
def test_affiche_les_6_produits(inventory_page: InventoryPage) -> None:
    expect(inventory_page.items).to_have_count(6)


@pytest.mark.regression
def test_ajout_de_deux_produits_met_a_jour_le_panier(inventory_page: InventoryPage) -> None:
    inventory_page.add_to_cart(products.BACKPACK)
    inventory_page.add_to_cart(products.BIKE_LIGHT)

    expect(inventory_page.cart_badge).to_have_text("2")


@pytest.mark.regression
def test_tri_par_prix_croissant(inventory_page: InventoryPage) -> None:
    inventory_page.sort_by("lohi")

    prices = inventory_page.get_prices()
    assert prices == sorted(prices)
