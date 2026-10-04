import requests

BASE_URL = "https://world.openfoodfacts.org/api/v2"
HEADERS = {"User-Agent": "InventoryManagementApp/1.0 (student project)"}


def fetch_product_by_barcode(barcode):
    url = f"{BASE_URL}/product/{barcode}.json"
    response = requests.get(url, headers=HEADERS, timeout=5)

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
    url = f"{BASE_URL}/search?search_terms={name}&json=true"
    response = requests.get(url, headers=HEADERS, timeout=5)

    if response.status_code == 200:
        data = response.json()
        products = data.get("products", [])
        if products:
            product = products[0]
            return [
            {
                "product_name": product.get("product_name", "Unknown"),
                "barcode": product.get("code", ""),
                "brands": product.get("brands", ""),
                "categories": product.get("categories", ""),
            }
            
        ]
    return None


# Testing functions
print(fetch_product_by_search("milk"))
print(fetch_product_by_barcode("737628064502"))  