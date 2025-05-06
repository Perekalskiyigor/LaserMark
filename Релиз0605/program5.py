#  pyinstaller --onefile program4.py
# pyinstaller --onefile --add-data "C:\\MaxiGraf\\x64\\APIAndrey\\Acam.dll;." program5.py

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
from tkinter import PhotoImage, filedialog
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

pause = False # Кнопка паузы операции резки

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
        template_label_plm.config(text=f"Выбран шаблон: \n {file_path.split('/')[-1]}", fg="green",font=("Arial", 9))
        load_status_label_plm.config(text=f"Загрузите шаблон \n {file_path.split('/')[-1]}", fg="red",font=("Arial", 9))
        # Проверяем, содержит ли имя файла слово "module", чтобы понять, что шаблон требует нумерации
        if "FRONT" in file_path:
            template_label_plm.config(text=f"Выбран шаблон: \n {file_path.split('/')[-1]}", fg="green",font=("Arial", 9))
            load_status_label_plm.config(text="Внимание, шаблон требует \n введение нумерации", fg="red")
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
            load_status_label_plm.config(text=f"Шаблон {file_path.split('/')[-1]} \nзагружен", fg="green")
        else:
            load_status_label_plm.config(text=f"Шаблон не загружен. \nОшибка: {response}", fg="red")
            print(f"Ошибка при чтении ответа: код {response}")
    elif not file_path:
        load_status_label_plm.config(text=f"Невозможно получить путь\n к шаблону", fg="red")
        print("Невозможно получить путь к шаблону")
    elif not pipe:
        load_status_label_plm.config(text=f"Подключение к программе маркировки \nпотеряно", fg="red")
        print("Подключение к серверу не установлено")
####################################################################################


########################### ГРАВИРОВКА ##########################################

# Резка лицевых с доступом к бд
####################################################################################

# Запускаем как отделный поток, нужно дляобновления интерфейса
def start_cuttingPLM():
    logging.info(f">>>>>>>>COMAND - START CUTTING def start_cuttingPLM()")
    global pipe  # Используем глобальный pipe
    global login_user
    global file_path
    new_value = 190 # Наскоько сдвинуть стол
    
    # Если путь содержит слово Front то кол-во устанавливаемиз поля ввода
    if "FRONT" in file_path:
        front = True
    else:
        front = False 
    if pipe and front == False:
        # Запускаем процесс в отдельном потоке
        thread = threading.Thread(target=cutting_processPLM, args=(new_value,), daemon=True)
        thread.start()
        logging.info(f"Main  - START  def cutting_processPLM_FRONT")
    else:
        # Запускаем процесс в отдельном потоке
        thread = threading.Thread(target=cutting_processPLM_FRONT, args=(new_value,), daemon=True)
        thread.start()
        logging.info(f"Main  - START  def cutting_processPLM")


# Маркировка лицевых с получением значением из поля
def cutting_processPLM_FRONT(new_value):
    global message1
    global file_path # Путь до загруженного шаблона
    global pause
    # Обновляем статус
    status_cutting_plm.config(text=f"Запуск гравировки", fg="green",font=("Arial", 9))
    logging.info(f"Main - Start Cuting PLM")

    # Кол-во деталей для маркировки
    try:
        
        count = int(entry_numbering_plm.get())

        logging.info(f"Main -Recieved count of module {count} for cutting PLM")

    except ValueError:
        print("Введено некорректное значение")
        messagebox.showinfo("Гравировка", "Не введено колличество для лицевых панелей.\n По умолчанию ставим 1")    
        count = 1  # Если возникла ошибка, устанавливаем значение по умолчанию 1

    print (f"Получено {count} деталй для гравировки")

    status_cutting_plm.config(text=f"Получено {count} деталй для гравировки", fg="green",font=("Arial", 9))
    
    i=0 # Переменная главного цикла, если нет деталей выводим сообщение
    # Цикл из  итераций от однок до count
    for i in range(1, count):

        while pause == True:
            print (f"нажата кнопка паузы")
            logging.info(f"Press button pause Cycle cutting in pause")
            time.sleep(1)
        
        #time.sleep(1)  # Ожидание перед выполнением действий

        if i % 2 != 0:  #  Если четная итерация надо сдвинуть стол на 100 Movemant_left.DistanceL

            logging.info(f"Main - {i} cutting itteration PLM")

            status_cutting_plm.config(text=f"Гравировка {i} детали", fg="green",font=("Arial", 9))
            
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
                status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))

            status_cutting_plm.config(text=f"Статус:\nПереместить стол на {new_value}", fg="green",font=("Arial", 9))
            print(f"Переместить стол на {new_value}")
            status_cutting_plm.config(text=f"Выполняется {i}\n иттерация", fg="green",font=("Arial", 9))
            
            
            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)

            # print(f"*****-{message1}")
            time.sleep(1)
            
            

            
            # Цикл проверки. что оборудование подключено и данные мы получаем
            ####################
            while True:  
                
                # Симуляция получения данных
                # response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
                #if response == 0:  # NO_ERROR
                #decoded_data = data.decode('UTF-8')  # Декодируем в строку
                #print("Ответ от сервера:", decoded_data)
                if "ErrorFromControler" in message1:  # Если нет ошибок. все хорошо идем дальше
                    status_cutting_plm.config(text=f"Нет соединения с маркировщиком", fg="red",font=("Arial", 9))
                    print("Оборудование отключено Ждем данные...")
                else:
                    break
                time.sleep(1)  # Ожидание перед повторной попыткой
            ####################

            # Проверяем, завершилась ли операция маркировки успешно первая
            while "MarkingCompletedSuccessfully" not in message1:
                print("Ожидаем завершения гравировки...")
                time.sleep(1)
                status_cutting_plm.config(text=f"Гравировка {i} детали завершена", fg="green",font=("Arial", 9))

            # Если успешно ставим пометку в базе данныхх для серийника
            if "MarkingCompletedSuccessfully" in message1:         
                # Помечаем как промаркированный сделт в проверке
                logging.info(f"Main - {i}Front side Mark succesfully")

            else:
                logging.warning(f"Main - Error {i}Front side Mark")
            
            


        # Нечетная итерация цикла гравировки
        else:

            logging.info(f"Main - {i} cutting itteration PLM")

            status_cutting_plm.config(text=f"Гравировка {i} детали", fg="green",font=("Arial", 9))

            
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
                status_cutting_plm.config(text=f"Ошибка:\n {response}", fg="red",font=("Arial", 9))
                print(f"Ошибка при чтении ответа: код {response}")


            status_cutting_plm.config(text=f"Статус:\n Переместить стол на 0", fg="green",font=("Arial", 9))
            print("Переместить стол на 0")

            
            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)
            print(f"*****-{message1}")
            time.sleep(1)
            
            ####################
            while True:  
                
                # Симуляция получения данных
                # response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
                #if response == 0:  # NO_ERROR
                #decoded_data = data.decode('UTF-8')  # Декодируем в строку
                #print("Ответ от сервера:", decoded_data)
                if "ErrorFromControler" in message1:  # Если нет ошибок. все хорошо идем дальше
                    status_cutting_plm.config(text=f"Нет соединения с маркировщиком", fg="red",font=("Arial", 9))
                    print("Оборудование отключено Ждем данные...")
                else:
                    print("Оборудование отключено Ждем данные...")
                    break
                    
                time.sleep(1)  # Ожидание перед повторной попыткой
            ####################

            # Проверяем, завершилась ли операция маркировки успешно первая
            while "MarkingCompletedSuccessfully" not in message1:
                print("Ожидаем завершения гравировки...")
                time.sleep(1)
                status_cutting_plm.config(text=f"Гравировка {i} детали завершена", fg="green",font=("Arial", 9))

            # Если успешно ставим пометку в базе данныхх для серийника
            if "MarkingCompletedSuccessfully" in message1:         
                # Помечаем как промаркированный сделт в проверке
                logging.info(f"Main - {i}Front side Mark succesfully")

            else:
                logging.warning(f"Main - Error {i}Front side Mark")
            
            
            


        message1 = ""
    print(f"/////////////FINISH////////////гравировка деталей завершена {message1}")


    print("ФИНИШ гравировки")
    if i:
        status_cutting_plm.config(text=f"Работа заверешена \n отмаркировано {i} деталей", fg="green",font=("Arial", 9))
    else:
        status_cutting_plm.config(text=f"В данном шаблоне, \n Нет неотмаркированных деталей", fg="green",font=("Arial", 9))

    messagebox.showinfo("Гравировка", "Гравировка завершена.")    


# Гравировка боковых с получением кол-ва от бд
def cutting_processPLM(new_value):
    global message1
    global file_path # Путь до загруженного шаблона
    global pause
    # Обновляем статус
    status_cutting_plm.config(text=f"Запуск гравировки", fg="green",font=("Arial", 9))
    logging.info(f"Main - Start Cuting PLM")

    # Кол-во деталей для маркировки
    try:
        
        # Из модуля получить какой сейчас заказ и его айди
        OrderID, seril_id  = SQLSerialProvider.extract_order_info(file_path)
        # Из модуля получить кол-во неотмаркированных среийников
        count = SQLSerialProvider.get_total_count(OrderID, seril_id)
        # Берем кол-во из бд
        # Преобразуем значение в целое число
        count = int(count) if count else 0  # Если значение пустое, то устанавливаем 0 как дефолт
        
        # Получаем кол-во отмаркированных деталей для прогресс бара
        marked_count = SQLSerialProvider.marked_serial(OrderID, seril_id)
        # Преобразуем значение в целое число
        marked_count = int(marked_count) if marked_count else 0  # Если значение пустое, то устанавливаем 0 как дефолт
        #Общее для прогресбара
        totalforprogress = SQLSerialProvider.totalforprogressbar(OrderID, seril_id)
        # Устанавливаем максимальное значение прогресс-бара
        progress["maximum"] = totalforprogress
        progress["value"] = marked_count  # Установите значение прогресбара
        progress_label.config(text=f"Отмарикрованных детелей: {marked_count}. \n Неотмарикрованных деталей: {totalforprogress - marked_count} \n Всего деталей: {totalforprogress}")
    
        


        logging.info(f"Main -Recieved count of module {count} for cutting PLM")

        

    except ValueError:
        count = 1  # Если возникла ошибка, устанавливаем значение по умолчанию 1
        marked_count = 0

    print (f"Получено {count} деталй для гравировки")
    status_cutting_plm.config(text=f"Получено {count} деталей", fg="green",font=("Arial", 9))
    
    i=0 # Переменная главного цикла, если нет деталей выводим сообщение
    # Цикл из  итераций от однок до count
    for i in range(1, count):

        while pause == True:
            print (f"нажата кнопка паузы")
            logging.info(f"Press button pause Cycle cutting in pause")
            time.sleep(1)
        
        #time.sleep(1)  # Ожидание перед выполнением действий

        if i % 2 != 0:  #  Если четная итерация надо сдвинуть стол на 100 Movemant_left.DistanceL

            logging.info(f"Main - {i} cutting itteration PLM")
            status_cutting_plm.config(text=f"Гравировка {i} детали", fg="green",font=("Arial", 9))
            
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
                status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))

            status_cutting_plm.config(text=f"Статус:\nПереместить стол на {new_value}", fg="green",font=("Arial", 9))
            print(f"Переместить стол на {new_value}")
            status_cutting_plm.config(text=f"Выполняется {i}\n иттерация", fg="green",font=("Arial", 9))
            

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
                status_cutting_plm.config(text=f"Ошибка установки серии", fg="red",font=("Arial", 9))
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
                status_cutting_plm.config(text=f"Ошибка установки Qr кода", fg="red",font=("Arial", 9))
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
                status_cutting_plm.config(text=f"Ошибка установки Серийного номера", fg="red",font=("Arial", 9))
                return  # Не выполняем дальнейшую логику функции
            else:
                print(f"Ошибка при чтении ответа: код {response}")
            # Ваш код для выполнения команды "Set new Value"
            print("Команда Set new Value выполнена с новым значением:", new_value)
            print(f"decoded_data")
            logging.info(f"************************************")
            logging.info(f"Main - {i} itteration cutting finish")
            
            
            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)



            # print(f"*****-{message1}")
            time.sleep(1)
            
            

            
            # Цикл проверки. что оборудование подключено и данные мы получаем
            ####################
            while True:  
                
                # Симуляция получения данных
                # response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
                #if response == 0:  # NO_ERROR
                #decoded_data = data.decode('UTF-8')  # Декодируем в строку
                #print("Ответ от сервера:", decoded_data)
                if "ErrorFromControler" in message1:  # Если нет ошибок. все хорошо идем дальше
                    status_cutting_plm.config(text=f"Нет соединения с маркировщиком", fg="red",font=("Arial", 9))
                    print("Оборудование отключено Ждем данные...")
                else:
                    break
                time.sleep(1)  # Ожидание перед повторной попыткой
            ####################

            # Проверяем, завершилась ли операция маркировки успешно первая
            while "MarkingCompletedSuccessfully" not in message1:
                print("Ожидаем завершения гравировки...")
                time.sleep(1)
                status_cutting_plm.config(text=f"{i} иттерация завершена", fg="green",font=("Arial", 9))

            # Если успешно ставим пометку в базе данныхх для серийника
            if "MarkingCompletedSuccessfully" in message1:         
                # Помечаем как промаркированный сделт в проверке
                SQLSerialProvider.updateMark(id_serial, login_user)
                logging.info(f"Main - Sent 1 to Mark in DB id={id_serial}")
                SQLSerialProvider.updateMark(id_serial, login_user)
                SentLog1C.sent_result_To1C(id_serial)

                # Получаем кол-во отмаркированных деталей для прогресс бара
                marked_count = SQLSerialProvider.marked_serial(OrderID, seril_id)
                # Преобразуем значение в целое число
                marked_count = int(marked_count) if marked_count else 0  # Если значение пустое, то устанавливаем 0 как дефолт
                progress["value"] = marked_count  # Установите значение прогресбара
                progress_label.config(text=f"Отмарикрованных детелей: {marked_count}. \n Неотмарикрованных деталей: {totalforprogress - marked_count} \n Всего деталей: {totalforprogress}")

                status_cutting_plm.config(text=f"Гравировка {i} детали завершена", fg="green",font=("Arial", 9))

            else:
                logging.warning(f"Main - Error Can't Sent 1 to Mark in DB id={id_serial}")
            
            


        # Нечетная итерация цикла гравировки
        else:

            logging.info(f"Main - {i} cutting itteration PLM")

            status_cutting_plm.config(text=f"Гравировка {i} детали", fg="green",font=("Arial", 9))

            
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
                status_cutting_plm.config(text=f"Ошибка:\n {response}", fg="red",font=("Arial", 9))
                print(f"Ошибка при чтении ответа: код {response}")


            status_cutting_plm.config(text=f"Статус:\n Переместить стол на 0", fg="green",font=("Arial", 9))
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
                status_cutting_plm.config(text=f"Ошибка установки Серии", fg="red",font=("Arial", 9))
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
                status_cutting_plm.config(text=f"Ошибка установки Qr кода", fg="red",font=("Arial", 9))
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
                status_cutting_plm.config(text=f"Ошибка установки Серийного номера", fg="red",font=("Arial", 9))
                return  # Не выполняем дальнейшую логику функции
            else:
                print(f"Ошибка при чтении ответа: код {response}")
            # Ваш код для выполнения команды "Set new Value"
            print("Команда Set new Value выполнена с новым значением:", new_value)
            print(f"decoded_data")
            
    
            logging.info(f"************************************")
            logging.info(f"Main - {i} itteration cutting finish")




            
            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)
            print(f"*****-{message1}")
            time.sleep(1)
            
            ####################
            while True:  
                
                # Симуляция получения данных
                # response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
                #if response == 0:  # NO_ERROR
                #decoded_data = data.decode('UTF-8')  # Декодируем в строку
                #print("Ответ от сервера:", decoded_data)
                if "ErrorFromControler" in message1:  # Если нет ошибок. все хорошо идем дальше
                    status_cutting_plm.config(text=f"Нет соединения с маркировщиком", fg="red",font=("Arial", 9))
                    print("Оборудование отключено Ждем данные...")
                else:
                    print("Оборудование отключено Ждем данные...")
                    break
                    
                time.sleep(1)  # Ожидание перед повторной попыткой
            ####################

            # Проверяем, завершилась ли операция маркировки успешно первая
            while "MarkingCompletedSuccessfully" not in message1:
                print("Ожидаем завершения гравировки...")
                time.sleep(1)

            # Если успешно ставим пометку в базе данныхх для серийника
            if "MarkingCompletedSuccessfully" in message1:         
                # Помечаем как промаркированный сделт в проверке
                SQLSerialProvider.updateMark(id_serial, login_user)
                logging.info(f"Main - Sent 1 to Mar in DB id={id_serial}")
                SQLSerialProvider.updateMark(id_serial, login_user)
                SentLog1C.sent_result_To1C(id_serial)

                # Получаем кол-во отмаркированных деталей для прогресс бара
                marked_count = SQLSerialProvider.marked_serial(OrderID, seril_id)
                # Преобразуем значение в целое число
                marked_count = int(marked_count) if marked_count else 0  # Если значение пустое, то устанавливаем 0 как дефолт
                progress["value"] = marked_count  # Установите значение прогресбара
                progress_label.config(text=f"Отмарикрованных детелей: {marked_count}. \n Неотмарикрованных деталей: {totalforprogress - marked_count} \n Всего деталей: {totalforprogress}")


                status_cutting_plm.config(text=f"Гравировка {i} детали завершена", fg="green",font=("Arial", 9))
            else:
                logging.warning(f"Main - Error Can't Sent 1 to Mark in DB id={id_serial}")
            
            
            


        message1 = ""
    print(f"***///////{message1}")


    print("ФИНИШ гравировки")
    if i:
        status_cutting_plm.config(text=f"Работа заверешена \n отмаркировано {i} деталей", fg="green",font=("Arial", 9))
    else:
        status_cutting_plm.config(text=f"В данном шаблоне, \n Нет неотмаркированных деталей", fg="green",font=("Arial", 9))

    messagebox.showinfo("Гравировка", "Гравировка завершена.")    
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
        path, OrderID, idTemplate, pathFront = getPathAPI.getPathTemplate(orders)
        # print(path)
        # print(OrderID)
        # print(idTemplate)
        getPathAPI.save_template_to_project_folder(path, OrderID, idTemplate, pathFront)
        label_order_plm.config(text=f"Шаблон получен в папку \n Template", fg="green")
        print(f"Шаблон получен в папку Template")

        # If pathFront contains a path, show a pop-up warning
        if pathFront:
            messagebox.showwarning("Внимание", "Шаблон для лицевых панелей (шаблон с приставкой FRONT) будет доступен с вкладки лицевые панели, на этой вкладке его выбрать невозможно! Оба шаблона успешно загружены.")
        
    
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
        Authorization.create_table_if_not_exists()
        user = Authorization.get_user_from_db(login,password)
        
        # Если есть пользователь в базе
        if user == 200:
            # Если логин и пароль правильные, активируем кнопки
            StartCut.config(state="normal")  # Активируем кнопку "Старт"
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
    root.title("Управление РТК")
    # Сделать главное окно во весь экран
    root.state("zoomed")


    # Стили
    style = ttk.Style()
    style.configure(
        "TButton",
        font=("Arial", 14),
        padding=(10, 10),
        width=15
    )
    style.configure(
        "Custom.TLabelframe.Label",
        font=("Arial", 14),
        foreground="#000066"
    )
    style.configure(
        "Start.TCheckbutton",
        font=("Arial", 14),
        padding=(12, 10),
        foreground="white",
        background="#28a745"
    )
    style.configure(
        "Pause.TCheckbutton",
        font=("Arial", 14),
        padding=(12, 10),
        foreground="white",
        background="#fd7e14"
    )

    font_settings = ("Arial", 14)


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

    notebook = ttk.Notebook(root)
    notebook.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

    main_frame = ttk.Frame(notebook)
    notebook.add(main_frame, text="Главная")

    settings_frame = ttk.Frame(notebook)
    notebook.add(settings_frame, text="Настройки")


    
    font_settings = ("Arial", 14)

    # Переменная для кнопки "Пуск/Пауза"
    toggle_var = tk.BooleanVar()

    # Функции
    def update_button():
        global pause
        if toggle_var.get():
            toggle_button.config(text="Пуск", style="Pause.TCheckbutton")
            pause = True
            print("Пауза включена")
        else:
            toggle_button.config(text="Пауза", style="Start.TCheckbutton")
            print("Пуск включён")
            pause = False

    def on_toggle():
        if toggle_var.get():
            print("Пауза (включено)")
        else:
            print("Пуск (выключено)")

    # Notebook (вкладки)
    notebook = ttk.Notebook(root)
    notebook.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

    main_frame = ttk.Frame(notebook)
    notebook.add(main_frame, text="Главная")

    settings_frame = ttk.Frame(notebook)
    notebook.add(settings_frame, text="Настройки")

    # Загрузка изображения
    try:
        img = PhotoImage(file="logo.png")
        img = img.subsample(5, 5)
    except:
        img = None

    # Вкладка "Главная"
    # Изображение
    if img:
        img_label = ttk.Label(main_frame, image=img)
        img_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

    info_frame = ttk.Frame(main_frame, padding=[10, 10])
    info_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")

    ttk.Label(info_frame, text="Версия: 1.0.0", font=font_settings).pack(anchor="w", pady=5)
    ttk.Label(info_frame, text="Разработчик: КТО", font=font_settings).pack(anchor="w", pady=5)
    ttk.Label(info_frame, text="Контакт: r.tukanov@prosoftsystems.ru", font=font_settings).pack(anchor="w", pady=5)

    #################### frame1: ПЛМ START
    frame1 = ttk.LabelFrame(main_frame, text="Запрос в 1С ПЛМ", padding=[8, 10], style="Custom.TLabelframe")
    frame1.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
    main_frame.grid_rowconfigure(1, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)
    frame1.grid_columnconfigure(0, weight=1)

    # Поле ввода Номер заказа 
    ttk.Label(frame1, text="Введите номер заказа:", font=font_settings).grid(row=0, column=0, sticky="w")
    entry_order_plm = ttk.Entry(frame1, font=font_settings)
    entry_order_plm.grid(row=1, column=0, sticky="ew", pady=5)

    # Привязка горячих клавиш к полю номер заказа
    entry_order_plm.bind("<Control-c>", copy_text)  # Ctrl+C для копирования
    entry_order_plm.bind("<Control-v>", paste_text)  # Ctrl+V для вставки

    # Создание контекстного меню к полю номер заказа
    context_menu = tk.Menu(root, tearoff=0)
    context_menu.add_command(label="Копировать", command=copy_from_menu)
    context_menu.add_command(label="Вставить", command=paste_from_menu)

    # Привязка контекстного меню к полю номер заказа
    entry_order_plm.bind("<Button-3>", show_context_menu)  # Правый клик мыши

    # Лэйбел и поле ввода года заказа
    ttk.Label(frame1, text="Введите год:", font=font_settings).grid(row=2, column=0, sticky="w")
    entry_year_plm = ttk.Entry(frame1, font=font_settings)
    entry_year_plm.insert(0, "2025")
    entry_year_plm.grid(row=3, column=0, sticky="ew", pady=5)

    # Кнопка запрос в плм
    button_search_plm = ttk.Button(frame1, text="Запросить", style="TButton", command=load_template_fromPLM)
    button_search_plm.grid(row=4, column=0, sticky="w", pady=10)


    label_order_plm = tk.Label(frame1, text="Ожидаем загрузки \n шаблона маркировки", font=font_settings, foreground="green")
    label_order_plm.grid(row=5, column=0, sticky="w")

    # frame2: Управление шаблонами
    frame2 = ttk.LabelFrame(main_frame, text="Управление шаблонами", padding=[8, 10], style="Custom.TLabelframe")
    frame2.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

    # Настройка масштабирования внутри main_frame и frame2
    main_frame.grid_columnconfigure(1, weight=1)
    main_frame.grid_rowconfigure(1, weight=1)
    frame2.grid_columnconfigure(0, weight=1)

    # Кнопка "Выбрать шаблон"
    button_select_template_plm = ttk.Button(frame2, text="Выбрать шаблон", style="TButton", command=load_templatePLM)
    button_select_template_plm.grid(row=0, column=0, sticky="ew", pady=(0, 10))

    # Лейбл "Шаблон не выбран"
    template_label_plm = tk.Label(frame2, text="Шаблон не выбран", font=font_settings, foreground="red")
    template_label_plm.grid(row=1, column=0, sticky="w", pady=(0, 10))

    # Кнопка "Загрузить шаблон"
    button_load_template_plm = ttk.Button(frame2, text="Загрузить шаблон", style="TButton", command=setTamplate)
    button_load_template_plm.grid(row=2, column=0, sticky="ew", pady=(0, 10))

    # Лейбл "Шаблон не загружен"
    load_status_label_plm = tk.Label(frame2, text="Шаблон не загружен", font=font_settings, foreground="red")
    load_status_label_plm.grid(row=3, column=0, sticky="w", pady=(0, 10))

    # Поле ввода нумерации
    entry_numbering_plm = tk.Entry(frame2, font=font_settings)
    entry_numbering_plm.insert(0, "1")
    entry_numbering_plm.config(state="disabled")
    entry_numbering_plm.grid(row=4, column=0, sticky="ew", pady=(0, 10))

    #№№№№№№№№№№№№№№№№№№№№№№№№№ frame3: маркировка
    # Настройка main_frame для масштабирования
    main_frame.grid_rowconfigure(1, weight=1)
    main_frame.grid_columnconfigure(3, weight=1)

    # frame3: Управление маркировкой
    frame3 = ttk.LabelFrame(main_frame, text="Управление маркировкой", padding=[8, 10], style="Custom.TLabelframe")
    frame3.grid(row=1, column=3, padx=10, pady=10, sticky="nsew")
    frame3.grid_columnconfigure(0, weight=1)  # для масштабирования по ширине

    # Кнопка "Пуск"
    StartCut = ttk.Button(frame3, text="Пуск", style="TButton", command=start_cuttingPLM, state="disabled")
    StartCut.grid(row=0, column=0, sticky="ew", pady=(0, 10))

    # Статус маркировки
    status_cutting_plm = tk.Label(frame3, text="Ожидание", font=font_settings, foreground="green")
    status_cutting_plm.grid(row=1, column=0, sticky="w", pady=(0, 10))

    # Кнопка "Пауза"
    toggle_button = ttk.Checkbutton(
        frame3,
        width=12,
        text="Пауза",
        variable=toggle_var,
        command=update_button,
        style="Start.TCheckbutton"
    )
    toggle_button.grid(row=2, column=0, sticky="w", pady=(0, 10))

    # Прогресс-бар снизу окна
    progress_label = tk.Label(root, text="Кол-во оставшихся деталей", font=font_settings)
    progress_label.grid(row=2, column=0, columnspan=4, sticky="ew", padx=10)


    progress = ttk.Progressbar(root, orient="horizontal", length=800, mode="determinate")  # Увеличили длину
    progress.grid(row=3, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 10))
    progress["value"] = 0 # Установите значение на 0
    ##############################

    ######################## Вкладка "Настройки"
    ttk.Label(settings_frame, text="Настройки приложения", font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 5), padx=10)

    auto_start_var = tk.BooleanVar()
    ttk.Checkbutton(settings_frame, text="Автоматический запуск", variable=auto_start_var).pack(anchor="w", padx=10, pady=5)

    ttk.Label(settings_frame, text="Папка сохранения шаблонов:", font=font_settings).pack(anchor="w", padx=10, pady=(15, 5))
    entry_path = ttk.Entry(settings_frame, font=font_settings, width=40)
    entry_path.pack(anchor="w", padx=10, pady=5)
    entry_path.insert(0, "C:/Users/ИмяПользователя/Documents")

    ttk.Button(settings_frame, text="Сохранить настройки", style="TButton").pack(anchor="w", padx=10, pady=10)

    # Масштабируемость
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(1, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=1)
    main_frame.grid_columnconfigure(3, weight=1)



    
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