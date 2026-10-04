import requests

BASE_URL = "https://world.openfoodfacts.org/api/v2"
SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"

HEADERS = {"User-Agent": "InventoryManagementApp/1.0 (student project)"}


def fetch_product_by_barcode(barcode):
    url = f"{BASE_URL}/product/{barcode}.json"

    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
    except requests.exceptions.RequestException:
        return None

    if response.status_code != 200:
        return None

    data = response.json()
    if data.get("status") != 1:  # Product not found
        return None

    product = data.get("product", {})
    return {
        "product_name": product.get("product_name", "Unknown"),
        "barcode": barcode,
        "brands": product.get("brands", ""),
        "categories": product.get("categories", ""),
    }




def fetch_product_by_search(name):
    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 1,
    }

    try:
        response = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10)
    except requests.exceptions.RequestException:
        return None

    if response.status_code != 200:
        return None

    products = response.json().get("products", [])
    if not products:
        return None

    product = products[0]
    return {
        "product_name": product.get("product_name", "Unknown"),
        "barcode": product.get("code", ""),
        "brands": product.get("brands", ""),
        "categories": product.get("categories", ""),
    }
