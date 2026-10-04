
import cli


# ---------- fakes ----------

class FakeResponse:
    def __init__(self, status, data=None):
        self.status_code = status
        self._data = data

    def get_json(self, silent=False):
        return self._data


class FakeClient:
    """Stands in for Flask's test client and records the last request."""
    def __init__(self, status=200, data=None):
        self.status, self.data, self.last = status, data, None

    def get(self, path, **kwargs):
        self.last = ("get", path)
        return FakeResponse(self.status, self.data)


def feed(monkeypatch, *answers):
    """Pretend the user types these answers, in order."""
    typed = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(typed))


def set_user(monkeypatch, name):
    monkeypatch.setattr(cli.backend, "get_current_user", lambda: name)


# ---------- number() ----------

def test_number_blank_returns_none(monkeypatch):
    feed(monkeypatch, "")
    assert cli.number("Price: ", float) is None


def test_number_converts_valid_input(monkeypatch):
    feed(monkeypatch, "4.5")
    assert cli.number("Price: ", float) == 4.5


def test_number_asks_again_after_bad_input(monkeypatch):
    feed(monkeypatch, "abc", "7")
    assert cli.number("Quantity: ", int) == 7


# ---------- line() and path_for() ----------

def test_line_shows_item_details():
    item = {"id": 1, "product_name": "Milk", "barcode": "123", "brands": "Dairyco", "Price": 2.5, "Quantity": 4}
    text = cli.line(item)
    assert "Milk" in text and "123" in text and "2.5" in text


def test_line_handles_missing_fields():
    text = cli.line({"product_name": "Milk", "barcode": "1"})
    assert "price -" in text and "qty -" in text


def test_path_for_encodes_special_characters():
    assert cli.path_for("a/b") == "/inventory/a%2Fb"


# ---------- report() ----------

def test_report_login_required(capsys):
    cli.report(401, {"error": "Login required"})
    assert "log in" in capsys.readouterr().out.lower()


def test_report_shows_error_message(capsys):
    cli.report(404, {"error": "Item not found"})
    assert "Item not found" in capsys.readouterr().out


def test_report_lists_items(capsys):
    cli.report(200, [{"id": 1, "product_name": "Milk", "barcode": "1"}])
    assert "Milk" in capsys.readouterr().out


def test_report_empty_list(capsys):
    cli.report(200, [])
    assert "empty" in capsys.readouterr().out.lower()


def test_report_done_when_no_body(capsys):
    cli.report(204, None)
    assert "Done" in capsys.readouterr().out


# ---------- call() and exists() ----------

def test_call_returns_status_and_json(monkeypatch):
    monkeypatch.setattr(cli, "client", FakeClient(200, {"ok": True}))
    assert cli.call("get", "/inventory") == (200, {"ok": True})


def test_exists_true_when_found(monkeypatch):
    fake = FakeClient(200, {"barcode": "123"})
    monkeypatch.setattr(cli, "client", fake)
    assert cli.exists("123") is True
    assert fake.last == ("get", "/inventory/123")


def test_exists_false_when_missing(monkeypatch):
    monkeypatch.setattr(cli, "client", FakeClient(404, {"error": "Item not found"}))
    assert cli.exists("999") is False


# ---------- choose_action() ----------

def test_logged_out_menu_choice(monkeypatch):
    set_user(monkeypatch, None)
    feed(monkeypatch, "2")
    assert cli.choose_action() == "login"


def test_logged_in_menu_choice(monkeypatch):
    set_user(monkeypatch, "kim")
    feed(monkeypatch, "3")
    assert cli.choose_action() == "add"


def test_invalid_menu_choices_return_none(monkeypatch):
    set_user(monkeypatch, None)
    feed(monkeypatch, "99", "abc")
    assert cli.choose_action() is None
    assert cli.choose_action() is None


# ---------- main() ----------

def test_main_quits(monkeypatch, capsys):
    set_user(monkeypatch, None)
    feed(monkeypatch, "4")
    cli.main()
    assert "Goodbye" in capsys.readouterr().out


def test_main_lists_items(monkeypatch, capsys):
    set_user(monkeypatch, None)
    monkeypatch.setattr(cli, "client", FakeClient(200, [{"id": 1, "product_name": "Milk", "barcode": "1"}]))
    feed(monkeypatch, "3", "4")   # View all items, then Quit
    cli.main()
    assert "Milk" in capsys.readouterr().out