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

exit = False
quit = False
pipe = None  # Глобальная переменная для канала pipe

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
    print("2")
    while not quit:
        try:            
            msg = ''
            rtnvalue, data = win32file.ReadFile(handle, 256, pywintypes.OVERLAPPED())
            print(f'The rtnvalue is {rtnvalue}')    
            while rtnvalue == 234:
                msg = msg + bytes(data).decode(encoding='unicode_escape') 
                rtnvalue, data = win32file.ReadFile(handle, 256, pywintypes.OVERLAPPED())               
            if rtnvalue == 0: 
                msg = msg + bytes(data).decode(encoding='unicode_escape')
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
def choose_file():
    root = tk.Tk()
    root.withdraw()  
    file_path = filedialog.askopenfilename()  
    if file_path:
        print("Выбранный файл:", file_path)
        entry_path.delete(0, tk.END)
        entry_path.insert(0, file_path)

# Загрузка файла
####################################################################################
def start_command():
    global pipe  # Используем глобальный pipe
    file_path = entry_path.get()
    if file_path and pipe:
        some_data = str.encode(f"LoadLE", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data)
        some_data = str.encode(file_path, encoding='UTF-8')
        win32file.WriteFile(pipe, some_data)
        # Ваш код для выполнения команды "LoadLE" с выбранным файлом
        print("Выполнена команда LoadLE с файлом:", file_path)
        message.config(text=f"Выполнена команда LoadLE с файлом: {file_path}")
        # Читаем ответ из pipe
        response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
        if response == 0:  # NO_ERROR
            decoded_data = data.decode('UTF-8')  # Декодируем в строку
            print("Ответ от сервера:", decoded_data)
            message.config(text=f"Ответ от сервера: {decoded_data}")
        else:
            print(f"Ошибка при чтении ответа: код {response}")
    elif not file_path:
        message.config(text="")  # Устанавливаем пустую строку, чтобы очистить текущий текст
        print("Файл не выбран")
        message.config(text=f"Файл не выбран")
    elif not pipe:
        message.config(text="")  # Устанавливаем пустую строку, чтобы очистить текущий текст
        print("Подключение к серверу не установлено")
        message.config(text=f"Подключение к серверу не установлено")
####################################################################################


# Страрт команда
####################################################################################

def start_cutting():
    global pipe  # Используем глобальный pipe
    new_value = entry_movement.get()
    if pipe:
        # Команда на перемещение
        some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data_cmd)
        some_data_cmd = str.encode(f"Movemant_left.DistanceL={new_value}", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data_cmd)
        message.config(text="")  # Устанавливаем пустую строку, чтобы очистить текущий текст
        message.config(text=f"Переместить стол на {new_value}")

        # ответ на пермещение
        response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
        if response == 0:  # NO_ERROR
            decoded_data = data.decode('UTF-8')  # Декодируем в строку
            print("Ответ от сервера:", decoded_data)
        else:
            print(f"Ошибка при чтении ответа: код {response}")

        '''
        # Команда резка
        some_data = str.encode(f"Start mark", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data)
        message.config(text="")  # Устанавливаем пустую строку, чтобы очистить текущий текст
        message.config(text=f"Начать резку")
        '''
        
    
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



if __name__ == '__main__':  
    # Создание графического интерфейса
    root = tk.Tk()
    root.title("Графический интерфейс")
    root.geometry("500x400")  # Размер окна
    root.resizable(False, False)  # Фиксированный размер окна

    # Основная рамка
    frame_main = ttk.Frame(root, padding=10)
    frame_main.pack(fill="both", expand=True)

    # Заголовок
    label_title = ttk.Label(frame_main, text="Управление процессом", font=("Arial", 16, "bold"))
    label_title.pack(pady=10)

    # Кнопка для выбора файла
    button_choose = ttk.Button(frame_main, text="Выбрать файл", command=choose_file)
    button_choose.pack(pady=5, fill="x")

    # Поле ввода для отображения выбранного пути к файлу
    entry_path = ttk.Entry(frame_main, width=50)
    entry_path.pack(pady=5, fill="x")

    # Кнопка "Открыть файл"
    button_start = ttk.Button(frame_main, text="Открыть файл", command=start_command)
    button_start.pack(pady=5, fill="x")

    # Поле ввода для ввода переменной changing
    entry_changing = ttk.Entry(frame_main, width=50)
    entry_changing.pack(pady=5, fill="x")

    # Кнопка "Преобразовать"
    button_execute = ttk.Button(frame_main, text="Исполнить команду", command=execute_set_new_value)
    button_execute.pack(pady=5, fill="x")

    # Поле ввода для отображения выбранного пути к файлу
    entry_movement = ttk.Entry(frame_main, width=50)
    entry_movement.pack(pady=5, fill="x")

    # Кнопка "Старт"
    button_start_cut = ttk.Button(frame_main, text="Старт", command=start_cutting)
    button_start_cut.pack(pady=5, fill="x")

    # Разделитель
    separator = ttk.Separator(frame_main, orient="horizontal")
    separator.pack(fill="x", pady=10)

    # Консоль
    message = ttk.Label(frame_main, text="Сообщений нет", relief="sunken", anchor="w", padding=5)
    message.pack(fill="x", pady=5, expand=True)
    
    # Запуск потоков
    x = threading.Thread(target=thread_start)  
    x.start()
    time.sleep(7)
    server_thread = threading.Thread(target=pipe_server)
    server_thread.start()
    time.sleep(1) 
    client_thread = threading.Thread(target=pipe_client)
    client_thread.start()
    root.mainloop()  # Запуск главного цикла Tkinter
    server_thread.join()
    client_thread.join()
