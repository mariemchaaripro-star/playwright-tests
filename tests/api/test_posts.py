"""Tests d'API du endpoint /posts (sans navigateur).

Vérifient les codes HTTP et le contenu des réponses en lecture (GET), création (POST)
et pour une ressource inexistante (404). Tous ces tests portent le marker `api`.
"""

import pytest
from playwright.sync_api import APIRequestContext

from utils.helpers import unique_id

pytestmark = pytest.mark.api


@pytest.mark.smoke
def test_get_post_renvoie_un_article(api: APIRequestContext) -> None:
    response = api.get("/posts/1")

    assert response.status == 200
    body = response.json()
    assert body["id"] == 1
    assert isinstance(body["title"], str)


@pytest.mark.regression
def test_post_cree_un_article(api: APIRequestContext) -> None:
    payload = {"title": unique_id("post"), "body": "contenu", "userId": 1}

    response = api.post("/posts", data=payload)

    assert response.status == 201
    assert payload.items() <= response.json().items()


@pytest.mark.regression
def test_ressource_inexistante_renvoie_404(api: APIRequestContext) -> None:
    response = api.get("/posts/999999")

    assert response.status == 404
