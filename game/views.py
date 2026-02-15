from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from . import logic
from .models import Winner

SESSION_TEXTS = 'game_texts'
SESSION_CLICKED = 'game_clicked'
SESSION_CANCEL = 'game_cancel'
SESSION_SELECTED = 'game_selected'
SESSION_PROMPTED = 'game_prompted'  # [i, j] indices to highlight after check_del
SESSION_PENDING_WIN_ROWS = 'game_pending_win_rows'  # число рядов при победе для записи в рекорды


def _get_state(request):
    texts = request.session.get(SESSION_TEXTS)
    clicked = request.session.get(SESSION_CLICKED)
    cancel = request.session.get(SESSION_CANCEL)
    if not texts or not clicked:
        texts = list(logic.DEFAULT_TEXTS)
        clicked = ['0'] * len(texts)
        cancel = [[-1, ''], [-1, '']]
    return texts, clicked, cancel


def _save_state(request, texts, clicked, cancel=None):
    request.session[SESSION_TEXTS] = texts
    request.session[SESSION_CLICKED] = clicked
    if cancel is not None:
        request.session[SESSION_CANCEL] = cancel


def _ajax_response(request, pending_win_rows_override=None):
    texts, clicked, cancel = _get_state(request)
    won = logic.check_win(clicked)
    selected = request.session.get(SESSION_SELECTED)
    prompted = set(request.session.get(SESSION_PROMPTED) or [])
    pending_win_rows = pending_win_rows_override if pending_win_rows_override is not None else request.session.get(SESSION_PENDING_WIN_ROWS)
    if won and pending_win_rows is None:
        pending_win_rows = len(texts) // 9
    cells = [{'index': i, 'text': t, 'state': c} for i, (t, c) in enumerate(zip(texts, clicked))]
    html = render_to_string('game/game_content.html', {
        'cells': cells,
        'cols': 9,
        'won': won,
        'selected_index': selected,
        'prompted_indices': prompted,
        'pending_win_rows': pending_win_rows,
    }, request=request)
    return JsonResponse({'html': html})


@require_GET
def rules_view(request):
    return render(request, 'game/info_page.html', {
        'title': 'Правила игры',
        'content': '''
        <p>Цель игры — зачеркнуть все цифры за наименьшее число рядов.</p>
        <p>Зачеркивайте пары цифр по правилам:</p>
        <ul>
            <li>Одинаковые цифры (например, 3 и 3)</li>
            <li>Либо цифры, дающие в сумме 10 (например, 2 и 8, 4 и 6)</li>
        </ul>
        <p>Пара должна быть «рядом»: по горизонтали или вертикали, без других активных цифр между ними (уже зачёркнутые не мешают).</p>
        <p>Выберите первую цифру (она подсветится), затем нажмите вторую — пара зачеркнётся. Меню «Продолжить» используется когда на поле уже нечего зачеркнуть, все незачёркнутые цифры повторно дописываются в конец без пропусков.</p>
        ''',
    })


@require_GET
def about_view(request):
    return render(request, 'game/info_page.html', {
        'title': 'Об игре',
        'content': '''
        <p><strong>"многа цЫфЫр"</strong> — головоломка с цифрами в сетке 9×N.</p>
        <p>Игра есть в двух вариантах: веб-версия (Django) и десктоп (tkinter, <code>main.py</code>).</p>
        <p>Посвящается Томскому Государственному Университету, и конкретно группе 1174 ФПМК, 2002го года выпуска.</p>
        ''',
    })


@require_GET
def author_view(request):
    return render(request, 'game/info_page.html', {
        'title': 'Об авторе',
        'content': '''
        <p>Автор аутист</p>
        ''',
    })


@require_GET
def records_view(request):
    """Таблица рекордов: до 10 записей, по возрастанию рядов, затем по дате."""
    records = Winner.objects.order_by('row_count', '-victory_date')[:10]
    return render(request, 'game/records.html', {'records': records})


@require_POST
def record_win_view(request):
    """Записать победителя: имя из POST, число рядов из сессии."""
    name = (request.POST.get('winner_name') or '').strip()[:200]
    row_count = request.session.get(SESSION_PENDING_WIN_ROWS)
    if row_count is not None and name:
        Winner.objects.create(winner_name=name, row_count=row_count)
        if SESSION_PENDING_WIN_ROWS in request.session:
            del request.session[SESSION_PENDING_WIN_ROWS]
        messages.success(request, 'Запись добавлена в таблицу рекордов.')
    return redirect('game:records')


@ensure_csrf_cookie
@require_GET
def game_view(request):
    texts, clicked, cancel = _get_state(request)
    _save_state(request, texts, clicked, cancel)
    won = logic.check_win(clicked)
    selected = request.session.get(SESSION_SELECTED)
    prompted = set(request.session.get(SESSION_PROMPTED) or [])
    pending_win_rows = request.session.get(SESSION_PENDING_WIN_ROWS)
    cells = [{'index': i, 'text': t, 'state': c} for i, (t, c) in enumerate(zip(texts, clicked))]
    return render(request, 'game/game.html', {
        'cells': cells,
        'cols': 9,
        'won': won,
        'selected_index': selected,
        'prompted_indices': prompted,
        'pending_win_rows': pending_win_rows,
    })


@require_POST
def action_view(request):
    action = request.POST.get('action', '')
    texts, clicked, cancel = _get_state(request)

    if 'cell' in request.POST:
        try:
            cell_index = int(request.POST.get('cell'))
        except (ValueError, TypeError):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return _ajax_response(request)
            return redirect('game:play')
        selected = request.session.get(SESSION_SELECTED)
        if selected is None:
            if 0 <= cell_index < len(clicked) and clicked[cell_index] != '2':
                request.session[SESSION_SELECTED] = cell_index
            if SESSION_PROMPTED in request.session:
                del request.session[SESSION_PROMPTED]
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return _ajax_response(request)
            return redirect('game:play')
        if selected == cell_index:
            if SESSION_SELECTED in request.session:
                del request.session[SESSION_SELECTED]
            if SESSION_PROMPTED in request.session:
                del request.session[SESSION_PROMPTED]
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return _ajax_response(request)
            return redirect('game:play')
        i0, i1 = selected, cell_index
        if SESSION_SELECTED in request.session:
            del request.session[SESSION_SELECTED]
        if SESSION_PROMPTED in request.session:
            del request.session[SESSION_PROMPTED]
        texts, clicked, cancel, ok, msg = logic.try_strike(texts, clicked, cancel, i0, i1)
        _save_state(request, texts, clicked, cancel)
        pending_win_rows = None
        if ok:
            if logic.check_win(clicked):
                pending_win_rows = len(texts) // 9
                request.session[SESSION_PENDING_WIN_ROWS] = pending_win_rows
                messages.success(request, 'Поздравляю, вы выиграли!')
        else:
            messages.error(request, msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return _ajax_response(request, pending_win_rows_override=pending_win_rows)
        return redirect('game:play')

    if action == 'start_over':
        texts = list(logic.DEFAULT_TEXTS)
        clicked = ['0'] * len(texts)
        cancel = [[-1, ''], [-1, '']]
        _save_state(request, texts, clicked, cancel)
        if SESSION_PROMPTED in request.session:
            del request.session[SESSION_PROMPTED]
        if SESSION_PENDING_WIN_ROWS in request.session:
            del request.session[SESSION_PENDING_WIN_ROWS]
        messages.success(request, 'Поехали.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return _ajax_response(request)
        return redirect('game:play')

    if action == 'continue':
        texts, clicked = logic.do_continue(texts, clicked)
        rows = len(texts) // 9
        if rows > 150:
            texts = list(logic.DEFAULT_TEXTS)
            clicked = ['0'] * len(texts)
            cancel = [[-1, ''], [-1, '']]
            _save_state(request, texts, clicked, cancel)
            if SESSION_PROMPTED in request.session:
                del request.session[SESSION_PROMPTED]
            messages.success(request, 'Игра начата заново, а то было слишком много кнопок без шансов их все зачеркнуть')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return _ajax_response(request)
            return redirect('game:play')
        cancel = [[-1, ''], [-1, '']]
        _save_state(request, texts, clicked, cancel)
        if SESSION_PROMPTED in request.session:
            del request.session[SESSION_PROMPTED]
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return _ajax_response(request)
        return redirect('game:play')

    if action == 'check_del':
        pair = logic.find_removable_pair(texts, clicked)
        if pair:
            request.session[SESSION_PROMPTED] = pair
            #messages.info(request, f'Да, можно стереть пару: ячейки {pair[0]} и {pair[1]}.')
        else:
            if SESSION_PROMPTED in request.session:
                del request.session[SESSION_PROMPTED]
            messages.warning(request, 'Стирать больше нечего. Нажмите «Продолжить».')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return _ajax_response(request)
        return redirect('game:play')

    if action == 'undo':
        texts, clicked, cancel, ok, msg = logic.undo_last_strike(texts, clicked, cancel)
        _save_state(request, texts, clicked, cancel)
        if SESSION_PROMPTED in request.session:
            del request.session[SESSION_PROMPTED]
        if ok:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return _ajax_response(request)
        return redirect('game:play')

    if action == 'select':
        try:
            idx = int(request.POST.get('index'))
        except (ValueError, TypeError):
            return redirect('game:play')
        if 0 <= idx < len(clicked) and clicked[idx] != '2':
            request.session[SESSION_SELECTED] = idx
        if SESSION_PROMPTED in request.session:
            del request.session[SESSION_PROMPTED]
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return _ajax_response(request)
        return redirect('game:play')

    if action == 'clear_selection':
        if SESSION_SELECTED in request.session:
            del request.session[SESSION_SELECTED]
        if SESSION_PROMPTED in request.session:
            del request.session[SESSION_PROMPTED]
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return _ajax_response(request)
        return redirect('game:play')

    if action == 'strike':
        try:
            i0 = int(request.POST.get('i0'))
            i1 = int(request.POST.get('i1'))
        except (ValueError, TypeError):
            messages.error(request, 'Выберите две ячейки.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return _ajax_response(request)
            return redirect('game:play')
        if SESSION_SELECTED in request.session:
            del request.session[SESSION_SELECTED]
        if SESSION_PROMPTED in request.session:
            del request.session[SESSION_PROMPTED]
        texts, clicked, cancel, ok, msg = logic.try_strike(texts, clicked, cancel, i0, i1)
        _save_state(request, texts, clicked, cancel)
        row_count = len(texts) // 9
        if ok:
            if logic.check_win(clicked):
                request.session[SESSION_PENDING_WIN_ROWS] = row_count
                messages.success(request, 'Поздравляю, вы выиграли!')
        else:
            messages.error(request, msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            pending = row_count if (ok and logic.check_win(clicked)) else None
            return _ajax_response(request, pending_win_rows_override=pending)
        return redirect('game:play')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return _ajax_response(request)
    return redirect('game:play')
