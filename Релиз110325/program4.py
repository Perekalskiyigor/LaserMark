import logging

# Set up logging to file
logging.basicConfig(
    level=logging.DEBUG,  # Adjust the logging level as needed
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('app_log.log'), logging.StreamHandler()]
)

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

import API_1C # Модуль запроса к апи плм для сохранения шаблона
import SQLSerialProvider # Модуль получения серийников из БД
import getPathAPI # Сохранение шаблона в папку
import Authorization # Модуль с авторизациями
import SentLog1C # Отпарвка отчета в 1С

exit = False
quit = False
pipe = None  # Глобальная переменная для канала pipe

file_path = "" # Глобальная переменная для пути

message1 = ""

login_user = "" # Глобальная переменная для хранения пользователя текущего, передаем в базу

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



# выбор шаблона Обычного вручную
####################################################################################
def load_template():
    global file_path
    print('работает комагнда выбора шаблона')
    # Открываем диалог для выбора файла
    file_path = filedialog.askopenfilename(title="Выберите шаблон", filetypes=[("Текстовые файлы", "*.le")])
    if file_path:
        template_label_plm.config(text=f"Выбран шаблон: {file_path.split('/')[-1]}", fg="green")
        template_label.config(text=f"Выбран шаблон: {file_path.split('/')[-1]}", fg="green")
        load_status_label_plm.config(text="Шаблон готов к загрузке", fg="green")
        load_status_label.config(text="Шаблон готов к загрузке", fg="green")
        
        # Проверяем, содержит ли имя файла слово "module" нужно чтобы понять, что шаблон требует нумерации
        if "module" in file_path.split('/')[-1].lower():
            template_label_plm.config(text=f"Выбранный шаблон: {file_path.split('/')[-1]}")
            template_label.config(text=f"Выбранный шаблон: {file_path.split('/')[-1]}")
            load_status_label_plm.config(text="Внимание, шаблон требует введение нумерации", fg="red")
            load_status_label.config(text="Внимание, шаблон требует введение нумерации", fg="red")
            entry_numbering_plm.config(state="normal")  # Делаем поле ввода нумерации доступным
            entry_numbering.config(state="normal")  # Делаем поле ввода нумерации доступным
        else:
            entry_numbering_plm.config(state="disabled")  # Делаем поле ввода нумерации недоступным
            entry_numbering.config(state="disabled")  # Делаем поле ввода нумерации недоступным

    else:
        messagebox.showwarning("Ошибка", "Шаблон не выбран.")
    print(f'полученный путь{file_path}')
    return file_path
####################################################################################


# выбор шаблона ПЛМ
####################################################################################
def load_templatePLM():
    logging.info(f">>>>>>>>COMAND - CHOOSE TEMPLATE def load_templatePLM()")
    global file_path
    print('работает команда выбора шаблона')
    
    # Устанавливаем начальную папку для выбора шаблона (в папке проекта в папке Templates)
    project_folder = os.path.dirname(os.path.abspath(__file__))  # Получаем путь к текущей папке проекта
    templates_folder = os.path.join(project_folder, 'Templates')  # Папка Templates внутри проекта
    
    # Открываем диалог для выбора файла в папке Templates
    file_path = filedialog.askopenfilename(title="Выберите шаблон", 
                                           filetypes=[("Текстовые файлы", "*.le")],
                                           initialdir=templates_folder)  # Указываем начальную папку
    
    if file_path:
        template_label_plm.config(text=f"Выбран шаблон: {file_path.split('/')[-1]}", fg="green")
        
        # Проверяем, содержит ли имя файла слово "module", чтобы понять, что шаблон требует нумерации
        if "module" in file_path.split('/')[-1].lower():
            template_label_plm.config(text=f"Выбранный шаблон: {file_path.split('/')[-1]}")
            load_status_label_plm.config(text="Внимание, шаблон требует введение нумерации", fg="red")
            entry_numbering_plm.config(state="normal")  # Делаем поле ввода нумерации доступным
        else:
            entry_numbering_plm.config(state="disabled")  # Делаем поле ввода нумерации недоступным

    else:
        messagebox.showwarning("Ошибка", "Шаблон не выбран.")
    
    print(f'полученный путь: {file_path}')
    return file_path
####################################################################################



# Загрузка в программу
####################################################################################
def setTamplate():
    logging.info(f">>>>>>>>COMAND - SET TEMPLATE def def setTamplate()")
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
        load_status_label_plm.config(text="Шаблон загружен", fg="green")
        response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
        if response == 0:  # NO_ERROR
            decoded_data = data.decode('UTF-8')  # Декодируем в строку
            print("Ответ от сервера:", decoded_data)
            status_label.config(text=f"Шаблон {file_path.split('/')[-1]} \nзагружен", fg="green")
        else:
            status_label.config(text=f"Шаблон не загружен. \nОшибка: {response}", fg="red")
            print(f"Ошибка при чтении ответа: код {response}")
    elif not file_path:
        status_label.config(text=f"Невозможно получить путь\n к шаблону", fg="red")
        print("Невозможно получить путь к шаблону")
    elif not pipe:
        status_label.config(text=f"Подключение к программе маркировки \nпотеряно", fg="red")
        print("Подключение к серверу не установлено")
####################################################################################



# Страрт команда гравировки
####################################################################################

# Запускаем как отделный поток, нужно дляобновления интерфейса
def start_cutting():
    global pipe  # Используем глобальный pipe
    new_value = 186 # Наскоько сдвинуть стол
    if pipe:
        # Запускаем процесс в отдельном потоке
        thread = threading.Thread(target=cutting_process, args=(new_value,), daemon=True)
        thread.start()

def cutting_process(new_value):
    global message1
    # Обновляем статус
    status_label.config(text="Статус:\n Запуск гравировки")

    # Кол-во деталей для маркировки
    try:
        # Проверяем, если поле entry_count пустое, то берем значение из entry_count_plm
        count = entry_count.get()
        # Если значение пустое, используем значение из entry_count_plm
        if not count:  # Если строка пустая
            count = entry_count_plm.get()
        # Преобразуем значение в целое число
        count = int(count) if count else 0  # Если значение пустое, то устанавливаем 0 как дефолт

    except ValueError:
        count = 1  # Если возникла ошибка, устанавливаем значение по умолчанию 1

    # Цикл из  итераций от однок до count
    for i in range(1, count):  
        
        time.sleep(3)  # Ожидание перед выполнением действий

        if i % 2 != 0:  #  Если четная итерация надо сдвинуть стол на 100 Movemant_left.DistanceL

            # Команда на перемещение
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Before_marking\\Movemant_left.DistanceL={new_value}", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
 
            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
            else:
                print(f"Ошибка при чтении ответа: код {response}")
                status_label.config(text=f"Ошибка:\n код {response}", fg="red")

            status_label.config(text=f"Статус:\nПереместить стол на {new_value}", fg="green")
            print(f"Переместить стол на {new_value}")

            # Обновляем изображение GIF
            current_gif_label.config(image=gif_running_img)
            current_gif_label_plm.config(image=gif_running_img)
            
            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)
            status_label.config(text=f"Статус:\nГравировка", fg="green")

            # print(f"*****-{message1}")
            time.sleep(3)
            

            # Цикл проверки. что оборудование подключено и данные мы получаем
            ####################
            while True:  
                
                # Симуляция получения данных
                # response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
                #if response == 0:  # NO_ERROR
                #decoded_data = data.decode('UTF-8')  # Декодируем в строку
                #print("Ответ от сервера:", decoded_data)
                if "ErrorFromControler" in message1:  # Если нет ошибок. все хорошо идем дальше
                    status_label.config(text="Статус:\n Нет соединения", fg="red")
                    print("Оборудование отключено Ждем данные...")
                else:
                    break
                time.sleep(1)  # Ожидание перед повторной попыткой
            ####################

            # Проверяем, завершилась ли операция маркировки успешно первая
            while "MarkingCompletedSuccessfully" not in message1:
                print("Ожидаем завершения резки...")
                status_label.config(text=f"Статус:\nОжидаем завершения резки...", fg="green")
                time.sleep(1)
                status_label.config(text=f"Статус:\n{i} иттерация гравировки", fg="green")

        else:  # Нечетная итерация
            # Команда на перемещение
            some_data_cmd = str.encode("Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            movement_cmd = str.encode("Before_marking\\Movemant_left.DistanceL=0", encoding='UTF-8')
            win32file.WriteFile(pipe, movement_cmd)
            
            

            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode(encoding='unicode_escape')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
            else:
                status_label.config(text=f"Ошибка:\n {response}", fg="red")
                print(f"Ошибка при чтении ответа: код {response}")


            status_label.config(text=f"Статус:\n Переместить стол на 0", fg="green")
            print("Переместить стол на 0")

            # Обновляем изображение GIF
            current_gif_label.config(image=gif_running_img)
            current_gif_label_plm.config(image=gif_running_img)
            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)
            print(f"*****-{message1}")
            time.sleep(3)
            
            ####################
            while True:  
                
                # Симуляция получения данных
                # response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
                #if response == 0:  # NO_ERROR
                #decoded_data = data.decode('UTF-8')  # Декодируем в строку
                #print("Ответ от сервера:", decoded_data)
                if "ErrorFromControler" in message1:  # Если нет ошибок. все хорошо идем дальше
                    status_label.config(text="Статус:\n Нет соединения", fg="red")
                    print("Оборудование отключено Ждем данные...")
                else:
                    print("Оборудование отключено Ждем данные...")
                    break
                    
                time.sleep(1)  # Ожидание перед повторной попыткой
            ####################

            # Проверяем, завершилась ли операция маркировки успешно первая
            while "MarkingCompletedSuccessfully" not in message1:
                print("Ожидаем завершения резки...")
                time.sleep(1)
                status_label.config(text=f"Статус:\n{i} итерация завершена", fg="green")

        message1 = ""
    print(f"***///////{message1}")

    # Обновляем изображение GIF
    current_gif_label.config(image=gif_not_running_img)
    current_gif_label_plm.config(image=gif_not_running_img)

    print("ФИНИШ резки")
    status_label.config(text=f"Статус:\nГравировка заверешена.\n ({i} деталей)", fg="green")

        
#########################################################################################################  


# Резка лицевых с доступом к бд
####################################################################################

# Запускаем как отделный поток, нужно дляобновления интерфейса
def start_cuttingPLM():
    logging.info(f">>>>>>>>COMAND - START CUTTING def start_cuttingPLM()")
    global pipe  # Используем глобальный pipe
    global login_user
    new_value = 186 # Наскоько сдвинуть стол
    if pipe:
        # Запускаем процесс в отдельном потоке
        thread = threading.Thread(target=cutting_processPLM, args=(new_value,), daemon=True)
        thread.start()

def cutting_processPLM(new_value):
    global message1
    global file_path # Путь до загруженного шаблона
    # Обновляем статус
    status_label_plm.config(text="Статус:\n Запуск гравировки")
    logging.info(f"Main - Start Cuting PLM")

    # Кол-во деталей для маркировки
    try:
        
        # Из модуля получить какой сейчас заказ и его айди
        OrderID, seril_id = SQLSerialProvider.extract_order_info(file_path)
        # Из модуля получить кол-во неотмаркированных среийников
        count = SQLSerialProvider.get_total_count(seril_id, OrderID)
        # Берем кол-во из бд
        # Преобразуем значение в целое число
        count = int(count) if count else 0  # Если значение пустое, то устанавливаем 0 как дефолт

        logging.info(f"Main -Recieved count of module {count} for cutting PLM")

    except ValueError:
        count = 1  # Если возникла ошибка, устанавливаем значение по умолчанию 1

    i=0 # Переменная главного цикла, если нет деталей выводим сообщение
    # Цикл из  итераций от однок до count
    for i in range(1, count):  
        
        time.sleep(3)  # Ожидание перед выполнением действий

        if i % 2 != 0:  #  Если четная итерация надо сдвинуть стол на 100 Movemant_left.DistanceL

            logging.info(f"Main - {i} cutting itteration PLM")

            # Обновляем изображение GIF
            current_gif_label_plm.config(image=gif_running_img)
            current_gif_label_plm.config(image=gif_running_img)
            
            # Команда на перемещение
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Before_marking\\Movemant_left.DistanceL={new_value}", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            logging.info(f"Main - {new_value} moved left direction")
 
            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
            else:
                print(f"Ошибка при чтении ответа: код {response}")
                status_label_plm.config(text=f"Ошибка:\n код {response}", fg="red")

            status_label_plm.config(text=f"Статус:\nПереместить стол на {new_value}", fg="green")
            print(f"Переместить стол на {new_value}")
            

            # Обновляем перменные в максиграф согласно значений из бд
            # Из модуля Берем один неотмаркированный серийник и его данные.
            result = SQLSerialProvider.get_serial_number_info(OrderID, seril_id)
            # Из модуля Берем заказ из поля если нет просим ввести. так как делаем запрос по номеру заказа
            #(2172, 76, '25027163', 'V00956935', '004-AAA', 0, 10)
            logging.info(f"Main - Recieved data for cutting from DB {result}")

            
            #Элементы гравировки получаемые из базы
            QRcode=result[3]
            NumberSerial=result[2]
            Seria=result[4]
            id_serial = result[0] # id серийника в бд

            """
            print('********************')
            print(i, 'иттерация')
            print('***для итерации получены***')
            print ('QRcode', QRcode)
            print ('NumberSerial', NumberSerial)
            print ('Seria', Seria)
            print ('id_serial', id_serial)

            print('********************')
            """
            

            # Поле Серия
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Marking\\Series.Text={Seria}", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)

            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
                logging.info(f"Main - Cutting Series {Seria} finish")
            elif decoded_data == -200:
                status_label.config(text=f"Команда некорректна", fg="red")
                return  # Не выполняем дальнейшую логику функции
            else:
                print(f"Ошибка при чтении ответа: код {response}")
            # Ваш код для выполнения команды "Set new Value"
            print("Команда Set new Value выполнена с новым значением:", new_value)
            print(f"decoded_data")
            


            # Поле QR код
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Marking\\Datamatrix.Data={QRcode}", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)

            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
                logging.info(f"Main - Cutting QRcode {QRcode} finish")
            elif decoded_data == -200:
                status_label.config(text=f"Команда некорректна", fg="red")
                return  # Не выполняем дальнейшую логику функции
            else:
                print(f"Ошибка при чтении ответа: код {response}")
            # Ваш код для выполнения команды "Set new Value"
            print("Команда Set new Value выполнена с новым значением:", new_value)
            print(f"decoded_data")
            

            # Поле Number код
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Marking\\NumberSerial.Text={NumberSerial}", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            
            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
                logging.info(f"Main - Cutting NumberSerial {NumberSerial} finish")
            elif decoded_data == -200:
                status_label.config(text=f"Команда некорректна", fg="red")
                return  # Не выполняем дальнейшую логику функции
            else:
                print(f"Ошибка при чтении ответа: код {response}")
            # Ваш код для выполнения команды "Set new Value"
            print("Команда Set new Value выполнена с новым значением:", new_value)
            print(f"decoded_data")
            time.sleep(5) # Убери 5с вермени
            logging.info(f"************************************")
            logging.info(f"Main - {i} itteration cutting finish")

            
            """
            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)
            status_label.config(text=f"Статус:\nГравировка", fg="green")

            # print(f"*****-{message1}")
            
            """
            


            time.sleep(3)

            SQLSerialProvider.updateMark(id_serial, login_user)
            time.sleep(2)
            SentLog1C.sent_result_To1C(id_serial)
            time.sleep(2)

            

            """
            # Цикл проверки. что оборудование подключено и данные мы получаем
            ####################
            while True:  
                
                # Симуляция получения данных
                # response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
                #if response == 0:  # NO_ERROR
                #decoded_data = data.decode('UTF-8')  # Декодируем в строку
                #print("Ответ от сервера:", decoded_data)
                if "ErrorFromControler" in message1:  # Если нет ошибок. все хорошо идем дальше
                    status_label.config(text="Статус:\n Нет соединения", fg="red")
                    print("Оборудование отключено Ждем данные...")
                else:
                    break
                time.sleep(1)  # Ожидание перед повторной попыткой
            ####################

            # Проверяем, завершилась ли операция маркировки успешно первая
            while "MarkingCompletedSuccessfully" not in message1:
                print("Ожидаем завершения резки...")
                status_label.config(text=f"Статус:\nОжидаем завершения резки...", fg="green")
                time.sleep(1)
                status_label.config(text=f"Статус:\n{i} иттерация гравировки", fg="green")

            # Если успешно ставим пометку в базе данныхх для серийника
            if "MarkingCompletedSuccessfully" in message1:         
                # Помечаем как промаркированный сделт в проверке
                SQLSerialProvider.updateMark(id_serial, login_user)
                logging.info(f"Main - Sent 1 to Mark in DB id={id_serial}")
            else:
                logging.warning(f"Main - Error Can't Sent 1 to Mark in DB id={id_serial}")
            """
            


        # Нечетная итерация цикла гравировки
        else:

            logging.info(f"Main - {i} cutting itteration PLM")

            # Обновляем изображение GIF
            current_gif_label_plm.config(image=gif_running_img)
            current_gif_label_plm.config(image=gif_running_img)
            
            # Команда на перемещение
            some_data_cmd = str.encode("Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            movement_cmd = str.encode("Before_marking\\Movemant_left.DistanceL=0", encoding='UTF-8')
            win32file.WriteFile(pipe, movement_cmd)
            logging.info(f"Main - 0 moved left direction")
            
            

            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode(encoding='unicode_escape')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
            else:
                status_label_plm.config(text=f"Ошибка:\n {response}", fg="red")
                print(f"Ошибка при чтении ответа: код {response}")


            status_label_plm.config(text=f"Статус:\n Переместить стол на 0", fg="green")
            print("Переместить стол на 0")

            

            # Обновляем перменные в максиграф согласно значений из бд
            # Из модуля Берем один неотмаркированный серийник и его данные.
            result = SQLSerialProvider.get_serial_number_info(OrderID, seril_id)
            # Из модуля Берем заказ из поля если нет просим ввести. так как делаем запрос по номеру заказа
            #(2172, 76, '25027163', 'V00956935', '004-AAA', 0, 10)
            logging.info(f"Main - Recieved data for cutting from DB {result}")

            #Элементы гравировки получаемые из базы
            QRcode=result[3]
            NumberSerial=result[2]
            Seria=result[4]
            id_serial = result[0] # id серийника в бд

            """
            print('********************')
            print('***для итерации получены***')
            print(i, 'иттерация')
            print ('QRcode', QRcode)
            print ('NumberSerial', NumberSerial)
            print ('Seria', Seria)
            print ('id_serial', id_serial)

            print('********************')
            """
            


            # Поле Серия
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Marking\\Series.Text={Seria}", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)

            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
                logging.info(f"Main - Cutting Seria {Seria} finish")
            elif decoded_data == -200:
                status_label_plm.config(text=f"Команда некорректна", fg="red")
                return  # Не выполняем дальнейшую логику функции
            else:
                print(f"Ошибка при чтении ответа: код {response}")
            # Ваш код для выполнения команды "Set new Value"
            print("Команда Set new Value выполнена с новым значением:", new_value)
            print(f"decoded_data")
            


            # Поле QR код
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Marking\\Datamatrix.Data={QRcode}", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)

            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
                logging.info(f"Main - Cutting QRcode {QRcode} finish")
            elif decoded_data == -200:
                status_label_plm.config(text=f"Команда некорректна", fg="red")
                return  # Не выполняем дальнейшую логику функции
            else:
                print(f"Ошибка при чтении ответа: код {response}")
            # Ваш код для выполнения команды "Set new Value"
            print("Команда Set new Value выполнена с новым значением:", new_value)
            print(f"decoded_data")
            

            # Поле Number код
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Marking\\NumberSerial.Text={NumberSerial}", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)

            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
                logging.info(f"Main - Cutting NumberSerial {NumberSerial} finish")
            elif decoded_data == -200:
                status_label_plm.config(text=f"Команда некорректна", fg="red")
                return  # Не выполняем дальнейшую логику функции
            else:
                print(f"Ошибка при чтении ответа: код {response}")
            # Ваш код для выполнения команды "Set new Value"
            print("Команда Set new Value выполнена с новым значением:", new_value)
            print(f"decoded_data")
            
            time.sleep(5) # Убери 5с вермени
            logging.info(f"************************************")
            logging.info(f"Main - {i} itteration cutting finish")

            time.sleep(3)

            SQLSerialProvider.updateMark(id_serial, login_user)
            time.sleep(2)
            SentLog1C.sent_result_To1C(id_serial)
            time.sleep(2)

            """
            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)
            print(f"*****-{message1}")
            time.sleep(3)
            
            ####################
            while True:  
                
                # Симуляция получения данных
                # response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
                #if response == 0:  # NO_ERROR
                #decoded_data = data.decode('UTF-8')  # Декодируем в строку
                #print("Ответ от сервера:", decoded_data)
                if "ErrorFromControler" in message1:  # Если нет ошибок. все хорошо идем дальше
                    status_label.config(text="Статус:\n Нет соединения", fg="red")
                    print("Оборудование отключено Ждем данные...")
                else:
                    print("Оборудование отключено Ждем данные...")
                    break
                    
                time.sleep(1)  # Ожидание перед повторной попыткой
            ####################

            # Проверяем, завершилась ли операция маркировки успешно первая
            while "MarkingCompletedSuccessfully" not in message1:
                print("Ожидаем завершения резки...")
                time.sleep(1)
                status_label.config(text=f"Статус:\n{i} итерация завершена", fg="green")

            # Если успешно ставим пометку в базе данныхх для серийника
            if "MarkingCompletedSuccessfully" in message1:         
                # Помечаем как промаркированный сделт в проверке
                SQLSerialProvider.updateMark(id_serial, login_user)
                logging.info(f"Main - Sent 1 to Mar in DB id={id_serial}")
            else:
                logging.warning(f"Main - Error Can't Sent 1 to Mark in DB id={id_serial}")
            """
            
            


        message1 = ""
    print(f"***///////{message1}")

    # Обновляем изображение GIF
    current_gif_label.config(image=gif_not_running_img)
    current_gif_label_plm.config(image=gif_not_running_img)

    print("ФИНИШ резки")
    if i:
        status_label_plm.config(text=f"Статус:\nГравировка заверешена.\n ({i} деталей)", fg="green")
    else:
        status_label_plm.config(text=f"Статус:\nВ данном шаблоне, Нет неотмаркированных деталей)", fg="green")

        
#########################################################################################################   

# Установка нового значения
######################################################################################################### 

# Movemant_left.DistanceL=5

def execute_command():
    global pipe  # Используем глобальный pipe
    new_value = entry_command.get()
    # Проверяем, если значение пустое
    if not new_value:
        status_label.config(text=f"Ошибка:\nкоманда не получена!", fg="red")
        print("Ошибка: команда не получена!")
        return  # Не выполняем дальнейшую логику функции

    # Если значение получено, продолжаем выполнение функции
    print("Команда получена:", new_value)
    # Дальнейшая логика выполнения функции
    if pipe:
        some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data_cmd)
        some_data_value = str.encode(new_value, encoding='UTF-8')
        win32file.WriteFile(pipe, some_data_value)
        print(some_data_value)
        status_label.config(text=f"Выполнена комада \n Set new Value={some_data_value}")

        # Читаем ответ из pipe
        response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
        if response == 0:  # NO_ERROR
            decoded_data = data.decode('UTF-8')  # Декодируем в строку
            print("Ответ от сервера:", decoded_data)
        elif decoded_data == -200:
            status_label.config(text=f"Команда некорректна", fg="red")
            return  # Не выполняем дальнейшую логику функции
        else:
            print(f"Ошибка при чтении ответа: код {response}")
        # Ваш код для выполнения команды "Set new Value"
        print("Команда Set new Value выполнена с новым значением:", new_value)
        print(f"decoded_data")
    else:
        print("Подключение к серверу не установлено")

######################################################################################################### 

# Запрос в ПЛМ
######################################################################################################### 
def load_template_fromPLM():
    OrderID = entry_order_plm.get()
    # Пример вызова функции
    # order_for_production_code = "ЗНП-0077224"
    if OrderID == "":
        label_order_plm.config(text=f"Введите номер заказа", fg="red")
    else:
        order_for_production_year = entry_year_plm.get()
        status = API_1C.process_order_data(OrderID, order_for_production_year)
        # Получаем шаблон в папку
        # Получаем один последний шалон и набор серийников для заказа
        orders = getPathAPI.fetch_orders_from_db(OrderID)
        path, OrderID, idTemplate = getPathAPI.getPathTemplate(orders)
        # print(path)
        # print(OrderID)
        # print(idTemplate)
        getPathAPI.save_template_to_project_folder(path, OrderID, idTemplate)
        label_order_plm.config(text=f"Шаблон получен в папку", fg="green")
        print(f'From PLM Recieve {status}')
    
######################################################################################################### 


# Передача тип модуля в АПИ
######################################################################################################### 
def on_select(value):
    print(f"Вы выбрали: {value}")
######################################################################################################### 


def show_about():
    about_window = tk.Toplevel(root)
    about_window.title("О программе")
    about_window.geometry("400x300")
    
    label_info = tk.Label(about_window, text="Версия: 1.0\nРазработчик: Конструкторско-технологический отдел", font=("Arial", 12))
    label_info.pack(pady=20)
    
    button_close = tk.Button(about_window, text="Закрыть", command=about_window.destroy)
    button_close.pack(pady=10)


if __name__ == '__main__': 
    # Функции для копирования и вставки
    def copy_text(event=None):
        entry_order_plm.clipboard_clear()  # Очищаем буфер обмена
        entry_order_plm.clipboard_append(entry_order_plm.get())  # Копируем текст в буфер обмена

    def paste_text(event=None):
        entry_order_plm.insert(tk.END, entry_order_plm.clipboard_get())  # Вставляем текст из буфера обмена

    def show_context_menu(event):
        context_menu.post(event.x_root, event.y_root)

    def copy_from_menu():
        copy_text()

    def paste_from_menu():
        paste_text() 

    # Функция для проверки логина и пароля
    def authenticate():
        global login_user
        login = entry_login.get()
        password = entry_password.get()
        user = Authorization.get_user_from_db(login,password)
        
        # Если есть пользователь в базе
        if user == 200:
            # Если логин и пароль правильные, активируем кнопки
            button_start_plm.config(state="normal")  # Активируем кнопку "Старт ПЛМ"
            button_start.config(state="normal")  # Активируем кнопку "Старт"
            auth_window.destroy()  # Закрываем окно авторизации
            login_user = login # Для записи в базу таблицу Сериал
        elif user == 404:
            label_error.config(text="Пользователь существует. Неверный логин или пароль \nПопробуйте: 1")
        elif user == 500:
            # Если логин или пароль неправильные, показываем ошибку
            label_error.config(text="Новый пользователь")
            # Если логин или пароль неправильные, показываем ошибку
            # Отображаем диалоговое окно с вопросом о создании системного пользователя
            result = messagebox.askyesno("Ошибка авторизации", 
                                        f"Такого пользователя нет. Хотите взять текущего пользователя системы?\nПароль: 1")
            
            if result:  # Если пользователь нажал "Да"
                user = Authorization.set_system_user_info()  # Функция для создания/получения системного пользователя
                label_error.config(text="Системный пользователь создан.\nПерезапустите приложение для повторной попытки.")
                # Закрываем главное окно
                root.destroy()
            else:  # Если пользователь нажал "Нет"
                messagebox.showinfo("Ошибка", "Пользователь не создан")
                root.destroy()  # Закрываем приложение, так как пользователь отказался создавать системного пользователя

    # Создание графического интерфейса
    # Создаем главное окно
    root = tk.Tk()
    root.title("Система управления")
    root.geometry("500x850")

    # Окно авторизации
    auth_window = tk.Toplevel(root)
    auth_window.title("Авторизация")
    auth_window.geometry("500x200")

    # Устанавливаем окно авторизации всегда поверх
    auth_window.attributes("-topmost", True)

    # Логин
    label_login = tk.Label(auth_window, text="Логин:")
    label_login.pack(pady=5)
    entry_login = tk.Entry(auth_window)
    # Получаем текущего пользователя Windows
    current_user = os.getlogin()
    entry_login.insert(0, current_user)  # Устанавливаем логин по умолчанию
    entry_login.pack(pady=5)

    # Пароль
    label_password = tk.Label(auth_window, text="Пароль:")
    label_password.pack(pady=5)
    entry_password = tk.Entry(auth_window, show="*")
    entry_password.pack(pady=5)

    # Кнопка для авторизации
    button_login = tk.Button(auth_window, text="Войти", command=authenticate)
    button_login.pack(pady=10)

    # Ошибка авторизации
    label_error = tk.Label(auth_window, text="", fg="red")
    label_error.pack(pady=5)

    # Создаем вкладки
    tab_control = ttk.Notebook(root)
    tab_main = ttk.Frame(tab_control)
    tab_about = ttk.Frame(tab_control)
    tab_plm = ttk.Frame(tab_control)  # Вкладка для ПЛМ

    # Добавляем вкладки в контроль
    tab_control.add(tab_main, text="Главная")
    tab_control.add(tab_plm, text="ПЛМ")  # Добавлена вкладка для ПЛМ
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
    button_start = tk.Button(tab_main, text="Старт", command=start_cutting)
    button_start.pack(pady=20)
    button_start.config(state="disabled")

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

    
    #########################################
    # Вкладка "ПЛМ" 
    # Загружаем логотип
    # Создаем лейбл для логотипа
    logo_label2 = tk.Label(tab_plm, image=logo_img)
    logo_label2.pack(pady=10)


    label_title_plm = tk.Label(tab_plm, text="Загрузите ПЛМ шаблон и настройте параметры", font=("Arial", 14))
    label_title_plm.pack(pady=10)

    
    # Создаем фрейм для размещения полей на одной строке
    frame_order_year = tk.Frame(tab_plm)
    frame_order_year.pack(pady=5)

    # Введите номер производственного заказа
    label_order_plm = tk.Label(frame_order_year, text="Номер заказа")
    label_order_plm.pack(side="left", padx=5)

    # Поле ввода заказа
    entry_order_plm = tk.Entry(frame_order_year)
    entry_order_plm.pack(side="left", padx=5)

    # Привязка горячих клавиш
    entry_order_plm.bind("<Control-c>", copy_text)  # Ctrl+C для копирования
    entry_order_plm.bind("<Control-v>", paste_text)  # Ctrl+V для вставки

    # Создание контекстного меню
    context_menu = tk.Menu(root, tearoff=0)
    context_menu.add_command(label="Копировать", command=copy_from_menu)
    context_menu.add_command(label="Вставить", command=paste_from_menu)

    # Привязка контекстного меню
    entry_order_plm.bind("<Button-3>", show_context_menu)  # Правый клик мыши

    # Введите год (по умолчанию 2025)
    label_year_plm = tk.Label(frame_order_year, text="Год")
    label_year_plm.pack(side="left", padx=5)

    entry_year_plm = tk.Entry(frame_order_year)
    entry_year_plm.insert(0, "2025")  # Устанавливаем значение по умолчанию 2025
    entry_year_plm.pack(side="left", padx=5)

    # Какой шаблон взять (лицевая или нет), отравляется в апи 1С
    # Переменная для хранения выбранного значения
    selected_value = tk.StringVar()
    
    
    # Создание фрейма для размещения радио кнопок в строку
    frame_radio = tk.Frame(tab_plm)
    frame_radio.pack(pady=5)

    # Создание радио кнопок
    radio1 = tk.Radiobutton(frame_radio, text="Лицевая", variable=selected_value, value="Лицевая", command=lambda: print(selected_value.get()))
    radio1.pack(side="left", padx=10)

    radio2 = tk.Radiobutton(frame_radio, text="Боковая левая", variable=selected_value, value="Боковая левая", command=lambda: print(selected_value.get()))
    radio2.pack(side="left", padx=10)

    button_search_plm = tk.Button(tab_plm, text="Запрос в ПЛМ", command=load_template_fromPLM)
    button_search_plm.pack(pady=10)

    label_order_plm = tk.Label(tab_plm, text="Шаблон не найден", font=("Arial", 10), fg="red")
    label_order_plm.pack(pady=5)


    button_select_template_plm = tk.Button(tab_plm, text="Выбрать ПЛМ шаблон", command=load_templatePLM)
    button_select_template_plm.pack(pady=10)

    template_label_plm = tk.Label(tab_plm, text="ПЛМ шаблон не выбран", font=("Arial", 10), fg="red")
    template_label_plm.pack(pady=5)

    button_load_template_plm = tk.Button(tab_plm, text="Загрузить ПЛМ шаблон", command=setTamplate)
    button_load_template_plm.pack(pady=10)

    load_status_label_plm = tk.Label(tab_plm, text="ПЛМ шаблон не загружен", font=("Arial", 10), fg="red")
    load_status_label_plm.pack(pady=5)

    label_count_plm = tk.Label(tab_plm, text="Введите количество для ПЛМ:")
    label_count_plm.pack(pady=5)
    entry_count_plm = tk.Entry(tab_plm)
    entry_count_plm.pack(pady=5)

    label_numbering_plm = tk.Label(tab_plm, text="Введите ПЛМ нумерацию:")
    label_numbering_plm.pack(pady=5)
    entry_numbering_plm = tk.Entry(tab_plm)
    entry_numbering_plm.pack(pady=5)

    button_start_plm = tk.Button(tab_plm, text="Старт ПЛМ", command=start_cuttingPLM)
    button_start_plm.pack(pady=20)
    button_start_plm.config(state="disabled")

    status_label_plm = tk.Label(tab_plm, text="Статус: Ожидание ПЛМ", font=("Arial", 12))
    status_label_plm.pack(pady=10)

    current_gif_label_plm = tk.Label(tab_plm, image=gif_not_running_img)
    current_gif_label_plm.pack(pady=10)

    # Вкладка "О программе"
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


    # Before_marking\Movemant_left.DistanceL=
    # Marking\NumberSerial.Text=12345bca