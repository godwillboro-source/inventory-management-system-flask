import pytest
import requests

import api_handler


# ---------- fakes ----------

class FakeResponse:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


def patch_get(monkeypatch, response=None, error=None):
    """Replace requests.get. Returns a list that records every call as (url, kwargs)."""
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        if error:
            raise error
        return response

    monkeypatch.setattr(api_handler.requests, "get", fake_get)
    return calls


NUTELLA = {"product_name": "Nutella", "brands": "Ferrero", "categories": "Spreads", "code": "3017620422003"}


# ---------- fetch_product_by_barcode ----------

def test_barcode_returns_product(monkeypatch):
    patch_get(monkeypatch, FakeResponse(200, {"status": 1, "product": NUTELLA}))
    assert api_handler.fetch_product_by_barcode("3017620422003") == {
        "product_name": "Nutella",
        "barcode": "3017620422003",
        "brands": "Ferrero",
        "categories": "Spreads",
    }


def test_barcode_uses_the_barcode_you_passed_in(monkeypatch):
    patch_get(monkeypatch, FakeResponse(200, {"status": 1, "product": {"product_name": "X"}}))
    assert api_handler.fetch_product_by_barcode("555")["barcode"] == "555"


def test_barcode_fills_in_missing_fields(monkeypatch):
    patch_get(monkeypatch, FakeResponse(200, {"status": 1, "product": {}}))
    product = api_handler.fetch_product_by_barcode("123")
    assert product["product_name"] == "Unknown"
    assert product["brands"] == "" and product["categories"] == ""


def test_barcode_sends_correct_request(monkeypatch):
    calls = patch_get(monkeypatch, FakeResponse(200, {"status": 1, "product": NUTELLA}))
    api_handler.fetch_product_by_barcode("123")
    url, kwargs = calls[0]
    assert url == f"{api_handler.BASE_URL}/product/123.json"
    assert kwargs["headers"] == api_handler.HEADERS
    assert kwargs["timeout"] == 5


def test_barcode_not_found_status_zero(monkeypatch):
    patch_get(monkeypatch, FakeResponse(200, {"status": 0}))
    assert api_handler.fetch_product_by_barcode("000") is None


def test_barcode_bad_http_status(monkeypatch):
    patch_get(monkeypatch, FakeResponse(500))
    assert api_handler.fetch_product_by_barcode("123") is None


@pytest.mark.parametrize("error", [
    requests.exceptions.ConnectionError(),
    requests.exceptions.Timeout(),
])
def test_barcode_network_error_returns_none(monkeypatch, error):
    patch_get(monkeypatch, error=error)
    assert api_handler.fetch_product_by_barcode("123") is None


# ---------- fetch_product_by_search ----------

def test_search_returns_first_product(monkeypatch):
    patch_get(monkeypatch, FakeResponse(200, {"products": [NUTELLA]}))
    assert api_handler.fetch_product_by_search("nutella") == {
        "product_name": "Nutella",
        "barcode": "3017620422003",   # the API calls it "code"
        "brands": "Ferrero",
        "categories": "Spreads",
    }


def test_search_only_uses_the_first_result(monkeypatch):
    second = {"product_name": "Other", "code": "999"}
    patch_get(monkeypatch, FakeResponse(200, {"products": [NUTELLA, second]}))
    assert api_handler.fetch_product_by_search("nutella")["product_name"] == "Nutella"


def test_search_fills_in_missing_fields(monkeypatch):
    patch_get(monkeypatch, FakeResponse(200, {"products": [{}]}))
    product = api_handler.fetch_product_by_search("anything")
    assert product == {"product_name": "Unknown", "barcode": "", "brands": "", "categories": ""}


def test_search_sends_correct_request(monkeypatch):
    calls = patch_get(monkeypatch, FakeResponse(200, {"products": [NUTELLA]}))
    api_handler.fetch_product_by_search("ben & jerry's")
    url, kwargs = calls[0]
    assert url == api_handler.SEARCH_URL
    assert kwargs["params"]["search_terms"] == "ben & jerry's"   # requests encodes it for us
    assert kwargs["params"]["page_size"] == 1
    assert kwargs["headers"] == api_handler.HEADERS
    assert kwargs["timeout"] == 10


def test_search_no_results(monkeypatch):
    patch_get(monkeypatch, FakeResponse(200, {"products": []}))
    assert api_handler.fetch_product_by_search("zzzz") is None


def test_search_missing_products_key(monkeypatch):
    patch_get(monkeypatch, FakeResponse(200, {}))
    assert api_handler.fetch_product_by_search("zzzz") is None


def test_search_bad_http_status(monkeypatch):
    patch_get(monkeypatch, FakeResponse(503))
    assert api_handler.fetch_product_by_search("nutella") is None


@pytest.mark.parametrize("error", [
    requests.exceptions.ConnectionError(),
    requests.exceptions.Timeout(),
])
def test_search_network_error_returns_none(monkeypatch, error):
    patch_get(monkeypatch, error=error)
    assert api_handler.fetch_product_by_search("nutella") is None