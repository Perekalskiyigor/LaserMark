from elevate import elevate

# Запросить права администратора
elevate()

import tkinter as tk
from tkinter import filedialog
import time
import sys
import win32pipe
import win32file
import pywintypes
import threading
import os
import subprocess
from pathlib import Path
from tkinter import ttk
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk

exit = False
quit = False
pipe = None  # Глобальная переменная для канала pipe

file_path = "" # Глобальная переменная для пути

message1 = ""

pause_event = threading.Event()
pause_event.set()  # Устанавливаем событие как активное

def thread_start():
    print("thread_start_1")
    # Получаем путь к текущей директории
    current_directory = os.getcwd()
    # Формируем путь к исполняемому файлу MaxiGraf.exe
    maxigraf_exe_path = os.path.join(current_directory, "MaxiGraf.exe")

    # Запускаем MaxiGraf.exe из текущей директории
    subprocess.Popen([maxigraf_exe_path, "PipeU", "MaxiGrafPipe"], stdout=subprocess.PIPE)  
    print("thread_start_2")
    

def ThreadForBackServer(handle):
    global quit
    quit = False
    global message1
    print("2")
    while not quit:
        try:            
            msg = ''
            rtnvalue, data = win32file.ReadFile(handle, 256, pywintypes.OVERLAPPED())
            print(f'The rtnvalue is {rtnvalue}')    
            while rtnvalue == 234:
                msg = msg + bytes(data).decode(encoding='utf-8', errors='replace')
                message1 = msg
                rtnvalue, data = win32file.ReadFile(handle, 256, pywintypes.OVERLAPPED())               
            if rtnvalue == 0:
                msg = msg + bytes(data).decode(encoding='utf-8', errors='replace')
                message1 = msg
                print(msg)               
            print(msg)
        except pywintypes.error as e:
            if e.args[0] == 2:
                print("no pipe, trying again in a sec")
                time.sleep(1)
            elif e.args[0] == 109:
                print("broken pipe, bye bye")
                quit = True
                global exit
                exit = True
    print(exit)
    print("3")   

# Запуск серверного потока
####################################################################################
def pipe_server():
    global pipe  # Делаем pipe глобальным
    print("pipe server")
    global exit
    pipe = win32pipe.CreateNamedPipe(
        r'\\.\pipe\MaxiGrafPipe',
        win32pipe.PIPE_ACCESS_DUPLEX,
        win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
        1, 65536, 65536,
        0,
        None)
    try:
        print("waiting for client")
        win32pipe.ConnectNamedPipe(pipe, None)
        print("got client")
        while exit is False:
            print(exit)           
            mes = input('Enter your command:')
            print(mes)

            if mes == "Quit":     
                some_data = str.encode(f"Bay-Bay", encoding='UTF-8')
                win32file.WriteFile(pipe, some_data)
                global quit
                quit = True                
                exit = True
            elif mes == "Start":
                some_data = str.encode(f"Start mark", encoding='UTF-8')
                win32file.WriteFile(pipe, some_data)
            # Остальные условия команд здесь
    finally:
        win32file.CloseHandle(pipe)

# Виджет получения пути к файлу
####################################################################################       
"""
def choose_file():
    root = tk.Tk()
    root.withdraw()  
    file_path = filedialog.askopenfilename()  
    if file_path:
        print("Выбранный файл:", file_path)
        entry_path.delete(0, tk.END)
        entry_path.insert(0, file_path)
"""





# Страрт команда
####################################################################################

# Запускаем как отделный поток, нужно дляобновления интерфейса
def start_cutting():
    global pipe  # Используем глобальный pipe
    new_value = entry_movement.get()
    if pipe:
        # Запускаем процесс в отдельном потоке
        thread = threading.Thread(target=cutting_process, args=(new_value,), daemon=True)
        thread.start()

def cutting_process(new_value):
    global message1
    # new_value = entry_movement.get()
    for i in range(1, 11):  # Цикл из 10 итераций
        while True:  # Ожидаем данных, не пропуская итерации
            
            # Симуляция получения данных
            # response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            #if response == 0:  # NO_ERROR
            #decoded_data = data.decode('UTF-8')  # Декодируем в строку
            #print("Ответ от сервера:", decoded_data)
            if "ErrorFromControler" not in message1:  # Если данные получены, выходим из ожидания
                break
            print("Оборудование отключено Ждем данные...")
            time.sleep(1)  # Ожидание перед повторной попыткой

        time.sleep(3)  # Ожидание перед выполнением действий

        if i % 2 == 0:  # Четная итерация

            
            # Команда на перемещение
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Movemant_left.DistanceL={new_value}", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            
            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
                message.config(text=f"Перемещение: {decoded_data}")
            else:
                print(f"Ошибка при чтении ответа: код {response}")

            update_message(f"Переместить стол на {new_value}")
            print(f"Переместить стол на {new_value}")

            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)
            update_message(f"Режем на {i} итерации")

            

            print(f"*****-{message1}")
            time.sleep(3)

            # Проверяем, завершилась ли операция маркировки успешно первая
            while "MarkingCompletedSuccessfully" not in message1:
                print("Ожидаем завершения резки...")
                time.sleep(1)
                update_message(f"Резка на {i} итерации завершена")

        else:  # Нечетная итерация
            # Команда на перемещение
            some_data_cmd = str.encode("Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            movement_cmd = str.encode("Movemant_left.DistanceL=0", encoding='UTF-8')
            win32file.WriteFile(pipe, movement_cmd)
            
            

            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode(encoding='unicode_escape')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
                message.config(text=f"Перемещение: {decoded_data}")
            else:
                print(f"Ошибка при чтении ответа: код {response}")


            update_message("Переместить стол на 0")
            print("Переместить стол на 0")

            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)
            update_message(f"Режем на {i} итерации")

            update_message(f"Резка на {i} итерации завершена")

            print(f"*****-{message1}")
            time.sleep(3)


            # Проверяем, завершилась ли операция маркировки успешно первая
            while "MarkingCompletedSuccessfully" not in message1:
                print("Ожидаем завершения резки...")
                time.sleep(1)
                update_message(f"Резка на {i} итерации завершена")


            
            '''
            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)

            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode(encoding='unicode_escape')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
                message.config(text=f"Резка: {decoded_data}")
            else:
                print(f"Ошибка при чтении ответа: код {response}")

            update_message("Резка завершена")
            print("Резка")
            '''
        message1 = ""
    print(f"***///////{message1}")

    print("ФИНИШ резки")
    update_message(f"Резка завершена")

            
            
# Обновляем поля интрефейса    
def update_message(text):
    # Обновляем текст в метке из основного потока
    message.after(0, lambda: message.config(text=text))
                
        
#########################################################################################################    


# Установка нового значения
######################################################################################################### 

def execute_set_new_value():
    global pipe  # Используем глобальный pipe
    new_value = entry_changing.get()
    if pipe:
        some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data_cmd)
        some_data_value = str.encode(new_value, encoding='UTF-8')
        win32file.WriteFile(pipe, some_data_value)
        print(some_data_value)
        message.config(text="")  # Устанавливаем пустую строку, чтобы очистить текущий текст
        message.config(text=f"Выполнена комада Set new Value={some_data_value}")

        # Читаем ответ из pipe
        response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
        if response == 0:  # NO_ERROR
            decoded_data = data.decode('UTF-8')  # Декодируем в строку
            print("Ответ от сервера:", decoded_data)
        else:
            print(f"Ошибка при чтении ответа: код {response}")
        # Ваш код для выполнения команды "Set new Value"
        print("Команда Set new Value выполнена с новым значением:", new_value)
    else:
        print("Подключение к серверу не установлено")

######################################################################################################### 

# Запуск клиента
######################################################################################################### 
def pipe_client():
    print("pipe client")
    connect = True   
    while connect:
        try:      
            handle = win32file.CreateFile(
                r'\\.\pipe\BackMaxiGrafPipe',
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            if connect:
                msg = ''
                rtnvalue, data = win32file.ReadFile(handle, 256, pywintypes.OVERLAPPED())
                while rtnvalue == 234:
                    msg = msg + bytes(data).decode(encoding='unicode_escape') 
                    rtnvalue, data = win32file.ReadFile(handle, 256, pywintypes.OVERLAPPED())
                    print(msg)
                if rtnvalue == 0:
                    msg = msg + bytes(data).decode(encoding='unicode_escape')
                    print(msg)
                print(f'The rtnvalue is {rtnvalue}')    
                print(f'The message is {msg}' + ' .end')
                some_data = str.encode("Yes I can do BakcMaxiGrafPipe")
                win32file.WriteFile(handle, some_data)            
                print("Yes I can do BakcMaxiGrafPipe")
                if connect:
                    print("1")                    
                    x = threading.Thread(target=ThreadForBackServer, args=(handle,))  
                    x.daemon = True
                    x.start()                     
                    pipe_server()  
                    print("4")
                    connect = False
        except pywintypes.error as e:
            if e.args[0] == 2:
                print("try again for a while")
                time.sleep(1)
                connect = False
            elif e.args[0] == 109:
                print("broken pipe, bye bye")
                connect = False
######################################################################################################### 



####################### ФУНКЦИИ ИНТЕРФЕЙСА #######################



# выбор шаблона
####################################################################################
def load_template():
    global file_path
    print('работает комагнда выбора шаблона')
    # Открываем диалог для выбора файла
    file_path = filedialog.askopenfilename(title="Выберите шаблон", filetypes=[("Текстовые файлы", "*.le")])
    if file_path:
        template_label.config(text=f"Выбран шаблон: {file_path.split('/')[-1]}")
        load_status_label.config(text="Шаблон загружен", fg="green")
        
        # Проверяем, содержит ли имя файла слово "module" нужно чтобы понять, что шаблон требует нумерации
        if "module" in file_path.split('/')[-1].lower():
            template_label.config(text=f"Выбранный шаблон: {file_path.split('/')[-1]}")
            load_status_label.config(text="Внимание, шаблон требует введение нумерации", fg="red")
            entry_numbering.config(state="normal")  # Делаем поле ввода нумерации доступным
        else:
            entry_numbering.config(state="disabled")  # Делаем поле ввода нумерации недоступным

    else:
        messagebox.showwarning("Ошибка", "Шаблон не выбран.")
    print(f'полученный путь{file_path}')
    return file_path
####################################################################################




# Загрузка в программу
####################################################################################
def setTamplate():
    global file_path
    # print(f'********{file_path}')
    global pipe  # Используем глобальный pipe
    if file_path and pipe:
        some_data = str.encode(f"LoadLE", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data)
        some_data = str.encode(file_path, encoding='UTF-8')
        win32file.WriteFile(pipe, some_data)
        # Ваш код для выполнения команды "LoadLE" с выбранным файлом
        print("Выполнена команда LoadLE с файлом:", file_path)
        # Читаем ответ из pipe
        response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
        if response == 0:  # NO_ERROR
            decoded_data = data.decode('UTF-8')  # Декодируем в строку
            print("Ответ от сервера:", decoded_data)
            status_label.config(text=f"Шаблон {file_path.split('/')[-1]} загружен", fg="green")
        else:
            status_label.config(text=f"Шаблон не загружен. Ошибка: {response}", fg="red")
            print(f"Ошибка при чтении ответа: код {response}")
    elif not file_path:
        status_label.config(text=f"Невозможно получить путь к шаблону", fg="red")
        print("Невозможно получить путь к шаблону")
    elif not pipe:
        status_label.config(text=f"Подключение к программе маркировки потеряно", fg="red")
        print("Подключение к серверу не установлено")
####################################################################################







# Страрт команда
####################################################################################

# Запускаем как отделный поток, нужно дляобновления интерфейса
def start_cutting():
    global pipe  # Используем глобальный pipe
    new_value = entry_movement.get()
    if pipe:
        # Запускаем процесс в отдельном потоке
        thread = threading.Thread(target=cutting_process, args=(new_value,), daemon=True)
        thread.start()

def cutting_process(new_value):
    global message1
    # new_value = entry_movement.get()
    for i in range(1, 11):  # Цикл из 10 итераций
        while True:  # Ожидаем данных, не пропуская итерации
            
            # Симуляция получения данных
            # response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            #if response == 0:  # NO_ERROR
            #decoded_data = data.decode('UTF-8')  # Декодируем в строку
            #print("Ответ от сервера:", decoded_data)
            if "ErrorFromControler" not in message1:  # Если данные получены, выходим из ожидания
                break
            print("Оборудование отключено Ждем данные...")
            time.sleep(1)  # Ожидание перед повторной попыткой

        time.sleep(3)  # Ожидание перед выполнением действий

        if i % 2 == 0:  # Четная итерация

            
            # Команда на перемещение
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Movemant_left.DistanceL={new_value}", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            
            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
                message.config(text=f"Перемещение: {decoded_data}")
            else:
                print(f"Ошибка при чтении ответа: код {response}")

            update_message(f"Переместить стол на {new_value}")
            print(f"Переместить стол на {new_value}")

            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)
            update_message(f"Режем на {i} итерации")

            

            print(f"*****-{message1}")
            time.sleep(3)

            # Проверяем, завершилась ли операция маркировки успешно первая
            while "MarkingCompletedSuccessfully" not in message1:
                print("Ожидаем завершения резки...")
                time.sleep(1)
                update_message(f"Резка на {i} итерации завершена")

        else:  # Нечетная итерация
            # Команда на перемещение
            some_data_cmd = str.encode("Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            movement_cmd = str.encode("Movemant_left.DistanceL=0", encoding='UTF-8')
            win32file.WriteFile(pipe, movement_cmd)
            
            

            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode(encoding='unicode_escape')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
                message.config(text=f"Перемещение: {decoded_data}")
            else:
                print(f"Ошибка при чтении ответа: код {response}")


            update_message("Переместить стол на 0")
            print("Переместить стол на 0")

            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)
            update_message(f"Режем на {i} итерации")

            update_message(f"Резка на {i} итерации завершена")

            print(f"*****-{message1}")
            time.sleep(3)


            # Проверяем, завершилась ли операция маркировки успешно первая
            while "MarkingCompletedSuccessfully" not in message1:
                print("Ожидаем завершения резки...")
                time.sleep(1)
                update_message(f"Резка на {i} итерации завершена")


            
            '''
            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)

            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode(encoding='unicode_escape')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
                message.config(text=f"Резка: {decoded_data}")
            else:
                print(f"Ошибка при чтении ответа: код {response}")

            update_message("Резка завершена")
            print("Резка")
            '''
        message1 = ""
    print(f"***///////{message1}")

    print("ФИНИШ резки")
    update_message(f"Резка завершена")

            
            
# Обновляем поля интрефейса    
def update_message(text):
    # Обновляем текст в метке из основного потока
    message.after(0, lambda: message.config(text=text))
                
        
#########################################################################################################    

def start_cutting():
    global pipe  # Используем глобальный pipe
    new_value = entry_movement.get()
    if pipe:
        # Запускаем процесс в отдельном потоке
        thread = threading.Thread(target=cutting_process, args=(new_value,), daemon=True)
        thread.start()


def start_processing():
    pass

def execute_command():
    pass

def show_about():
    about_window = tk.Toplevel(root)
    about_window.title("О программе")
    about_window.geometry("400x300")
    
    label_info = tk.Label(about_window, text="Версия: 1.0\nРазработчик: Конструкторско-технологический отдел", font=("Arial", 12))
    label_info.pack(pady=20)
    
    button_close = tk.Button(about_window, text="Закрыть", command=about_window.destroy)
    button_close.pack(pady=10)


if __name__ == '__main__':  
    # Создание графического интерфейса
    # Создаем главное окно
    root = tk.Tk()
    root.title("Дружелюбный интерфейс")
    root.geometry("500x800")

    # Создаем вкладки
    tab_control = ttk.Notebook(root)
    tab_main = ttk.Frame(tab_control)
    tab_about = ttk.Frame(tab_control)

    # Добавляем вкладки в контроль
    tab_control.add(tab_main, text="Главная")
    tab_control.add(tab_about, text="О программе")
    tab_control.pack(expand=1, fill="both")

    # Вкладка "Главная"
    # Загружаем логотип
    logo = Image.open("logo.png")  # Замените на путь к своему логотипу
    logo = logo.resize((100, 100), Image.Resampling.LANCZOS)
    logo_img = ImageTk.PhotoImage(logo)

    # Создаем лейбл для логотипа
    logo_label = tk.Label(tab_main, image=logo_img)
    logo_label.pack(pady=10)

    # Текстовые подсказки
    label_title = tk.Label(tab_main, text="Загрузите шаблон и настройте параметры", font=("Arial", 14))
    label_title.pack(pady=10)

    # Кнопка выбора шаблона
    button_select_template = tk.Button(tab_main, text="Выбрать шаблон", command=load_template)
    button_select_template.pack(pady=10)

    # Метка для отображения выбранного шаблона
    template_label = tk.Label(tab_main, text="Шаблон не выбран", font=("Arial", 10))
    template_label.pack(pady=5)

    # Кнопка загрузки шаблона
    button_load_template = tk.Button(tab_main, text="Загрузить шаблон", command=setTamplate)
    button_load_template.pack(pady=10)

    # Метка для отображения статуса загрузки шаблона
    load_status_label = tk.Label(tab_main, text="Шаблон не загружен", font=("Arial", 10), fg="red")
    load_status_label.pack(pady=5)

    # Поле ввода для количества
    label_count = tk.Label(tab_main, text="Введите количество:")
    label_count.pack(pady=5)
    entry_count = tk.Entry(tab_main)
    entry_count.pack(pady=5)

    # Поле ввода для нумерации
    label_numbering = tk.Label(tab_main, text="Введите нумерацию:")
    label_numbering.pack(pady=5)
    entry_numbering = tk.Entry(tab_main)
    entry_numbering.pack(pady=5)

    # Поле для ввода команды
    label_command = tk.Label(tab_main, text="Введите команду:")
    label_command.pack(pady=5)
    entry_command = tk.Entry(tab_main)
    entry_command.pack(pady=5)

    # Кнопка для выполнения команды
    button_execute_command = tk.Button(tab_main, text="Выполнить команду", command=execute_command)
    button_execute_command.pack(pady=10)

    # Кнопка для старта
    button_start = tk.Button(tab_main, text="Старт", command=start_processing)
    button_start.pack(pady=20)

    # Лейбл для состояния
    status_label = tk.Label(tab_main, text="Статус: Ожидание", font=("Arial", 12))
    status_label.pack(pady=10)

    # Настроим анимацию GIF (запущено и не запущено)
    gif_not_running = Image.open("gif_not_running.png")  # Путь к анимации для "не запущено"
    gif_running = Image.open("gif_running.png")  # Путь к анимации для "запущено"
    gif_not_running = gif_not_running.resize((100, 100), Image.Resampling.LANCZOS)
    gif_running = gif_running.resize((100, 100), Image.Resampling.LANCZOS)

    gif_not_running_img = ImageTk.PhotoImage(gif_not_running)
    gif_running_img = ImageTk.PhotoImage(gif_running)

    # Создаем лейбл для отображения GIF
    current_gif_label = tk.Label(tab_main, image=gif_not_running_img)
    current_gif_label.pack(pady=10)

    # Вкладка "О программе"
    # Здесь можно добавить текст или информацию о программе
    label_about = tk.Label(tab_about, text="Версия: 1.0\nРазработчик: Конструкторско-технологический отдел", font=("Arial", 14))
    label_about.pack(pady=50)
    
    # Запуск потоков
    x = threading.Thread(target=thread_start)  
    x.start()
    time.sleep(10)
    server_thread = threading.Thread(target=pipe_server)
    server_thread.start()
    time.sleep(1) 
    client_thread = threading.Thread(target=pipe_client)
    client_thread.start()
    root.mainloop()  # Запуск главного цикла Tkinter
    server_thread.join()
    client_thread.join()