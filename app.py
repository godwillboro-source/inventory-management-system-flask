from flask import Flask, render_template, request, jsonify, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from api_handler import fetch_product_by_barcode, fetch_product_by_search

app = Flask(__name__)

#in memory storage for users
users = []
#inventory storage for products
inventory = []
current_user = None
#------------------------------------------------------------------------
#Helper functions
#------------------------------------------------------------------------

def login_required_json():
    if current_user is None:
        return jsonify({"error": "Login required"}), 401
    return None

def find_item(barcode):
    """Find an item in the inventory by its barcode."""
    for item in inventory:
        if item["barcode"] == barcode:
            return item
    return None
#------------------------------------------------------------------------
#Authentication 
#------------------------------------------------------------------------
def register(username, password):
    username = username.strip()
    if not username or not password:
        return "Username and password are required"
    if any(u["username"] == username for u in users):
        return "Username already exists"
    users.append({
        "id": len(users) + 1,
        "username": username,
        "password_hash": generate_password_hash(password),
    })
    return "Registration successful. You can now log in."

def login(username, password):
    global current_user
    username = username.strip()
    user = next((u for u in users if u["username"] == username), None)
    if not user or not check_password_hash(user["password_hash"], password):
        return "Invalid username or password"
    current_user = username
    return "Login successful"

def logout():
    global current_user
    current_user = None
    return "Logged out successfully"

def get_current_user():
    return current_user
#------------------------------------------------------------------------
# CRUD routes
#------------------------------------------------------------------------
@app.route("/inventory", methods=["GET"])
def get_all_items():
    return jsonify(inventory), 200

@app.route("/inventory/<barcode>", methods=["GET"])
def get_item_by_barcode(barcode):
    item = find_item(barcode)
    if item:
        return jsonify(item), 200
    return jsonify({"error": "Item not found"}), 404

@app.route("/inventory", methods=["POST"])
# Add a new item to the inventory without fetching from OpenFoodFacts API

def add_item():
    auth_error = login_required_json()
    if auth_error:
        return auth_error
    data = request.get_json()
    if not data or "barcode" not in data:
        return jsonify({"error": "Invalid request"}), 400

    new_item = {
        "id": max([item["id"] for item in inventory], default=0) + 1,
        "product_name": data.get("product_name"),
        "barcode": data.get("barcode", ""),
        "Price": data.get("Price", 0.0),
        "Quantity": data.get("Quantity", 0),
        "brands": data.get("brands", ""),
        "categories": data.get("categories", ""),
    }
    inventory.append(new_item)
    return jsonify(new_item), 201

@app.route("/inventory/<barcode>", methods=["PATCH"])
def update_item(barcode):
    auth_error = login_required_json()
    if auth_error:
        return auth_error
    item = find_item(barcode)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    # Updating present fields only
    for key in ["product_name", "Price", "Quantity", "brands", "categories"]:
        if key in data:
            item[key] = data[key]

    return jsonify(item), 200

@app.route("/inventory/<barcode>", methods=["DELETE"])
def delete_item(barcode):
    auth_error = login_required_json()
    if auth_error:
        return auth_error
    item = find_item(barcode)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    inventory.remove(item)
    return jsonify({"message": "Item deleted"}), 204

@app.route("/inventory/search", methods=["GET"])
def search_item():
    auth_error = login_required_json()
    if auth_error:
        return auth_error
    
    barcode = request.args.get("barcode")
    name = request.args.get("name")
    if barcode:
        product = fetch_product_by_barcode(barcode)
    elif name:
        product = fetch_product_by_search(name)
    else:
        return jsonify({"error": "Barcode or name parameter is required"}), 400
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product), 200

@app.route("/inventory/import", methods=["POST"])
#import an item from OpenFoodFacts API using barcode or name
def import_item():
    auth_error = login_required_json()
    if auth_error:
        return auth_error
    
    barcode = request.args.get("barcode")
    name = request.args.get("name")

    if barcode:
        product = fetch_product_by_barcode(barcode)
    elif name:
        product = fetch_product_by_search(name)
    else:
        return jsonify({"error": "Barcode or name parameter is required"}), 400

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    new_item = {
        "id": max([item["id"] for item in inventory], default=0) + 1,
        "product_name": product.get("product_name"),
        "barcode": product.get("barcode", ""),
        "Price": product.get("Price", 0.0),
        "Quantity": product.get("Quantity", 0),
        "brands": product.get("brands", ""),
        "categories": product.get("categories", ""),
    }
    inventory.append(new_item)
    return jsonify(new_item), 201

if __name__ == "__main__":
    app.run(debug=True)