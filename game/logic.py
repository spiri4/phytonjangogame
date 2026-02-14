"""
Game logic for цИфИрки (Digits) — ported from tkinter main.py.
State: texts (list of cell labels), clicked (list of '0'|'1'|'2'), cancel_indices.
"""
from itertools import combinations

DEFAULT_TEXTS = [
    "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "1", "1", "1", "2", "1", "3", "1", "4", "1",
    "5", "1", "6", "1", "7", "1", "8", "1", "9",
]


def check_nearest_index(clicked: list, index1: int, index2: int) -> bool:
    """True if indices are adjacent or connected by disabled cells only."""
    if index2 - index1 == 1 or (index2 - index1) / 9 == 1:
        return True
    if (index2 - index1) % 9 == 0:  # same column
        for k in range(index1 + 9, index2, 9):
            if clicked[k] != '2':
                return False
        return True
    # same row
    for p in range(index1 + 1, index2, 1):
        if clicked[p] != '2':
            return False
    return True


def check_win(clicked: list) -> bool:
    return all(c == '2' for c in clicked)


def check_row_empty(clicked: list, row_start: int) -> bool:
    """Row is from row_start to row_start+8 (9 cells)."""
    for f in range(row_start, min(row_start + 9, len(clicked))):
        if clicked[f] != '2':
            return False
    return True


def try_strike(texts: list, clicked: list, cancel_indices: list, i0: int, i1: int) -> tuple:
    """
    Try to cross out pair at i0, i1. Returns (new_texts, new_clicked, new_cancel_indices, success, message).
    """
    texts = list(texts)
    clicked = list(clicked)
    cancel_indices = [list(c) for c in cancel_indices]

    if i0 > i1:
        i0, i1 = i1, i0

    try:
        v0 = int(texts[i0])
        v1 = int(texts[i1])
    except (ValueError, IndexError):
        return texts, clicked, cancel_indices, False, "Выберите две цифры."

    if not (v0 == v1 or v0 + v1 == 10):
        return texts, clicked, cancel_indices, False, "Зачеркивать можно либо одинаковые цифры, либо дающие в сумме 10."

    if not check_nearest_index(clicked, i0, i1):
        return texts, clicked, cancel_indices, False, "Цифры должны быть рядом по горизонтали или вертикали (без других активных между ними)."

    # Apply strike — store this pair for undo
    cancel_indices[0] = [i0, texts[i0]]
    cancel_indices[1] = [i1, texts[i1]]

    clicked[i0] = '2'
    clicked[i1] = '2'
    texts[i0] = '0'
    texts[i1] = '0'

    return texts, clicked, cancel_indices, True, "Пара зачеркнута."


def do_continue(texts: list, clicked: list) -> tuple:
    """Remove full rows of crossed-out cells; then new board = remaining + active cell texts."""
    texts = list(texts)
    clicked = list(clicked)
    n = len(texts)
    if n < 9:
        return texts, clicked

    row_count = n // 9
    for r in range(row_count - 1, -1, -1):
        start = r * 9
        if check_row_empty(clicked, start):
            del texts[start:start + 9]
            del clicked[start:start + 9]

    if not texts:
        return list(DEFAULT_TEXTS), ['0'] * len(DEFAULT_TEXTS)

    active_texts = [texts[i] for i in range(len(clicked)) if clicked[i] != '2']
    new_texts = texts + active_texts
    new_clicked = list(clicked) + ['0'] * len(active_texts)
    return new_texts, new_clicked


def find_removable_pair(texts: list, clicked: list) -> list:
    """Return [i, j] if a valid pair exists, else []."""
    active = [i for i in range(len(clicked)) if clicked[i] != '2']
    for i_idx, j_idx in combinations(active, 2):
        try:
            vi = int(texts[i_idx])
            vj = int(texts[j_idx])
        except (ValueError, IndexError):
            continue
        if (vi == vj or vi + vj == 10) and check_nearest_index(clicked, i_idx, j_idx):
            return [i_idx, j_idx]
    return []


def undo_last_strike(texts: list, clicked: list, cancel_indices: list) -> tuple:
    """Restore last two crossed cells. Returns (new_texts, new_clicked, new_cancel_indices, success, message)."""
    texts = list(texts)
    clicked = list(clicked)
    cancel_indices = [list(c) for c in cancel_indices]
    if not cancel_indices or cancel_indices[0] == [-1, ''] or cancel_indices[1] == [-1, '']:
        return texts, clicked, cancel_indices, False, "Нет зачеркиваний для отмены."
    i0, t0 = cancel_indices[0][0], cancel_indices[0][1]
    i1, t1 = cancel_indices[1][0], cancel_indices[1][1]
    if i0 >= len(texts) or i1 >= len(texts):
        return texts, clicked, cancel_indices, False, "Нет зачеркиваний для отмены."
    texts[i0], texts[i1] = t0, t1
    clicked[i0], clicked[i1] = '0', '0'
    cancel_indices[0] = [-1, '']
    cancel_indices[1] = [-1, '']
    return texts, clicked, cancel_indices, True, "Отмена выполнена."


def toggle_select(clicked: list, index: int) -> list:
    """Toggle cell at index between '0' and '1'; return new clicked list."""
    clicked = list(clicked)
    if index < 0 or index >= len(clicked) or clicked[index] == '2':
        return clicked
    clicked[index] = '1' if clicked[index] == '0' else '0'
    return clicked
