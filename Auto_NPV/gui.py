"""Модуль пользовательского интерфейса программы.
Средствами tkinter запускается интерактивное окно, в котором пользователь
задает исходные параметры для расчета показателей экономической эффективности
проекта строительства жилого комплекса: себестоимость строительства,
общая и жилая площадь здания, средняя стоимость кв. метра на старте продаж,
продолжительность строительства, ставка дисконтирования и др.
"""

import datetime
import tkinter as tk
from tkinter import messagebox

if __name__ == '__main__':
    print('Запуск скрипта "gui.py".')
else:
    print(f'Импорт и запуск модуля {__name__}.')

floor_area = 10_000  # общая площадь здания, кв. м
apartment_area = 7_000  # продаваемая площадь квартир, кв. м

construction_costs = 60_000  # руб./кв. м общей площади
construction_period = 10  # продолжительность строительства, кварталов

start_price = 105_000  # руб./кв. м на старте продаж
completion_premium = 30  # наценка на квартиры в сданном доме к цене на старте продаж, %

inflation = 5  # инфляция, % в год
discount_rate = 6  # ставка дисконтирования, % в год

FONTSIZE = ('Arial', 10, 'bold')
FONTSIZE_SMALL = ('Arial', 10)
FONTSIZE_BUTTONS = ('Arial', 10, 'bold')
PAD = 4
ENTRY_WIDTH = 10
COMBO_WIDTH = 16
SCALE_WIDTH = 200
BACKGROUND = '#80c1ff'

window = tk.Tk()
window.geometry('600x600')
window.title('Экономическая эффективность проекта')


def function_info(original_function):
    """Функция-декоратор - выводит в консоль информацию
    о вызываемой функции, дату и время вызова функции.
    Аргументы:
        original_function - исходная функция."""

    def wrapper_function(*args, **kwargs):
        now = datetime.datetime.today()
        print(f'{now}: вызов функции {original_function.__name__}')
        return original_function(*args, **kwargs)

    return wrapper_function


@function_info
def check_number(entry: str):
    """Функция принимает пользовательский ввод, возвращает преобразованное
    в число значение. При возникновении ошибок возвращает False и
    активирует предупреждение в интерактивном окне программы.
    Аргументы:
        entry - текстовое значение из пользовательского ввода."""
    try:
        entry = int(entry)

    except Exception as e:  # При возникновении ошибок преобразования в число
        print(f'Ошибка: {e}')
        if entry != '':
            messagebox.showerror('Ошибка', 'Введены нечисловые значения.')
        else:
            messagebox.showerror('Ошибка', 'Заполнены не все обязательные поля.')
        return False

    return entry


@function_info
def get_entries():
    """Функция запускается при нажатии пользователем на кнопку 'Запустить расчет'
    в интерактивном окне программы (см. переменную 'exit_button').
    Функция получает введенные пользователем значения параметров и присваивает их
    глобальным переменным. Закрывает интерактивное окно tkinter, если данные корректны."""

    global floor_area, apartment_area, construction_costs, construction_period, \
        start_price, completion_premium, inflation, discount_rate

    # Значения из виджетов Scale:
    construction_costs = scale_construction_cost.get()
    construction_period = scale_construction_period.get()
    start_price = scale_start_price.get()
    completion_premium = 1 + scale_completion_premium.get() / 100
    inflation = 1 + scale_inflation.get() / 100
    discount_rate = 1 + scale_discount_rate.get() / 100

    # Список значений пользовательского ввода из виджетов Entry, где могут быть ошибки:
    entered_list = [entry_floor_area.get(), entry_apartment_area.get()]
    # Список значений по умолчанию для этих переменных:
    default_list = [floor_area, apartment_area]
    # Проверяем, что все введенные с клавиатуры значения преобразуются в числовые,
    # и меняем значения, заданные по умолчанию, на пользовательский ввод:
    correct_nums = True
    for index, entry in enumerate(entered_list):
        cur_entry = check_number(entry)
        if cur_entry:
            default_list[index] = cur_entry
        else:
            correct_nums = False
            break

    # Если все данные заполнены корректно, закрываем окно.
    if correct_nums:
        floor_area, apartment_area = default_list
        window.destroy()  # Закрываем интерактивное окно программы.


# Текстовое поле с инструкциями для пользователя:
text_1 = """Введите исходные данные для расчета или оставьте значения,
заданные по умолчанию.
Нажмите 'Запустить расчет'.\n"""
instruction = tk.Label(window, text=text_1, font=FONTSIZE, justify='left')
instruction.grid(column=0, row=0, columnspan=3, padx=PAD, pady=PAD)

# Сегмент основного окна с параметрами проекта:
frame_project = tk.Frame(window, bg=BACKGROUND, bd=5)
frame_project.grid(column=0, row=1, columnspan=2, padx=PAD, pady=PAD)

indicator_project = tk.Label(frame_project, text='Параметры проекта', font=FONTSIZE_SMALL)
indicator_project.grid(column=0, row=0, columnspan=2, padx=PAD, pady=PAD)

reference_floor_area = tk.Label(frame_project, text='Общая площадь здания, кв. м', font=FONTSIZE_SMALL)
reference_floor_area.grid(column=0, row=1, sticky='W', padx=PAD, pady=PAD)
entry_floor_area = tk.Entry(frame_project, width=ENTRY_WIDTH, font=FONTSIZE)
entry_floor_area.grid(column=1, row=1, padx=PAD, pady=PAD)
entry_floor_area.insert(0, floor_area)

reference_apartment_area = tk.Label(frame_project, text='Площадь квартир, кв. м', font=FONTSIZE_SMALL)
reference_apartment_area.grid(column=0, row=2, sticky='W', padx=PAD, pady=PAD)
entry_apartment_area = tk.Entry(frame_project, width=ENTRY_WIDTH, font=FONTSIZE)
entry_apartment_area.grid(column=1, row=2, padx=PAD, pady=PAD)
entry_apartment_area.insert(0, apartment_area)

reference_construction_period = tk.Label(frame_project,
                                         text='Период строительства, кварталов',
                                         font=FONTSIZE_SMALL)
reference_construction_period.grid(column=0, row=3, sticky='W', padx=PAD, pady=PAD)
cost_var = tk.IntVar()
scale_construction_period = tk.Scale(frame_project, from_=4, to=20, bg=BACKGROUND,
                                     orient='horizontal', length=SCALE_WIDTH, font=FONTSIZE)
scale_construction_period.grid(column=1, row=3, padx=PAD, pady=PAD)
scale_construction_period.set(construction_period)


# Сегмент основного окна с затратами и ценовыми параметрами:
frame_economics = tk.Frame(window, bg=BACKGROUND, bd=5)
frame_economics.grid(column=0, row=2, columnspan=2, padx=PAD, pady=PAD)

reference_construction_cost = tk.Label(frame_economics,
                                       text='Себестоимость строительства, руб./кв. м',
                                       font=FONTSIZE_SMALL)
reference_construction_cost.grid(column=0, row=0, sticky='W', padx=PAD, pady=PAD)
scale_construction_cost = tk.Scale(frame_economics, from_=50_000, to=100_000, resolution=1_000,
                                   bg=BACKGROUND, orient='horizontal', length=SCALE_WIDTH, font=FONTSIZE)
scale_construction_cost.grid(column=1, row=0, padx=PAD, pady=PAD)
scale_construction_cost.set(construction_costs)

reference_start_price = tk.Label(frame_economics,
                                 text='Средняя цена квартир на старте продаж, руб./кв. м',
                                 font=FONTSIZE_SMALL)
reference_start_price.grid(column=0, row=1, sticky='W', padx=PAD, pady=PAD)
scale_start_price = tk.Scale(frame_economics, from_=80000, to=150000, resolution=1_000,
                             bg=BACKGROUND, orient='horizontal', length=SCALE_WIDTH, font=FONTSIZE)
scale_start_price.grid(column=1, row=1, padx=PAD, pady=PAD)
scale_start_price.set(start_price)

reference_completion_premium = tk.Label(frame_economics,
                                 text='Увеличение цен за период строительства, %',
                                 font=FONTSIZE_SMALL)
reference_completion_premium.grid(column=0, row=2, sticky='W', padx=PAD, pady=PAD)
scale_completion_premium = tk.Scale(frame_economics, from_=10, to=50, bg=BACKGROUND,
                                    orient='horizontal', length=SCALE_WIDTH, font=FONTSIZE)
scale_completion_premium.grid(column=1, row=2, padx=PAD, pady=PAD)
scale_completion_premium.set(completion_premium)

# Сегмент основного окна с процентными ставками:
frame_rates = tk.Frame(window, bg=BACKGROUND, bd=5)
frame_rates.grid(column=0, row=3, columnspan=2, padx=PAD, pady=PAD)

reference_inflation = tk.Label(frame_rates, text='Инфляция, %', font=FONTSIZE_SMALL)
reference_inflation.grid(column=0, row=0, sticky='W', padx=PAD, pady=PAD)
scale_inflation = tk.Scale(frame_rates, from_=1, to=20, bg=BACKGROUND,
                           orient='horizontal', length=SCALE_WIDTH, font=FONTSIZE)
scale_inflation.grid(column=1, row=0, padx=PAD, pady=PAD)
scale_inflation.set(inflation)

reference_discount_rate = tk.Label(frame_rates,
                                   text='Ставка дисконтирования, %',
                                   font=FONTSIZE_SMALL)
reference_discount_rate.grid(column=0, row=1, sticky='W', padx=PAD, pady=PAD)
scale_discount_rate = tk.Scale(frame_rates, from_=3, to=20, resolution=0.1,
                               bg=BACKGROUND, orient='horizontal', length=SCALE_WIDTH, font=FONTSIZE)
scale_discount_rate.grid(column=1, row=1, padx=PAD, pady=PAD)
scale_discount_rate.set(discount_rate)

# Кнопка для запуска программы и закрытия диалогового окна с виджетами:
exit_button = tk.Button(window, text='Запустить расчет', font=FONTSIZE_BUTTONS,
                        bg='#d90d1b', fg='white', command=get_entries)
exit_button.grid(column=0, row=4, columnspan=2, padx=PAD, pady=PAD)

window.mainloop()

# Для передачи параметров в главный модуль создается словарь:
parameters = {
    'floor_area': floor_area,
    'apartment_area': apartment_area,
    'construction_costs': construction_costs,
    'inflation_annual': inflation,
    'construction_period': construction_period,
    'start_price': start_price,
    'completion_premium': completion_premium,
    'discount_rate_annual': discount_rate
}
