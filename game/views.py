from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages

from . import logic

SESSION_TEXTS = 'game_texts'
SESSION_CLICKED = 'game_clicked'
SESSION_CANCEL = 'game_cancel'
SESSION_SELECTED = 'game_selected'
SESSION_PROMPTED = 'game_prompted'  # [i, j] indices to highlight after check_del


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


@ensure_csrf_cookie
@require_GET
def game_view(request):
    texts, clicked, cancel = _get_state(request)
    _save_state(request, texts, clicked, cancel)
    won = logic.check_win(clicked)
    selected = request.session.get(SESSION_SELECTED)
    prompted = set(request.session.get(SESSION_PROMPTED) or [])
    cells = [{'index': i, 'text': t, 'state': c} for i, (t, c) in enumerate(zip(texts, clicked))]
    return render(request, 'game/game.html', {
        'cells': cells,
        'cols': 9,
        'won': won,
        'selected_index': selected,
        'prompted_indices': prompted,
    })


@require_POST
def action_view(request):
    action = request.POST.get('action', '')
    texts, clicked, cancel = _get_state(request)

    if action == 'start_over':
        texts = list(logic.DEFAULT_TEXTS)
        clicked = ['0'] * len(texts)
        cancel = [[-1, ''], [-1, '']]
        _save_state(request, texts, clicked, cancel)
        if SESSION_PROMPTED in request.session:
            del request.session[SESSION_PROMPTED]
        messages.success(request, 'Игра начата заново.')
        return redirect('game:play')

    if action == 'continue':
        texts, clicked = logic.do_continue(texts, clicked)
        rows = len(texts) // 9
        if rows > 200:
            texts = list(logic.DEFAULT_TEXTS)
            clicked = ['0'] * len(texts)
            cancel = [[-1, ''], [-1, '']]
            _save_state(request, texts, clicked, cancel)
            if SESSION_PROMPTED in request.session:
                del request.session[SESSION_PROMPTED]
            messages.success(request, 'Игра начата заново, а то было слишком много кнопок без шансов их все зачеркнуть')
            return redirect('game:play')
        cancel = [[-1, ''], [-1, '']]
        _save_state(request, texts, clicked, cancel)
        if SESSION_PROMPTED in request.session:
            del request.session[SESSION_PROMPTED]
        return redirect('game:play')

    if action == 'check_del':
        pair = logic.find_removable_pair(texts, clicked)
        if pair:
            request.session[SESSION_PROMPTED] = pair
            messages.info(request, f'Да, можно стереть пару: ячейки {pair[0]} и {pair[1]}.')
        else:
            if SESSION_PROMPTED in request.session:
                del request.session[SESSION_PROMPTED]
            messages.warning(request, 'Стирать больше нечего. Нажмите «Продолжить».')
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
        return redirect('game:play')

    if action == 'clear_selection':
        if SESSION_SELECTED in request.session:
            del request.session[SESSION_SELECTED]
        if SESSION_PROMPTED in request.session:
            del request.session[SESSION_PROMPTED]
        return redirect('game:play')

    if action == 'strike':
        try:
            i0 = int(request.POST.get('i0'))
            i1 = int(request.POST.get('i1'))
        except (ValueError, TypeError):
            messages.error(request, 'Выберите две ячейки.')
            return redirect('game:play')
        if SESSION_SELECTED in request.session:
            del request.session[SESSION_SELECTED]
        if SESSION_PROMPTED in request.session:
            del request.session[SESSION_PROMPTED]
        texts, clicked, cancel, ok, msg = logic.try_strike(texts, clicked, cancel, i0, i1)
        _save_state(request, texts, clicked, cancel)
        if ok:
            # messages.success(request, msg)
            if logic.check_win(clicked):
                messages.success(request, 'Поздравляю, вы выиграли!')
        else:
            messages.error(request, msg)
        return redirect('game:play')

    return redirect('game:play')
