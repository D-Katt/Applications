"""Модуль для запуска интерактивного окна пользовательского интерфейса.
Позволяет выбрать файл формата .txt, .pdf, .xps, .oxps, .epub, .cbz, .fb2,
извлечь и озвучить в аудиоформате его содержимое. Работает как аудиоплейер,
позволяет останавливать и возобновлять воспроизведение текста,
выбирать страницу, хранит сведения о последней прослушанной странице файла
после закрытия окна GUI для использования при следующем обращении к файлу.
Команды для управления плейером осуществляются нажатием клавиш на клавиатуре.
Преобразование текста в аудио производится постранично, что позволяет
прослушивать большие файлы, не загружая их в память целиком.
"""

import pyttsx3
import fitz
import pygame
import os
import json
import threading

import tkinter as tk
from tkinter.filedialog import askopenfilename


def speak(sentence: str):
    """Функция озвучивает текстовую строку."""
    engine.say(sentence)
    engine.runAndWait()


# Звуковое сопровождение интерфейса (синхронизировано с открытием диалогового окна):
engine = pyttsx3.init()
t = threading.Thread(target=speak, args=['Выберите текстовый файл.'])
t.start()

# Пользовательский ввод пути к файлу:
root = tk.Tk()
root.wm_withdraw()
file_path = askopenfilename(title='Выберите файл',
                            filetypes=[('Text files', '*.txt; *.pdf; *.xps; *.oxps; .epub; .cbz; .fb2')])
root.destroy()

# Переменные для обработки текста:
content = []  # Текст постранично
n_pages = 0
cur_page = 0

# Для контроля паузы при воспроизведении аудио:
pause = False

# Память ридера (индекс текущей страницы по ссылке на файл):
if 'reader_memory.json' not in os.listdir():
    memory = json.loads('{}')
else:
    with open('reader_memory.json', 'r') as f:
        memory = json.load(f)
    if file_path in memory:
        cur_page = memory[file_path]

# Звуковое сопровождение интерфейса:
t.join()
speak('Выполняется обработка.')


def load_text(path: str):
    """Функция извлекает текст из файла
    и преобразует в список строк постранично."""

    global content, cur_page, n_pages

    # Если файл не выбран, озвучиваем рекомендацию
    # для пользователя и завершаем программу:
    if path == '':
        speak('Файл не найден. Попробуйте запустить программу и выбрать файл еще раз.')
        exit()

    try:
        extension = os.path.splitext(path)[1]

        # Для файлов в формате .txt:
        if extension == '.txt':
            with open(path, 'r') as f:
                while True:
                    # Считываем содержимое фрагментами по 4000 знаков,
                    # что примерно соответствует одной странице pdf:
                    data = f.read(4000)
                    if not data:
                        break
                    content.append(data)
            n_pages = len(content)
            # Если пользователь сохранил новый текст под названием,
            # которое уже есть в памяти ридера, и возникла ошибка индексации:
            if cur_page >= n_pages:
                cur_page = 0

        # Для файлов в формате .pdf и аналогичных:
        elif extension in ['.pdf', '.xps', '.oxps', '.epub', '.cbz', '.fb2']:
            doc = fitz.open(path)
            n_pages = doc.pageCount
            if cur_page >= n_pages:
                cur_page = 0

            for page in range(n_pages):
                current_page = doc.loadPage(page)
                cur_text = current_page.getText('text')
                content.append(cur_text)

    # При возникновении ошибок обработки файла, озвучиваем
    # рекомендацию для пользователя и завершаем программу:
    except Exception:
        speak('Произошла ошибка при обработке файла. Попробуйте запустить программу еще раз и выбрать другой файл.')
        exit()


# Преобразуем текст в список строк постранично:
load_text(file_path)


def text_to_audio_file():
    """Функция преобразует текст текущей страницы в аудиофайл."""
    engine.save_to_file(content[cur_page], 'reader_audio.wav')
    engine.runAndWait()


# Преобразуем текущую страницу в аудиофайл в текущей директории:
text_to_audio_file()

# При загрузке аудиофайла через pygame.mixer.load
# мы теряем возможность перезаписывать содержимое файла.
# Опция pygame.mixer.music.unload не работает.
# Создаем переменную, которая позволит освобождать файл
# для записи следующих страниц текста:
audio_file = open('reader_audio.wav')


def play_audio():
    """Функция запускает воспроизведение аудиофайла.
    Вызывается нажатием клавиши 's' на клавиатуре."""
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play(0)


def pause_audio():
    """Функция приостанавливает и возобновляет воспроизведение
    аудиофайла. Вызывается нажатием клавиши 'p' на клавиатуре."""

    global pause

    if not pause:
        pygame.mixer.music.pause()
        pause = True
    else:
        pygame.mixer.music.unpause()
        pause = False


# Настройки pygame:
pygame.mixer.pre_init(44100, -16, 2, 4096)
pygame.init()
pygame.mixer.init()

icon = pygame.image.load('icon.png')
pygame.display.set_icon(icon)
width = 900
height = 650
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Book Reader')

# Инструкции для пользователя, отображаемые в окне программы:
instruction_header = 'Команды для ввода с клавиатуры:'
instruction_1 = 's - начать воспроизведение файла'
instruction_2 = 'p - приостановить/возобновить'
instruction_3 = 'c + 12... + m - перейти к странице'
instruction_4 = 'i - прослушать инструкцию'
instruction_5 = 'q - закрыть окно программы'

header_font = pygame.font.SysFont('arial', 50)
text_font = pygame.font.SysFont('arial', 40)
text_color = (0, 0, 0)

text_header = header_font.render(instruction_header, True, text_color)
text_1 = text_font.render(instruction_1, True, text_color)
text_2 = text_font.render(instruction_2, True, text_color)
text_3 = text_font.render(instruction_3, True, text_color)
text_4 = text_font.render(instruction_4, True, text_color)
text_5 = text_font.render(instruction_5, True, text_color)

# Текущая позиция в текстовом файле:
position = f'Страница {cur_page + 1} из {n_pages}'
position_display = header_font.render(position, True, text_color)

# Событие, выполняемое по окончании воспроизведения аудио:
audio_finished = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(audio_finished)

# Звуковое сопровождение интерфейса (инструкция для пользователя):
audio_instruction = '''Для начала прослушивания текста нажмите клавишу s.
Для остановки и возобновления прослушивания используйте клавишу p.
В нижней части окна отображается номер текущей страницы.
Переход к следующей странице производится автоматически.
При этом может возникать пауза в пределах одной-двух секунд.
Вы можете изменить номер страницы. Для этого остановите воспроизведение файла,
нажмите клавишу c. Введите нужный номер страницы и проверьте, что он корректно
отображается в нижней части окна. Ошибочно введенное число можно отменить клавишей Backspace.
Завершив ввод, нажмите клавишу m - чтение возобновится с указанной страницы.
Для выхода из программы нажмите клавишу q.'''


def window_contents():
    """Функция наполняет окно программы текстом и виджетами."""
    screen.fill((166, 230, 247))
    # Виджет в нижней части экрана для отображения текущей страницы:
    w = position_display.get_width()
    h = position_display.get_height()
    pygame.draw.rect(screen, (83, 130, 207), (0, 520, width, h + 40))
    pygame.draw.rect(screen, (255, 255, 255), (190, 530, w + 20, h + 20))
    # Инструкция для пользователя и строка с номером текущей страницы:
    screen.blit(text_header, (50, 40))
    screen.blit(text_1, (80, 130))
    screen.blit(text_2, (80, 210))
    screen.blit(text_3, (80, 290))
    screen.blit(text_4, (80, 370))
    screen.blit(text_5, (80, 450))
    screen.blit(position_display, (200, 540))
    pygame.display.flip()


def page_entry() -> str:
    """Функция обрабатывает пользовательский ввод номера страницы
    с клавиатуры. Вызывается нажатием клавиши 'c'. Формирует и
    возвращает строку, содержащую номер страницы. Сигналом
    к завершению ввода служит нажатие клавиши 'm'."""

    global position_display

    new_page = ''

    typing = True
    while typing:

        for page_event in pygame.event.get():

            if page_event.type == pygame.KEYDOWN:

                if page_event.key == pygame.K_m:  # Окончание ввода номера страницы
                    typing = False

                elif page_event.key == pygame.K_BACKSPACE:  # Убрать последний введенный символ
                    if len(new_page) > 0:
                        new_page = new_page[:-1]
                        position = f'Страница {new_page} из {n_pages}'
                        position_display = header_font.render(position, True, text_color)
                        window_contents()

                else:  # Ввод номера страницы
                    entry = pygame.key.name(page_event.key)

                    if len(entry) == 3 and entry[1] in '0123456789':
                        new_page += entry[1]
                        position = f'Страница {new_page} из {n_pages}'
                        position_display = header_font.render(position, True, text_color)
                        window_contents()

    return new_page


def check_page(page: str):
    """Функция проверяет корректность введенной пользователем страницы."""
    # Если пользователь ввел номер страницы,
    # проверяем, что такая страница есть в файле:

    global cur_page, audio_file, pause

    if len(page) > 0:
        new_ind = int(page) - 1

        if 0 <= new_ind <= n_pages - 1:
            cur_page = new_ind
            speak(f'Перехожу к странице {page}')
            audio_file.close()
            text_to_audio_file()
            audio_file = open('reader_audio.wav')
            play_audio()
            pause = False

        else:
            speak(f'В файле нет страницы {page}. Нажмите c, введите номер страницы. В конце нажмите m.')
    # Если получена пустая строка:
    else:
        speak('Не указан номер страницы. Нажмите c, введите номер страницы. В конце нажмите m.')


def next_page():
    """Функция осуществляет переход к следующей странице
    при завершении воспроизведения аудиофайла текущей страницы."""

    global cur_page, position_display, audio_file

    cur_page += 1
    position = f'Страница {cur_page + 1} из {n_pages}'
    position_display = header_font.render(position, True, text_color)
    audio_file.close()
    text_to_audio_file()
    audio_file = open('reader_audio.wav')
    play_audio()


def window_manager():
    """Функция обеспечивает воспроизведение аудиофайла,
    мониторинг страниц текста и их преобразование в аудио,
    обрабатывает команды пользовательского ввода с клавиатуры."""

    clock = pygame.time.Clock()

    done = False
    while not done:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                done = True

            # Пользовательский ввод команд с клавиатуры:
            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_s:  # 's' - начать воспроизвдение
                    play_audio()

                elif event.key == pygame.K_p:  # 'p' - приостановить/возобновить
                    pause_audio()

                elif event.key == pygame.K_i:  # 'i' - прослушать инструкцию
                    speak(audio_instruction)

                elif event.key == pygame.K_q:  # 'q' - закрыть окно программы
                    done = True

                elif event.key == pygame.K_c:  # 'c' - изменить текущую страницу
                    # Обрабатываем пользовательский ввод:
                    new_page = page_entry()
                    # Проверяем корректность полученного номера:
                    check_page(new_page)

            # Завершение воспроизведения текущей страницы:
            elif event.type == audio_finished:
                # Если это не последняя страница текста:
                if cur_page < n_pages - 1:
                    next_page()
                else:
                    done = True

        window_contents()
        clock.tick(30)


# Запуск функции управления окном пользовательского интерфейса:
window_manager()

# Завершение процессов после закрытия окна:
pygame.quit()
audio_file.close()

# Обновляем индекс текущей страницы в памяти ридера:
if cur_page < n_pages - 1:
    memory[file_path] = cur_page
# Если файл прослушан до последней страницы, удаляем ссылку:
else:
    if file_path in memory:
        del memory[file_path]

with open('reader_memory.json', 'w') as f:
    json.dump(memory, f, indent=2)
