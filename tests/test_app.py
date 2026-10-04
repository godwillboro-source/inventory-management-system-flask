import pytest

import app as backend

client = backend.app.test_client()


# ---------- setup helpers ----------

@pytest.fixture(autouse=True)
def clean_state():
    """Every test starts with an empty inventory and nobody logged in."""
    backend.inventory.clear()
    backend.current_user = None


def log_in():
    backend.current_user = "kim"   


def add_item(barcode="123", name="Milk", price=2.0, quantity=5):
    """Put an item straight into the inventory list."""
    item = {
        "id": len(backend.inventory) + 1, "product_name": name, "barcode": barcode,
        "Price": price, "Quantity": quantity, "brands": "Dairyco", "categories": "Dairy",
    }
    backend.inventory.append(item)
    return item



def test_get_all_items_when_empty():
    response = client.get("/inventory")
    assert response.status_code == 200
    assert response.get_json() == []


def test_get_all_items_works_without_login():
    add_item("123")
    add_item("456")
    response = client.get("/inventory")
    assert response.status_code == 200
    assert len(response.get_json()) == 2


def test_get_item_by_barcode():
    add_item("123", name="Milk")
    response = client.get("/inventory/123")
    assert response.status_code == 200
    assert response.get_json()["product_name"] == "Milk"


def test_get_item_not_found():
    response = client.get("/inventory/999")
    assert response.status_code == 404
    assert "error" in response.get_json()



def test_create_requires_login():
    response = client.post("/inventory", json={"barcode": "123"})
    assert response.status_code == 401
    assert backend.inventory == []


def test_create_item_success():
    log_in()
    payload = {"barcode": "123", "product_name": "Milk", "Price": 2.5, "Quantity": 4,
               "brands": "Dairyco", "categories": "Dairy"}
    response = client.post("/inventory", json=payload)
    item = response.get_json()
    assert response.status_code == 201
    assert item["product_name"] == "Milk" and item["Price"] == 2.5 and item["Quantity"] == 4
    assert len(backend.inventory) == 1


def test_create_item_uses_defaults():
    log_in()
    item = client.post("/inventory", json={"barcode": "123"}).get_json()
    assert item["Price"] == 0.0 and item["Quantity"] == 0
    assert item["brands"] == "" and item["categories"] == ""


def test_create_item_ids_increase():
    log_in()
    first = client.post("/inventory", json={"barcode": "1"}).get_json()
    second = client.post("/inventory", json={"barcode": "2"}).get_json()
    assert second["id"] == first["id"] + 1


def test_create_item_without_barcode_is_rejected():
    log_in()
    assert client.post("/inventory", json={"product_name": "Milk"}).status_code == 400
    assert client.post("/inventory", json={}).status_code == 400
    assert backend.inventory == []


def test_created_item_can_be_read_back():
    log_in()
    client.post("/inventory", json={"barcode": "123", "product_name": "Milk"})
    assert client.get("/inventory/123").get_json()["product_name"] == "Milk"



def test_update_requires_login():
    add_item("123")
    assert client.patch("/inventory/123", json={"Price": 9}).status_code == 401
    assert backend.inventory[0]["Price"] == 2.0


def test_update_item_not_found():
    log_in()
    assert client.patch("/inventory/999", json={"Price": 9}).status_code == 404


def test_update_changes_only_given_fields():
    log_in()
    add_item("123", name="Milk", price=2.0, quantity=5)
    response = client.patch("/inventory/123", json={"Price": 9.99})
    assert response.status_code == 200
    item = backend.inventory[0]
    assert item["Price"] == 9.99
    assert item["product_name"] == "Milk" and item["Quantity"] == 5


def test_update_can_change_several_fields():
    log_in()
    add_item("123")
    client.patch("/inventory/123", json={"product_name": "Oat Milk", "Quantity": 20, "brands": "Oatly"})
    item = backend.inventory[0]
    assert item["product_name"] == "Oat Milk" and item["Quantity"] == 20 and item["brands"] == "Oatly"


def test_update_ignores_fields_that_cannot_be_changed():
    log_in()
    add_item("123")
    client.patch("/inventory/123", json={"id": 99, "barcode": "changed"})
    assert backend.inventory[0]["id"] == 1
    assert backend.inventory[0]["barcode"] == "123"


def test_update_with_empty_body_is_rejected():
    log_in()
    add_item("123")
    assert client.patch("/inventory/123", json={}).status_code == 400



def test_delete_requires_login():
    add_item("123")
    assert client.delete("/inventory/123").status_code == 401
    assert len(backend.inventory) == 1


def test_delete_item_not_found():
    log_in()
    assert client.delete("/inventory/999").status_code == 404


def test_delete_item_success():
    log_in()
    add_item("123")
    response = client.delete("/inventory/123")
    assert response.status_code == 204
    assert backend.inventory == []


def test_delete_removes_only_that_item():
    log_in()
    add_item("123")
    add_item("456")
    client.delete("/inventory/123")
    assert [i["barcode"] for i in backend.inventory] == ["456"]
    assert client.get("/inventory/123").status_code == 404