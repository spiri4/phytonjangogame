import tkinter as tk
from tkinter.ttk import *
from tkinter import messagebox
from tkinter import Menu
from itertools import combinations

def onButtonClick(ind, button_instance):
    # Обработка нажатия кнопки в зависимости от её состояния clicked
    match button_instance.clicked:
            case "1":
                button_instance.clicked = '0'
                button_instance.config(bg="#d9d9d9")
            case "0":
                button_instance.clicked = '1'
                button_instance.config(bg="lightgreen")
            case _:
                return
    # drop_avail = check_drop_available()
    check_drop_available()
    if check_win()=="Y": messagebox.showinfo("Победа!", "Поздравляю вы выйграли!")

def check_nearest_index(index1,index2):
    global buttons
    if index2-index1 == 1 or ((index2-index1)/9) == 1 : return "Y"
    else:
        if ((index2-index1)/9).is_integer() :
                #range не включает END о ужас
                for k in range(index1+9, index2, 9) : 
                    if buttons[k].clicked == '2' : k=k+9
                    else: return "N"
                return "Y"
        else:
            #range не включает END о ужас
            for p in range(index1+1, index2, 1) : 
                if buttons[p].clicked == '2' : p=p+1
                else: return "N"
            return "Y"   

# Проверка условия победы - все кнопки зачеркнуты    
def check_win():
    global buttons
    # Return "Y" only when every button has clicked == '2'
    return "Y" if all(getattr(b, 'clicked', None) == '2' for b in buttons) else "N"
    

def disable_button(index):
    global buttons, cancel_indices
    if cancel_indices[0] == (-1,-1): 
        cancel_indices[0] = (index, buttons[index]['text'])
    else :
        if cancel_indices[1] == (-1,-1): 
            cancel_indices[1] = (index, buttons[index]['text']) 
    buttons[index].clicked = '2'
    buttons[index].config(bg="black")
    buttons[index].config(text='0')
    buttons[index].config(state="disabled")

def unclick_button(index):
    global buttons, cancel_indices
    buttons[index].clicked = '0'
    # buttons[index].config(bg="#d9d9d9")
    buttons[index].config(bg="#f0f0f0")
    buttons[index].config(state="normal")
    if buttons[index]['text']=='0':
        if index==cancel_indices[0][0]: buttons[index].config(text=cancel_indices[0][1])
        if index==cancel_indices[1][0]: buttons[index].config(text=cancel_indices[1][1])

def prompt_button(index):
    global buttons
    buttons[index].config(fg="red")
    # font=('Arial', 10, 'bold italic')

def check_drop_available():
    global buttons
    # collect selected buttons (clicked == '1') with their numeric values
    selected = []  # list of (index, int(value))
    for i, b in enumerate(buttons):
        if getattr(b, 'clicked', None) == '1':
            try:
                val = int(b['text'])
            except Exception:
                # ignore non-numeric selections
                continue
            selected.append((i, val))

    if len(selected) != 2:
        return "N"

    # sort by index to preserve order
    selected.sort(key=lambda t: t[0])
    (i0, v0), (i1, v1) = selected

    # valid if equal or sum to 10
    if not (v0 == v1 or v0 + v1 == 10):
        unclick_button(i0)
        unclick_button(i1)
        messagebox.showerror("Эти цифры нельзя зачеркнуть", "Зачеркивать можно либо одинаковые цифры либо цифры дающие в сумме 10")
        return "N"

    if check_nearest_index(i0, i1) == "Y":
        disable_button(i0)
        disable_button(i1)
        return "Y"

    # еслил ни один if не сработал, то зачеркивать нельзя
    unclick_button(i0)
    unclick_button(i1)
    messagebox.showerror("Эти цифры нельзя зачеркнуть", "Зачеркивать можно либо одинаковые цифры либо цифры дающие в сумме 10")
    return "N"

# меню Выход
def quit_app():
    frame_container.destroy()
    root.destroy()
    root.quit()

# отрисовка глобального массива кнопок (buttons) во фрейме - через grid
def put_btns_in_grid():
    global buttons
    # Расположение кнопок в гриде в 9 колонок
    for i, btn in enumerate(buttons):
        r = i // 9 + 1
        c = i % 9 + 1
        btn.grid(row=r, column=c, sticky="w")


# создание массива кнопок на основе массива текстов из инпута
def create_content(btn_txt):
    global buttons, button_texts, frame_container, im
    if btn_txt==[]: btn_txt= button_texts
    # Clear existing content in the frame
    for widget in frame_container.winfo_children():
        widget.destroy()
    # Destroy any existing button widgets and reset the list
    for btn in buttons:
        try:
            btn.destroy()
        except Exception:
            pass
    buttons.clear()

    # Create buttons and append to the global list
    for i, text in enumerate(btn_txt):
        btn = tk.Button(
            frame_container,
            text=text,
            image=im,
            compound='c',
            width=20,
            height=20,
            padx=0,
            name='btn'+str(i)
        )
        btn.clicked = '0'
        btn.config(command=lambda i=i, b=btn: onButtonClick(i, b))
        buttons.append(btn)
        if btn_txt[i]=='0': disable_button(i)

    put_btns_in_grid()

# создание начального контента
def create_initial_content():
    global button_texts
    create_content(button_texts)

#Проверка что все кнопки в ряду зачеркнуты
def check_row_empty(row_ind):
    global buttons
    # for f in range(row_ind, row_ind + 8, 1): END сука не включается в range
    for f in range(row_ind, row_ind + 9, 1): 
        if buttons[f].clicked == '2' : f=f+1
        else: return "N"
    return "Y"

#Find any removable pair among active buttons
def check_to_del():
    global buttons
    btns = buttons
    # collect indices of non-disabled buttons (preserves order)
    active_idxs = [i for i, b in enumerate(btns) if b.clicked != '2']

    for i_idx, j_idx in combinations(active_idxs, 2):
        # quick numeric conversion; skip if not numeric
        try:
            vi = int(btns[i_idx]['text'])
            vj = int(btns[j_idx]['text'])
        except Exception:
            continue

        if (vi == vj or vi + vj == 10) and check_nearest_index(i_idx, j_idx) == "Y":
            messagebox.showerror("Да, есть что стереть", f"Да, можно стереть {i_idx} и {j_idx}")
            prompt_button(i_idx)
            prompt_button(j_idx)
            return

    messagebox.showerror("Нет, нечего стереть", "Стирать больше нечего, нажмите Продолжить")

# delete full rows of disabled buttons
def del_empty_rows():
    global buttons
    for del_row_ind in range(len(buttons)//9-1, -1, -1):
        if check_row_empty(del_row_ind*9) == "Y":
            del buttons[del_row_ind*9:del_row_ind*9+9]


# меню Продолжить
def continue_app():
    global buttons 
    buttons_dup = [] #временный массив с текстом кнопок
    del_empty_rows()
    i=0
    # сначала копируем все тексты кнопок в buttons_dup
    for i,text in enumerate(buttons):
        buttons_dup.append(buttons[i]['text'])
    # потом добавляем в buttons_dup только те тексты кнопок, которые не зачеркнуты
    i=0
    for i,text in enumerate(buttons):
        if buttons[i].clicked != '2' : buttons_dup.append(buttons[i]['text'])
    
    # пересоздаём массив кнопок на основе buttons_dup
    create_content(buttons_dup)
    # размещаем кнопки в гриде
    put_btns_in_grid()
    # очищаем временный массив
    buttons_dup.clear()

#  меню Отменить последнее зачеркивание
def cancel_last_strike():
    global buttons, cancel_indices
    if cancel_indices[0] == (-1,-1) or cancel_indices[1] == (-1,-1):
        messagebox.showerror("Ошибка", "Нет зачеркиваний для отмены")
        return
    unclick_button(cancel_indices[0][0])
    unclick_button(cancel_indices[1][0])
    cancel_indices = [(-1,-1),(-1,-1)]

# Создаем главное окно
root = tk.Tk()
root.title("цИфИрки")
root.geometry("260x600")
# можно растягивать окно по высоте, нельзя по ширине
root.resizable(False, True)
# родительский фрейм для кнопок
frame_container = tk.Frame(borderwidth=1, relief=tk.RIDGE)
frame_container.pack(pady=20, side='top')
# Создаем пустой список для кнопок
buttons = []
# Список при инициализации
button_texts = ["1", "2", "3", "4", "5", "6", "7" ,"8", "9",
                "1", "1", "1", "2", "1", "3", "1", "4", "1",
                "5", "1", "6", "1", "7", "1", "8", "1", "9"]
#глобальный массив пар индекса и значения последних двух зачеркнутых кнопок
cancel_indices = [(-1,-1),(-1,-1)]
im = tk.PhotoImage(width=1, height=1)
# меню
menu_bar = Menu(root)
root.config(menu=menu_bar)
action_menu = Menu(menu_bar)
menu_bar.add_cascade(label='Действия', menu=action_menu)
action_menu.add_command(label='Начать заново', command=create_initial_content)
action_menu.add_command(label='Продолжить', command=continue_app)
action_menu.add_command(label='Проверить есть ли что стереть', command=check_to_del)
action_menu.add_command(label='Отменить последнее зачеркивание', command=cancel_last_strike)
action_menu.add_command(label='Выход', command=quit_app)

# Инициализация контента
create_initial_content()

root.mainloop()