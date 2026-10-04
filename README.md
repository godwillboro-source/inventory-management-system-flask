# Inventory Management System

A small inventory manager built with Flask. It has:

- Flask routes for adding, viewing, updating and deleting inventory items
- login and registration with hashed passwords
- product lookup through the OpenFoodFacts API, by barcode or name
- a menu-driven CLI (`cli.py`)
- pytest tests (external calls are mocked, so no internet is needed)

Data is stored in Python lists, so it resets when the program closes.

## Project structure

```
inventory-management-system-flask/
├── app.py              # Flask routes + login/register functions
├── api_handler.py      # OpenFoodFacts API functions
├── cli.py              # command line interface
├── pytest.ini          # lets pytest find the project files
└── tests/
    ├── test_app.py
    ├── test_cli.py
    └── test_api_handler.py
```

## Installation

```bash
git clone https://github.com/godwillboro-source/inventory-management-system-flask.git
cd inventory-management-system-flask
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install flask requests pytest
```

## Running
- Run on two separate terminals
```bash
python app.py
```

```bash
python cli.py
```

## Authentication

Register, login and logout are plain functions in `app.py`. Only one user can be logged in at a time. Viewing items is open to everyone, but adding, updating, deleting, searching and importing require a login.

## Item format

Items are looked up by barcode. Product detail fields match OpenFoodFacts.

```json
{
  "id": 1,
  "barcode": "3017620422003",
  "product_name": "Nutella",
  "brands": "Ferrero",
  "categories": "Spreads",
  "Price": 5.99,
  "Quantity": 10
}
```

## API endpoints

| Method | Route | Login | Input | Output |
|--------|-------|-------|-------|--------|
| GET | `/inventory` | no | – | list of items (200) |
| GET | `/inventory/<barcode>` | no | – | one item (200) or 404 |
| POST | `/inventory` | yes | JSON: `barcode` required; other fields optional | new item (201) or 400 |
| PATCH | `/inventory/<barcode>` | yes | JSON with any of `product_name`, `Price`, `Quantity`, `brands`, `categories` | updated item (200), 400 or 404 |
| DELETE | `/inventory/<barcode>` | yes | – | empty reply (204) or 404 |
| GET | `/inventory/search?barcode=` or `?name=` | yes | query parameter | product found online (200), 400 or 404 |
| POST | `/inventory/import?barcode=` or `?name=` | yes | query parameter | new item (201), 400 or 404 |

Errors look like `{"error": "message"}`. Protected routes return `401` if you are not logged in. Imported items start with price 0 and quantity 0.

## CLI menus

The menu depends on whether you are logged in.

- **Logged out:** Register, Log in, View all items, Quit
- **Logged in:** View all items, Find item by barcode, Add item, Search online, Import from online, Update item, Delete item, Log out, Quit

For search and import, typing only digits is treated as a barcode, and anything else as a product name. The CLI refuses to add an item whose barcode already exists.

## Testing

```bash
pytest -v
```

`pytest.ini` adds the project folder to Python's search path so the tests in `tests/` can import the project files. The OpenFoodFacts requests are replaced with fakes.

- `test_app.py`: login functions and every route
- `test_cli.py`: the CLI's helpers and menus
- `test_api_handler.py`: the OpenFoodFacts functions

## Notes

- Data resets every time the program closes.
- Duplicate barcodes are blocked by the CLI, not by the routes.