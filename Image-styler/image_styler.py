import os
import numpy as np

from PIL import Image, ImageTk

import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Combobox
from tkinter.filedialog import asksaveasfilename, askopenfilename

import tensorflow as tf
import tensorflow_hub as hub

print('TF Version:', tf.__version__)
print('TF-Hub version:', hub.__version__)
print('Eager mode enabled:', tf.executing_eagerly())
print('GPU available:', len(tf.config.list_physical_devices('GPU')))

# Ссылка на модель на TF hub:
hub_link = 'https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2'

# Форматирование шрифтов и виджетов:
FONTSIZE = ('Arial', 10, 'bold')
FONTSIZE_SMALL = ('Arial', 10)
FONTSIZE_BUTTONS = ('Arial', 10, 'bold')
PAD = 6
BUTTON_WIDTH = 20
BUTTON_COLOR = '#039170'
BG_COLOR = '#a7fae7'

instruction_text = """Выберите файл с изображением и файл с образцом копируемого стиля.
В выпадающем списке выберите размер изображения в пикселях.
Нажмите <Обработка> и оцените результат.
Сохраните полученное изображение в файл под выбранным именем.
При необходимости повторите с другими исходными файлами.
Для завершения работы с программой нажмите <Закрыть>."""


class Styler:
    """Класс для создания интерактивного окна для обработки
    изображений с использованием модели style transfer."""

    def __init__(self):
        """Инициализация не требует передачи аргументов.
        При создании объекта запускается интерактивное окно
        с виджетами и инструкцией для пользователя."""

        self.window = tk.Tk()
        self.content_link = None  # Ссылка на файл с обрабатываемым изображением
        self.style_link = None  # Ссылка на файл с образцом стиля
        self.content = None  # Исходное изображение
        self.style = None  # Копируемое изображение
        self.result = None  # Результат преобразования
        self.content_display = None  # Для отображения на Canvas
        self.style_display = None
        self.result_display = None
        self.size = 384  # Размер изображения

        # Наполнение окна программы виджетами:
        self.create_window()

    def create_window(self):
        """Функция наполняет интерактивное окно программы виджетами."""

        self.window.geometry('950x500')
        self.window['bg'] = BG_COLOR
        self.window.title('Image Styler')

        # Блок для виджетов, инструкции и исходных изображений:
        self.main_frame = tk.Frame(self.window, bg=BG_COLOR, bd=5)
        self.main_frame.grid(column=0, row=0, rowspan=3, padx=PAD, pady=PAD)

        # Инструкция для пользователя:
        self.label_info = tk.Label(self.main_frame, text=instruction_text,
                                   justify='left', font=FONTSIZE, bg=BG_COLOR)
        self.label_info.grid(column=0, row=0, columnspan=4, padx=PAD, pady=PAD)

        # Кнопки для выбора файлов и подписи к ним:
        self.button_select_content = tk.Button(self.main_frame, text='Выбрать изображение',
                                               font=FONTSIZE_BUTTONS, width=BUTTON_WIDTH,
                                               bg=BUTTON_COLOR, fg='white', command=self.select_content)
        self.button_select_content.grid(column=0, row=1, padx=PAD, pady=PAD)
        self.label_content = tk.Label(self.main_frame, text='Исходное изображение не выбрано',
                                      font=FONTSIZE_SMALL, bg=BG_COLOR)
        self.label_content.grid(column=0, row=2, padx=PAD, pady=PAD)
        self.button_select_style = tk.Button(self.main_frame, text='Выбрать стиль',
                                             font=FONTSIZE_BUTTONS, width=BUTTON_WIDTH,
                                             bg=BUTTON_COLOR, fg='white', command=self.select_style)
        self.button_select_style.grid(column=1, row=1, padx=PAD, pady=PAD)
        self.label_style = tk.Label(self.main_frame, text='Копируемое изображение не выбрано',
                                    font=FONTSIZE_SMALL, bg=BG_COLOR)
        self.label_style.grid(column=1, row=2, padx=PAD, pady=PAD)

        # Выпадающий список для выбора размера изображения и подпись к нему:
        self.label_size = tk.Label(self.main_frame, text='Размер изображения', font=FONTSIZE_SMALL, bg=BG_COLOR)
        self.label_size.grid(column=0, row=4, sticky='E', padx=PAD, pady=PAD)
        self.combo_size = Combobox(self.main_frame, width=15, font=FONTSIZE)
        self.combo_size['values'] = ([256, 300, 384, 400])
        self.combo_size.current(2)
        self.combo_size.grid(column=1, row=4, sticky='W', padx=PAD, pady=PAD)

        # Кнопка для преобразования изображения:
        self.button_copy_style = tk.Button(self.main_frame, text='Обработка', width=BUTTON_WIDTH,
                                           font=FONTSIZE_BUTTONS, bg=BUTTON_COLOR, fg='white',
                                           command=self.transform)
        self.button_copy_style.grid(column=0, row=5, padx=PAD, pady=PAD)

        # Кнопка для сохранения изображения в файл:
        self.save_button = tk.Button(self.main_frame, text='Сохранить', width=BUTTON_WIDTH,
                                     font=FONTSIZE_BUTTONS, bg=BUTTON_COLOR, fg='white',
                                     command=self.save_image)
        self.save_button.grid(column=1, row=5, padx=PAD, pady=PAD)

        # Для отображения текущего статуса приложения:
        self.label_status = tk.Label(self.window, text='',
                                     font=FONTSIZE_SMALL, bg=BG_COLOR)
        self.label_status.grid(column=1, row=0, padx=PAD, pady=PAD)

        # Обозначаем места для размещения изображений:
        self.canvas_content = tk.Canvas(master=self.main_frame, width=200, height=200)
        self.canvas_content.create_rectangle(5, 5, 195, 195, fill=BG_COLOR, outline=BG_COLOR)
        self.canvas_content.grid(column=0, row=3)

        self.canvas_style = tk.Canvas(master=self.main_frame, width=200, height=200)
        self.canvas_style.create_rectangle(5, 5, 195, 195, fill=BG_COLOR, outline=BG_COLOR)
        self.canvas_style.grid(column=1, row=3)

        self.canvas_result = tk.Canvas(master=self.window, width=self.size, height=self.size)
        self.canvas_result.create_rectangle(5, 5, self.size - 5, self.size - 5, fill=BG_COLOR, outline=BG_COLOR)
        self.canvas_result.grid(column=1, row=1)

        # Кнопка закрывает окно программы:
        self.button_exit = tk.Button(self.window, text='Закрыть',
                                     font=FONTSIZE_BUTTONS, width=BUTTON_WIDTH,
                                     bg=BUTTON_COLOR, fg='white', command=self.close_window)
        self.button_exit.grid(column=1, row=2, padx=PAD, pady=PAD)

        self.window.mainloop()

    def select_content(self):
        """Функция запускает интерактивную форму для выбора
        исходного изображения. Вызывается нажатием кнопки 'Выбрать изображение'."""
        self.label_status['text'] = 'Идет загрузка исходного файла.'
        print('Content selection.')
        file_path = askopenfilename(title='Выберите файл с изображением',
                                    filetypes=[("Images", "*.png; *.jpg; *.jpeg")])
        if file_path:
            self.content_link = file_path
            self.label_content['text'] = os.path.basename(file_path)
            self.show_image(file_path, 0)
        else:
            self.label_status['text'] = 'Исходный файл не выбран.'

    def select_style(self):
        """Функция запускает интерактивную форму для выбора
        копируемого стиля. Вызывается нажатием кнопки 'Выбрать стиль'."""
        self.label_status['text'] = 'Идет загрузка копируемого стиля.'
        print('Style selection.')
        file_path = askopenfilename(title='Выберите файл с копируемым стилем',
                                    filetypes=[("Images", "*.png; *.jpg; *.jpeg")])
        if file_path:
            self.style_link = file_path
            self.label_style['text'] = os.path.basename(file_path)
            self.show_image(file_path, 1)
        else:
            self.label_status['text'] = 'Стиль не выбран.'

    def transform(self):
        """Функция преобразует исходное изображение
        через модель style transfer, отображает
        полученный результат в интерактивном окне.
        Вызывается нажатием кнопки 'Обработка'."""

        self.label_status['text'] = 'Идет преобразование исходного изображения.'
        print('Image transformation.')

        if self.content is None:
            print('Image transformation error: content image is missing.')
            messagebox.showerror('Ошибка', 'Не выбран исходный файл для обработки.')
            self.label_status['text'] = ''

        elif self.style is None:
            print('Image transformation error: style image is missing.')
            messagebox.showerror('Ошибка', 'Не выбран стиль для обработки изображения.')
            self.label_status['text'] = ''

        else:
            # Обработка исходного изображения:
            self.size = int(self.combo_size.get())
            content_image = process_image(self.content, (self.size, self.size))
            # Обработка изображения с образцом копируемого стиля:
            style_image = process_image(self.style)
            style_image = tf.nn.avg_pool(style_image, ksize=[3, 3], strides=[1, 1], padding='SAME')
            # Преобразование изображения:
            outputs = model(content_image, style_image)[0][0]  # Tensor object
            self.result = tf.keras.preprocessing.image.array_to_img(outputs.numpy())  # Image
            self.result_display = ImageTk.PhotoImage(self.result)  # PhotoImage

            # Отображение полученного результата в интерактивном окне:
            self.canvas_result = tk.Canvas(master=self.window, width=self.size, height=self.size)
            self.canvas_result.create_image(0, 0, anchor='nw', image=self.result_display)
            self.canvas_result.grid(column=1, row=1)
            self.label_status['text'] = 'Преобразование изображения завершено.'

    def show_image(self, image_path, pos):
        """Функция отображает в интерактивном окне программы
        изображение в указанной позиции. Вызывается автоматически
        при выборе ссылки на изображение внутри функций
        select_content() и select_style()."""

        print('Showing image.')
        img = Image.open(image_path)

        if pos == 0:
            # Исходное изображение
            self.content = img
            self.content_display = ImageTk.PhotoImage(img.resize([200, 200]))
            self.canvas_content.create_image(0, 0, anchor='nw', image=self.content_display)
            self.canvas_content.grid(column=pos, row=3)
            self.label_status['text'] = ''

        elif pos == 1:
            # Копируемый стиль
            self.style = img
            self.style_display = ImageTk.PhotoImage(img.resize([200, 200]))
            self.canvas_style.create_image(0, 0, anchor='nw', image=self.style_display)
            self.canvas_style.grid(column=pos, row=3)
            self.label_status['text'] = ''

    def save_image(self):
        """Функция запускает интерактивную форму для сохранения
        текущей версии изображения в файл .png.
        Вызывается нажатием кнопки 'Сохранить'."""

        if self.result is not None:
            file_path = asksaveasfilename(title='Укажите имя файла',
                                          filetypes=[("Изображения", "*.png; *.jpg; *.jpeg")])
            if file_path:
                print(file_path)
                file_path += '.png'
                print('Saved file:', file_path)
                self.result.save(file_path)
                self.label_status['text'] = 'Файл сохранен.'
            else:
                print('File name not entered. File not saved.')
        else:
            messagebox.showerror('Ошибка', '''Невозможно сохранить изображение.
            Выберите исходные файлы, нажмите <Обработка> и дождитесь ее завершения.
            Затем нажмите <Сохранить>.''')
            self.label_status['text'] = 'Невозможно сохранить изображение.'

    def close_window(self):
        """Функция закрывает интерактивное окно программы.
        Вызывается нажатием кнопки 'Закрыть'."""

        print('Program finished.')
        self.window.quit()
        self.window.destroy()


# -------------------- Функции для работы с моделью ------------------------------


def crop_image(image):
    """Функция принимает изображение и возвращает
    преобразованное изображение квадратной формы."""

    shape = image.shape
    new_shape = min(shape[1], shape[2])
    offset_y = max(shape[1] - shape[2], 0) // 2
    offset_x = max(shape[2] - shape[1], 0) // 2
    image = tf.image.crop_to_bounding_box(
        image, offset_y, offset_x, new_shape, new_shape)

    return image


def process_image(image, image_size=(256, 256), preserve_aspect_ratio=True):
    """Функция принимает изображение и размер,
    возвращает обработанное изображение."""

    # Преобразуем данные в массив numpy (float32),
    # добавляем измерение для batch, нормируем к диапазону [0, 1].
    image = tf.keras.preprocessing.image.img_to_array(image)
    img = image.astype(np.float32)[np.newaxis, ...]
    if img.max() > 1.0:
        img = img / 255.
    if len(img.shape) == 3:
        img = tf.stack([img, img, img], axis=-1)
    img = crop_image(img)
    img = tf.image.resize(img, image_size,
                          preserve_aspect_ratio=preserve_aspect_ratio)

    return img


# ---------------------------------------------------------------------------------------

# Загрузка модели с TF hub:
model = hub.load(hub_link)
print('Model loaded.')

# Запуск окна пользовательского интерфейса:
styler = Styler()
