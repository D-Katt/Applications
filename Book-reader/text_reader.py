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


# Звуковое сопровождение интерфейса:
engine = pyttsx3.init()
t1 = threading.Thread(target=speak, args=['Выберите текстовый файл.'])
t1.start()

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
t1.join()
speak('Выполняется обработка.')


def load_text(path: str):
    """Функция извлекает текст из файла
    и преобразует в список строк постранично."""

    global content, n_pages

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

        # Для файлов в формате .pdf и аналогичных:
        elif extension in ['.pdf', '.xps', '.oxps', '.epub', '.cbz', '.fb2']:
            doc = fitz.open(path)
            n_pages = doc.pageCount

            for page in range(n_pages):
                cur_page = doc.loadPage(page)
                cur_text = cur_page.getText('text')
                content.append(cur_text)

    # При возникновении ошибок обработки файла, озвучиваем
    # рекомендацию для пользователя и завершаем программу:
    except Exception as e:
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


def change_page():
    """Функция изменяет номер текущей страницы.
    Вызывается нажатием клавиши 'm' на клавиатуре."""
    global cur_page
    new_page = ''


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

text_header = header_font.render(instruction_header, True, (0, 0, 0))
text_1 = text_font.render(instruction_1, True, (0, 0, 0))
text_2 = text_font.render(instruction_2, True, (0, 0, 0))
text_3 = text_font.render(instruction_3, True, (0, 0, 0))
text_4 = text_font.render(instruction_4, True, (0, 0, 0))
text_5 = text_font.render(instruction_5, True, (0, 0, 0))

# Текущая позиция в текстовом файле:
position = f'Страница {cur_page + 1} из {n_pages}'
position_display = header_font.render(position, 1, (0, 0, 0))

# Событие, выполняемое по окончании воспроизведения аудио:
SONG_FINISHED = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(SONG_FINISHED)

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


def window_manager():
    """Функция обеспечивает воспроизведение аудиофайла,
    мониторинг страниц текста и их преобразование в аудио,
    обрабатывает команды пользовательского ввода с клавиатуры."""

    global cur_page, position_display, audio_file, pause

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

                elif event.key == pygame.K_c:  # 'm' - изменить текущую страницу
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
                                        position_display = header_font.render(position, 1, (0, 0, 0))
                                        window_contents()

                                else:  # Ввод номера страницы
                                    entry = pygame.key.name(page_event.key)

                                    if len(entry) == 3 and entry[1] in '0123456789':
                                        new_page += entry[1]
                                        position = f'Страница {new_page} из {n_pages}'
                                        position_display = header_font.render(position, 1, (0, 0, 0))
                                        window_contents()

                    # Если пользователь ввел номер страницы,
                    # проверяем, что такая страница есть в файле:
                    if len(new_page) > 0:
                        new_ind = int(new_page) - 1

                        if new_ind <= n_pages - 1:
                            cur_page = int(new_page) - 1
                            speak(f'Перехожу к странице {new_page}')
                            audio_file.close()
                            text_to_audio_file()
                            audio_file = open('reader_audio.wav')
                            play_audio()
                            pause = False

                        else:
                            speak(f'В файле нет страницы {new_page}. Нажмите c, введите номер страницы. В конце нажмите m.')
                    # Если получена пустая строка:
                    else:
                        speak('Не указан номер страницы. Нажмите c, введите номер страницы. В конце нажмите m.')

            # Завершение воспроизведения текущей страницы:
            elif event.type == SONG_FINISHED:
                cur_page += 1
                position = f'Страница {cur_page + 1} из {n_pages}'
                position_display = header_font.render(position, 1, (0, 0, 0))
                audio_file.close()
                text_to_audio_file()
                audio_file = open('reader_audio.wav')
                play_audio()

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
