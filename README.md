# цИфИрки (Digits game)

A puzzle game: cross out pairs of digits that are either the same or sum to 10. Pairs must be adjacent horizontally or vertically with no other active digits between them.

## Web version (Django)

### Setup and run

```bash
pip install -r requirements.txt
python manage.py runserver
```

Open **http://127.0.0.1:8000/** in your browser.

### How to play (web)

1. Click a digit to select it (it turns green).
2. Click another digit to try to cross the pair out. Valid pairs: same digit or digits that sum to 10, and they must be adjacent (or connected by already crossed-out cells).
3. Use the menu: **Начать заново** (start over), **Продолжить** (remove full rows and continue), **Проверить, есть ли что зачеркнуть**, **Отменить последнее зачеркивание** (undo last pair).

---

## Desktop version (tkinter)

```bash
python main.py
```

- Python 3.10+
- tkinter (included with Python on Windows/macOS; on Linux you may need `python3-tk`)
