import getpass
from urllib.parse import quote

import app as backend

client = backend.app.test_client()

LOGGED_OUT_MENU = [
    ("Register", "register"),
    ("Log in", "login"),
    ("View all items", "list"),
    ("Quit", "quit"),
]
LOGGED_IN_MENU = [
    ("View all items", "list"),
    ("Find item by barcode", "find"),
    ("Add item", "add"),
    ("Search online", "search"),
    ("Import from online", "import"),
    ("Update item", "update"),
    ("Delete item", "delete"),
    ("Log out", "logout"),
    ("Quit", "quit"),
]


def call(method, path, **kwargs):
    """Call a Flask route and return (status_code, json)."""
    r = getattr(client, method)(path, **kwargs)
    return r.status_code, r.get_json(silent=True)


def path_for(barcode):
    return f"/inventory/{quote(barcode, safe='')}"


def exists(barcode):
    return call("get", path_for(barcode))[0] == 200


def line(item):
    return (f"{item.get('id', '-')}. {item.get('product_name')} | barcode {item.get('barcode')} | "
            f"{item.get('brands') or '-'} | price {item.get('Price', '-')} | qty {item.get('Quantity', '-')}")


def report(status, data):
    """Print the result of a route call."""
    if status == 401:
        print("Please log in first.")
    elif status >= 400:
        print((data or {}).get("error", f"Error {status}"))
    elif isinstance(data, list):
        print("\n".join(line(i) for i in data) or "Inventory is empty.")
    elif data and "product_name" in data:
        print(line(data))
    else:
        print("Done.")


def number(prompt, cast):
    """Ask for a number; blank returns None."""
    while True:
        raw = input(prompt).strip()
        if not raw:
            return None
        try:
            return cast(raw)
        except ValueError:
            print("Please enter a valid number.")


def choose_action():
    """Show the menu for the current state (logged in or out) and return the chosen action."""
    user = backend.get_current_user()
    options = LOGGED_IN_MENU if user else LOGGED_OUT_MENU
    print(f"\n=== Logged in as {user} ===" if user else "\n=== Welcome (not logged in) ===")
    for number_, (label, _) in enumerate(options, start=1):
        print(f"{number_}) {label}")
    choice = input("> ").strip()
    if not choice.isdigit() or not 1 <= int(choice) <= len(options):
        print("Invalid choice.")
        return None
    return options[int(choice) - 1][1]


def main():
    try:
        while True:
            action = choose_action()

            if action == "quit":
                break
            elif action == "register":
                print(backend.register(input("Username: "), getpass.getpass("Password: ")))
            elif action == "login":
                print(backend.login(input("Username: "), getpass.getpass("Password: ")))
            elif action == "logout":
                print(backend.logout())
            elif action == "list":
                report(*call("get", "/inventory"))
            elif action == "find":
                report(*call("get", path_for(input("Barcode: ").strip())))
            elif action == "add":
                barcode = input("Barcode: ").strip()
                if not barcode:
                    print("Barcode is required.")
                elif exists(barcode):
                    print("That barcode already exists.")
                else:
                    item = {
                        "barcode": barcode,
                        "product_name": input("Name: ").strip(),
                        "brands": input("Brand (optional): ").strip(),
                        "Price": number("Price: ", float) or 0.0,
                        "Quantity": number("Quantity: ", int) or 0,
                    }
                    report(*call("post", "/inventory", json=item))
            elif action in ("search", "import"):
                query = input("Barcode or name: ").strip()
                key = "barcode" if query.isdigit() else "name"
                if action == "search":
                    report(*call("get", "/inventory/search", query_string={key: query}))
                elif key == "barcode" and exists(query):
                    print("That barcode already exists.")
                else:
                    report(*call("post", "/inventory/import", query_string={key: query}))
            elif action == "update":
                barcode = input("Barcode of item to update: ").strip()
                print("Leave blank to keep the current value.")
                changes = {
                    "product_name": input("New name: ").strip(),
                    "Price": number("New price: ", float),
                    "Quantity": number("New quantity: ", int),
                }
                changes = {k: v for k, v in changes.items() if v not in ("", None)}
                if changes:
                    report(*call("patch", path_for(barcode), json=changes))
                else:
                    print("Nothing to update.")
            elif action == "delete":
                report(*call("delete", path_for(input("Barcode: ").strip())))
    except (KeyboardInterrupt, EOFError):
        pass
    print("\nGoodbye!")


if __name__ == "__main__":
    main()