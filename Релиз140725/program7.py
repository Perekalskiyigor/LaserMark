#  pyinstaller --onefile program7.py
# pyinstaller --onefile --add-data "C:\\MaxiGraf\\x64\\APIAndrey\\Acam.dll;." program7.py

import logging
import reprlib
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

stop = False # Кнопка стоп операции резки

message1 = ""

login_user = "" # Глобальная переменная для хранения пользователя текущего, передаем в базу

# Глобальные переменные для управления отправкой в 1С
id_serial1С = "ABC123"  # Текущий серийник для отправки
id_serial_sent = "ABC123"  # Последний отправленный серийник
error_404_shown = False  # Флаг показа ошибки 404

pause_event = threading.Event()
# Флаг, который сигнализирует, что нужно поставить основной поток на паузу
pause_1С = threading.Event()


pause_event.set()  # Устанавливаем событие как активное


###############1C Log Sent#########################
# поток каждые 10 с отправляет логи в 1С
def LogSender_thread():
    global id_serial1С, id_serial_sent, error_404_shown
    print("1С thread start")
    
    while True:  # Бесконечный цикл
        try:
            # Если серийник не изменился или равен ABC123 - пропускаем
            if id_serial1С == id_serial_sent or id_serial1С == "ABC123":
                time.sleep(1)  # Короткая пауза
                continue
            
            print(f"Обнаружен новый серийник для отправки в 1С: {id_serial1С}")
            
            # Отправка результата в 1С                
            response_code1С = SentLog1C.sent_result_To1C(id_serial1С)
            print(f"Отправляем результат в 1С")
            # Проверка на 404 и показ сообщения один раз
            if response_code1С == 404 or response_code1С == None and not error_404_shown:
                messagebox.showerror("Ошибка", f"Отсутствует связь с 1С. Отчет о маркировки детали не отправлен.")
                error_404_shown = True
                pause_1С.set()  # Включаем режим паузы 
            elif response_code1С == 200:
                pause_1С.clear()  # Убираем паузу
                status_1С.config(text=f"Данные об отмаркированной детали {id_serial1С} \n отправлены в 1С успешно", fg="green",font=("Arial", 9))
            else:
                status_1С.config(text=f"Данные о маркеровке в 1С не потравляются, обратитесь к администратору", fg="red",font=("Arial", 9))
                pause_1С.set()
            
            # Пауза между проверками
            time.sleep(3)  # Проверяем каждые 3 секунд
            
        except Exception as e:
            print(f"Ошибка в потоке LogSender_thread: {e}")
            time.sleep(3)
###############1C Log Sent#########################


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
            # Из модуля получить какой сейчас заказ и его айди
            order, id = SQLSerialProvider.extract_order_info(file_path)
            # Получаем кол-во отмаркированных деталей для прогресс бара для фронтальных сразу берем макс
            marked_count = SQLSerialProvider.get_total_count(order, id)
            marked_count = int(marked_count) if marked_count else 0  # Если значение пустое, то устанавливаем 0 как дефолт
            #Общее для прогресбара для фронтальных берем макс
            progress["maximum"] = marked_count
            progress["value"] = marked_count  # Установите значение прогресбара
            progress_label.config(text=f"Отмарикрованных детелей: {marked_count}.")
            logging.info(f"cutting_processPLM_FRONT получила кол-во отмарикрованных {marked_count}")
        else:
            entry_numbering_plm.config(state="disabled")  # Делаем поле ввода нумерации недоступным
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
    # Подтягиваем настройки из бд
    LoadSettings()
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
    
    # Если путь содержит слово Front то кол-во устанавливаемиз поля ввода
    if "FRONT" in file_path:
        front = True
    else:
        front = False 
    if pipe and front == False:
        # Запускаем процесс в отдельном потоке
        thread = threading.Thread(target=cutting_processPLM, daemon=True)
        thread.start()
        logging.info(f"Main  - START  def cutting_processPLM_FRONT")
    else:
        # Запускаем процесс в отдельном потоке
        thread = threading.Thread(target=cutting_processPLM_FRONT, daemon=True)
        thread.start()
        logging.info(f"Main  - START  def cutting_processPLM")


# Маркировка лицевых с получением значением из поля
def cutting_processPLM_FRONT():
    global message1
    global file_path # Путь до загруженного шаблона
    global stop
    # Обновляем статус
    status_cutting_plm.config(text=f"Запуск гравировки", fg="green",font=("Arial", 9))
    logging.info(f"Запуск функции cutting_processPLM_FRONT гравировка фронтальных панелей")

    # Кол-во деталей для маркировки
    try:  
        count = int(entry_numbering_plm.get())
        # Преобразуем значение в целое число
        count = int(count) if count else 0  # Если значение пустое, то устанавливаем 0 как дефолт

        # Из модуля получить какой сейчас заказ и его айди
        order, id = SQLSerialProvider.extract_order_info(file_path)
        marked_count = SQLSerialProvider.get_total_count(order, id)
        # Получаем кол-во отмаркированных деталей для прогресс бара для фронтальных сразу берем макс
        marked_count = int(marked_count) if marked_count else 0  # Если значение пустое, то устанавливаем 0 как дефолт
        
        #Общее для прогресбара для фронтальных берем макс
        progress["maximum"] = marked_count + count
        progress["value"] = marked_count  # Установите значение прогресбара
        progress_label.config(text=f"Отмарикрованных детелей: {marked_count}. \n Неотмаркированных деталей: {marked_count + count}")
        logging.info(f"cutting_processPLM_FRONT получила кол-во {count} отмарикрованных {marked_count}")

        # Получаем данные по настройкам программы из бд
        settings = SQLSerialProvider.getSettings() # (4, '2025-06-10 10:50:56', 'i.perekalskii', 190.0, 60.0, 10.0, 1000.0, 20.0)
        distance_x_var = settings[3]
        speed_x_var = settings[4]
        laser_power_var = settings[5]
        marking_speed_var = settings[6]
        laser_frequency_var = settings[7]

        ######## Пердварительные настройки программы согласно настройкам из бд
        # Изменение скорости по оси Before_marking\Movemant_left.SpeedMoveAxis=20 скорость
        some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data_cmd)
        some_data_cmd = str.encode(f"Before_marking\\Movemant_left.SpeedMoveAxis={speed_x_var}", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data_cmd)
        logging.info(f"Main - {distance_x_var} moved left direction")
        # Читаем ответ из pipe
        response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
        if response == 0:  # NO_ERROR
            decoded_data = data.decode('UTF-8')  # Декодируем в строку
            print("Ответ от сервера:", decoded_data)
        else:
            print(f"Ошибка при чтении ответа: код {response}")
            status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))


        # Изменение мощности марикровки Marking.Power=85.0 мощность
        some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data_cmd)
        some_data_cmd = str.encode(f"Marking.Power={laser_power_var}", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data_cmd)
        logging.info(f"Main - {distance_x_var} moved left direction")
        # Читаем ответ из pipe
        response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
        if response == 0:  # NO_ERROR
            decoded_data = data.decode('UTF-8')  # Декодируем в строку
            print("Ответ от сервера:", decoded_data)
        else:
            print(f"Ошибка при чтении ответа: код {response}")
            status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))


        # Изменение скорости марикровки Marking.Speed=85.0 скорость
        some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data_cmd)
        some_data_cmd = str.encode(f"Marking.Speed={marking_speed_var}", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data_cmd)
        logging.info(f"Main - {distance_x_var} moved left direction")
        # Читаем ответ из pipe
        response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
        if response == 0:  # NO_ERROR
            decoded_data = data.decode('UTF-8')  # Декодируем в строку
            print("Ответ от сервера:", decoded_data)
        else:
            print(f"Ошибка при чтении ответа: код {response}")
            status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))


        # Изменение частоты лазера Marking.Freq=85.0 скорость
        some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data_cmd)
        some_data_cmd = str.encode(f"Marking.Freq={laser_frequency_var}", encoding='UTF-8')
        win32file.WriteFile(pipe, some_data_cmd)
        logging.info(f"Main - {distance_x_var} moved left direction")
        # Читаем ответ из pipe
        response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
        if response == 0:  # NO_ERROR
            decoded_data = data.decode('UTF-8')  # Декодируем в строку
            print("Ответ от сервера:", decoded_data)
        else:
            print(f"Ошибка при чтении ответа: код {response}")
            status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))


    except ValueError:
        print("Введено некорректное значение")
        messagebox.showinfo("Гравировка", "Не введено колличество для лицевых панелей.\n По умолчанию ставим 1")   

    # Проверяем количество деталей перед запуском цикла
    if count <= 0:
        status_cutting_plm.config(text="Нет деталей для гравировки!", fg="red", font=("Arial", 9))
        messagebox.showwarning("Предупреждение", "Не задано количество деталей для гравировки!")
        return  # Выходим из функции, если нет деталей


    print (f"Получено {count} деталй для гравировки")

    status_cutting_plm.config(text=f"Получено {count} деталй для гравировки", fg="green",font=("Arial", 9))
    
    i=1 # Переменная главного цикла, если нет деталей выводим сообщение
    success = 0 # Перменная хранения усешной марикровки, потом ее передаем в 1С
    # Цикл из  итераций от однок до count
    for i in range(1, count+1):

        toggle_button.config(state="normal")
        if stop == True:
            print (f"нажата кнопка стоп")
            logging.info(f"Press button stop Cycle cutting")
            return
        
        #time.sleep(1)  # Ожидание перед выполнением действий

        if i % 2 != 0:  #  Если четная итерация надо сдвинуть стол на 100 Movemant_left.DistanceL

            logging.info(f"Main - {i} cutting itteration PLM")
            b=0

            status_cutting_plm.config(text=f"Гравировка {i} детали", fg="green",font=("Arial", 9))

            #Перемещение по икс до маркировки
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Before_marking\\Movement_right.DistanceL={distance_x_var}", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            logging.info(f"Set Movement right - {distance_x_var} moved left direction")
            print (f"Set Movement right - {distance_x_var} moved left direction")
            time.sleep(1)
            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
            else:
                print(f"Ошибка при чтении ответа: код {response}")
                status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))

                status_cutting_plm.config(text=f"Статус:\nПереместить стол на {distance_x_var}", fg="green",font=("Arial", 9))
                print(f"Переместить стол на {distance_x_var}")
                status_cutting_plm.config(text=f"Выполняется {i}\n иттерация", fg="green",font=("Arial", 9))


            #Перемещение по икс после марикровки
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"After_marking\\Movement_left.DistanceL=-{distance_x_var}", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            logging.info(f"Set Movement left - {distance_x_var} moved left direction")
            print (f"Set Movement left - {distance_x_var} moved left direction")
            time.sleep(1)
            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
            else:
                print(f"Ошибка при чтении ответа: код {response}")
                status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))
            
            time.sleep(1)
            
            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)

            # print(f"*****-{message1}")
            time.sleep(1)
            
            
            


            ##########################*****
            # Очищаем message1 перед началом ожидания
            message1 = ""

            # Флаг успешного завершения
            marking_success = False

            logging.info("Ожидание завершения гравировки...")


            while True:
                
                message1 = message1.strip()

                # 3. Проверяем успешное завершение
                if "CompletedSuccessfully" in message1 or message1.find("CompletedSuccessfully") != -1:
                    logging.info(f"Гравировка завершена успешно!")
                    print(f"Гравировка завершена успешно! Ответ оборудования: {message1}")
                    marking_success = True
                    # Отметка об успешности марикровки в базу поле Ord.serial_numbers
                    SQLSerialProvider.updateMarkFRONT(id, login_user)
                    success = success+1 # Считаем успешно отмарикрованные
                    break

                # 4. Проверяем ошибки
                elif "ErrorFromControler" in message1 or "Error" in message1:
                    logging.error(f"Ошибка гравировки")
                    print(f"Ошибка гравировки: {message1}")
                    status_cutting_plm.config(text="Ошибка гравировки!", fg="red")
                    break

                # 5. Если статус не ясен, ждём 1 сек и повторяем
                time.sleep(1)
                b=b+1
                print(f"Ожидаем завершения гравировки ...{b}")
                print(f"Получаем сообщение {message1}")

            # Очищаем message1 после выхода из цикла
            message1 = ""

            if marking_success:
                logging.info(f"Деталь {i} успешно промаркирована!")
                status_cutting_plm.config(text=f"Гравировка {i} завершена", fg="green")
            else:
                logging.warning(f"Гравировка детали {i} не удалась!")
                # Дополнительные действия при ошибке...
            ##########################*****



 


        # Нечетная итерация цикла гравировки
        else:

            toggle_button.config(state="normal")
            while stop == True:
                print (f"нажата кнопка стоп")
                logging.info(f"Press button stop Cycle cutting")
                break

            logging.info(f"Main - {i} cutting itteration PLM")

            status_cutting_plm.config(text=f"Гравировка {i} детали", fg="green",font=("Arial", 9))

            


            status_cutting_plm.config(text=f"Статус:\nПереместить стол на {distance_x_var}", fg="green",font=("Arial", 9))
            print(f"Переместить стол на {distance_x_var}")
            status_cutting_plm.config(text=f"Выполняется {i}\n иттерация", fg="green",font=("Arial", 9))

            #Перемещение по икс до маркировки
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Before_marking\\Movement_right.DistanceL=0", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            logging.info(f"Main - 0 moved left direction")
            # Читаем ответ из pipe
            time.sleep(1)
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
            else:
                print(f"Ошибка при чтении ответа: код {response}")
                status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))

                status_cutting_plm.config(text=f"Статус:\nПереместить стол на {distance_x_var}", fg="green",font=("Arial", 9))
                print(f"Переместить стол на {distance_x_var}")
                status_cutting_plm.config(text=f"Выполняется {i}\n иттерация", fg="green",font=("Arial", 9))

            
            #Перемещение по икс после марикровки
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"After_marking\\Movement_left.DistanceL=0", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            logging.info(f"Main - 0 moved left direction")
            time.sleep(1)
            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
            else:
                print(f"Ошибка при чтении ответа: код {response}")
                status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))

            
            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)
            print(f"*****-{message1}")
            time.sleep(1)
            
            ##########################*****
            # Очищаем message1 перед началом ожидания
            message1 = ""


            # Флаг успешного завершения
            marking_success = False

            logging.info("Ожидание завершения гравировки...")

            while True:

                message1 = message1.strip()

                # 3. Проверяем успешное завершение
                if "CompletedSuccessfully" in message1 or message1.find("CompletedSuccessfully") != -1:
                    logging.info(f"Гравировка завершена успешно!")
                    print(f"Гравировка завершена успешно! Ответ оборудования: {message1}")
                    marking_success = True
                    # Отметка об успешности марикровки в базу поле Ord.serial_numbers
                    SQLSerialProvider.updateMarkFRONT(id, login_user)
                    success = success+1 # Считаем успешно отмарикрованные
                    break

                # 4. Проверяем ошибки
                elif "ErrorFromControler" in message1 or "Error" in message1:
                    logging.error(f"Ошибка гравировки")
                    print(f"Ошибка гравировки: {message1}")
                    status_cutting_plm.config(text="Ошибка гравировки!", fg="red")
                    break

                # 5. Если статус не ясен, ждём 1 сек и повторяем
                time.sleep(1)
                b=b+1
                print(f"Ожидаем завершения гравировки...{b}")
                print(f"Получаем сообщение {message1}")

            # Очищаем message1 после выхода из цикла
            message1 = ""

            if marking_success:
                logging.info(f"Деталь {i} успешно промаркирована!")
                status_cutting_plm.config(text=f"Гравировка {i} завершена", fg="green")
            else:
                logging.warning(f"Гравировка детали {i} не удалась!")
                # Дополнительные действия при ошибке...
            ##########################*****

    print(f"/////////////FINISH////////////гравировка деталей завершена {message1}")
    
    # Отправляем даннные в 1С
    res = SentLog1C.sent_result_To1CFRONT(login_user, id, success)
    if res == 200:
       messagebox.showinfo("Успех", f"Данные успешно отправлены в 1С. Пользователь {login_user} отмарикровал  {success} детеалей!")
    else:
        messagebox.showwarning("Ошибка", f"Нет соединения с 1С. Ошибка {res}. Данные о маркеровке не отправлены")
    success = 0


    print("ФИНИШ гравировки")
    if i:
        status_cutting_plm.config(text=f"Работа заверешена \n отмаркировано {success} деталей", fg="green",font=("Arial", 9))
    else:
        status_cutting_plm.config(text=f"В данном шаблоне, \n Нет неотмаркированных деталей", fg="green",font=("Arial", 9))

    messagebox.showinfo("Гравировка", "Гравировка завершена.") 



##################################################ГГРАВИРОВКА ЛЕВЫХ БОКОВЫХ
# Гравировка боковых с получением кол-ва от бд
def cutting_processPLM():
    global message1
    global file_path # Путь до загруженного шаблона
    global stop
    global pause_1С # флаг потока от отправителя отчетов 1С
    global id_serial1С # серийник для потока отправки в 1С
    b=0 # для отображения иттераций
    # Обновляем статус
    status_cutting_plm.config(text=f"Запуск гравировки", fg="green",font=("Arial", 9))
    logging.info(f"Main - Start Cuting PLM")

    # Получаем данные по настройкам программы из бд
    settings = SQLSerialProvider.getSettings() # (4, '2025-06-10 10:50:56', 'i.perekalskii', 190.0, 60.0, 10.0, 1000.0, 20.0)
    distance_x_var = settings[3]
    speed_x_var = settings[4]
    laser_power_var = settings[5]
    marking_speed_var = settings[6]
    laser_frequency_var = settings[7]

    ######## Пердварительные настройки программы согласно настройкам из бд
    # Изменение скорости по оси Before_marking\Movemant_left.SpeedMoveAxis=20 скорость
    some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
    win32file.WriteFile(pipe, some_data_cmd)
    some_data_cmd = str.encode(f"Before_marking\\Movemant_left.SpeedMoveAxis={speed_x_var}", encoding='UTF-8')
    win32file.WriteFile(pipe, some_data_cmd)
    logging.info(f"Main - {distance_x_var} moved left direction")
    # Читаем ответ из pipe
    response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
    if response == 0:  # NO_ERROR
        decoded_data = data.decode('UTF-8')  # Декодируем в строку
        print("Ответ от сервера:", decoded_data)
    else:
        print(f"Ошибка при чтении ответа: код {response}")
        status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))


    # Изменение мощности марикровки Marking.Power=85.0 мощность
    some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
    win32file.WriteFile(pipe, some_data_cmd)
    some_data_cmd = str.encode(f"Marking.Power={laser_power_var}", encoding='UTF-8')
    win32file.WriteFile(pipe, some_data_cmd)
    logging.info(f"Main - {distance_x_var} moved left direction")
    # Читаем ответ из pipe
    response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
    if response == 0:  # NO_ERROR
        decoded_data = data.decode('UTF-8')  # Декодируем в строку
        print("Ответ от сервера:", decoded_data)
    else:
        print(f"Ошибка при чтении ответа: код {response}")
        status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))


    # Изменение скорости марикровки Marking.Speed=85.0 скорость
    some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
    win32file.WriteFile(pipe, some_data_cmd)
    some_data_cmd = str.encode(f"Marking.Speed={marking_speed_var}", encoding='UTF-8')
    win32file.WriteFile(pipe, some_data_cmd)
    logging.info(f"Main - {distance_x_var} moved left direction")
    # Читаем ответ из pipe
    response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
    if response == 0:  # NO_ERROR
        decoded_data = data.decode('UTF-8')  # Декодируем в строку
        print("Ответ от сервера:", decoded_data)
    else:
        print(f"Ошибка при чтении ответа: код {response}")
        status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))


    # Изменение частоты лазера Marking.Freq=85.0 скорость
    some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
    win32file.WriteFile(pipe, some_data_cmd)
    some_data_cmd = str.encode(f"Marking.Freq={laser_frequency_var}", encoding='UTF-8')
    win32file.WriteFile(pipe, some_data_cmd)
    logging.info(f"Main - {distance_x_var} moved left direction")
    # Читаем ответ из pipe
    response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
    if response == 0:  # NO_ERROR
        decoded_data = data.decode('UTF-8')  # Декодируем в строку
        print("Ответ от сервера:", decoded_data)
    else:
        print(f"Ошибка при чтении ответа: код {response}")
        status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))


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

    # показ окна 1С соединения
    error_404_shown = False
    
    i=1 # Переменная главного цикла, если нет деталей выводим сообщение
    # Цикл из  итераций от однок до count
    for i in range(1, count+1):

        toggle_button.config(state="normal")
        if stop == True:
            print (f"нажата кнопка стоп")
            logging.info(f"Press button stop Cycle cutting")
            return
        
        #time.sleep(1)  # Ожидание перед выполнением действий

        if i % 2 != 0:  #  Если четная итерация надо сдвинуть стол на 100 Movemant_left.DistanceL

            logging.info(f"Main - {i} cutting itteration PLM")
            status_cutting_plm.config(text=f"Гравировка {i} детали", fg="green",font=("Arial", 9))
            
            #Перемещение по икс до маркировки
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Before_marking\\Movement_right.DistanceL={distance_x_var}", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            logging.info(f"Set Movement right - {distance_x_var} moved left direction")
            print (f"Set Movement right - {distance_x_var} moved left direction")
            time.sleep(0.2)
            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
            else:
                print(f"Ошибка при чтении ответа: код {response}")
                status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))

                status_cutting_plm.config(text=f"Статус:\nПереместить стол на {distance_x_var}", fg="green",font=("Arial", 9))
                print(f"Переместить стол на {distance_x_var}")
                status_cutting_plm.config(text=f"Выполняется {i}\n иттерация", fg="green",font=("Arial", 9))


            #Перемещение по икс после марикровки
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"After_marking\\Movement_left.DistanceL=-{distance_x_var}", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            logging.info(f"Set Movement left - {distance_x_var} moved left direction")
            print (f"Set Movement left - {distance_x_var} moved left direction")
            time.sleep(0.2)
            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
            else:
                print(f"Ошибка при чтении ответа: код {response}")
                status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))
 

            status_cutting_plm.config(text=f"Статус:\nПереместить стол на {distance_x_var}", fg="green",font=("Arial", 9))
            print(f"Переместить стол на {distance_x_var}")
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
            some_data_cmd = str.encode(f"Marking\\Series.Text=S {Seria}", encoding='UTF-8')
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
            print("Команда Set new Value выполнена с новым значением:",distance_x_var)
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
            print("Команда Set new Value выполнена с новым значением:", distance_x_var)
            print(f"decoded_data")
            

            # Поле Number код
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Marking\\NumberSerial.Text=N {NumberSerial}", encoding='UTF-8')
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
            print("Команда Set new Value выполнена с новым значением:", distance_x_var)
            print(f"decoded_data")
            logging.info(f"************************************")
            logging.info(f"Main - {i} itteration cutting finish")
            
            
            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)



            # print(f"*****-{message1}")
            #time.sleep(0.1)
            
            ##########################*****
            # Очищаем message1 перед началом ожидания
            message1 = ""

            # Флаг успешного завершения
            marking_success = False

            #logging.info("Ожидание завершения гравировки...")

            while True:

                # 1. Проверяем успешное завершение
                if "CompletedSuccessfully" in message1 or message1.find("CompletedSuccessfully") != -1:

                    logging.info(f"Гравировка завершена успешно! Ответ оборудования")
                    print(f"Гравировка завершена успешно!")
                    marking_success = True

                    # Обновляем статус
                    status_cutting_plm.config(text=f"{i} иттерация завершена", fg="green", font=("Arial", 9))
                    
                    # Помечаем как промаркированный сделт в проверке
                    SQLSerialProvider.updateMark(id_serial, login_user)
                    logging.info(f"Main - Sent 1 to Mark in DB id={id_serial}")
                    time.sleep(0.3)

                    # отправляем в 1С отчет в поток функции
                    id_serial1С = id_serial

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
                    
                    status_cutting_plm.config(text=f"Гравировка {i} детали завершена", fg="green", font=("Arial", 9))
                    break

                # 2. Тормозим если получили ответ от потка 1С что данные не ушли
                elif pause_1С == True:
                    logging.error(f"Программа не смогла отправить отчет в 1С, ставим на паузу программу")
                    print (f"Программа не смогла отправить отчет в 1С, ставим на паузу программу. Обратитиесь к администратору ")
                    break 

                # 3. Проверяем ошибки
                elif "ErrorFromControler" in message1 or "Error" in message1:
                    logging.error(f"Ошибка гравировки:")
                    print(f"Ошибка гравировки")
                    print("Оборудование отключено Ждем данные...")
                    toggle_button.config(state="normal")
                    if stop == True:
                        print (f"нажата кнопка стоп")
                        logging.info(f"Press button stop Cycle cutting")
                    break

                # 5. Если статус не ясен, ждём 1 сек и повторяем
                time.sleep(0.5)
                b=b+1
                print(f"Ожидаем завершения гравировки ...{b}")
                print(f"Получаем сообщение {message1}")


            # Очищаем message1 после выхода из цикла
            message1 = ""

            if marking_success:
                logging.info(f"Деталь {i} успешно промаркирована!")
                status_cutting_plm.config(text=f"Гравировка {i} завершена", fg="green")
            else:
                logging.warning(f"Гравировка детали {i} не удалась!")
                # Дополнительные действия при ошибке...
            ##########################*****

            


        # Нечетная итерация цикла гравировки
        else:

            toggle_button.config(state="normal")
            if stop == True:
                print (f"нажата кнопка стоп")
                logging.info(f"Press button stop Cycle cutting")
                return

            logging.info(f"Main - {i} cutting itteration PLM")

            status_cutting_plm.config(text=f"Гравировка {i} детали", fg="green",font=("Arial", 9))

            
            #Перемещение по икс до маркировки
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Before_marking\\Movement_right.DistanceL=0", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            logging.info(f"Main - 0 moved left direction")
            # Читаем ответ из pipe
            time.sleep(0.2)
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
            else:
                print(f"Ошибка при чтении ответа: код {response}")
                status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))

                status_cutting_plm.config(text=f"Статус:\nПереместить стол на {distance_x_var}", fg="green",font=("Arial", 9))
                print(f"Переместить стол на {distance_x_var}")
                status_cutting_plm.config(text=f"Выполняется {i}\n иттерация", fg="green",font=("Arial", 9))

            
            #Перемещение по икс после марикровки
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"After_marking\\Movement_left.DistanceL=0", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            logging.info(f"Main - 0 moved left direction")
            time.sleep(0.2)
            # Читаем ответ из pipe
            response, data = win32file.ReadFile(pipe, 4096)  # 4096 - размер буфера
            if response == 0:  # NO_ERROR
                decoded_data = data.decode('UTF-8')  # Декодируем в строку
                print("Ответ от сервера:", decoded_data)
            else:
                print(f"Ошибка при чтении ответа: код {response}")
                status_cutting_plm.config(text=f"Ошибка:\n код {response}", fg="red",font=("Arial", 9))


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
            some_data_cmd = str.encode(f"Marking\\Series.Text=S {Seria}", encoding='UTF-8')
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
            print("Команда Set new Value выполнена с новым значением:", distance_x_var)
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
            print("Команда Set new Value выполнена с новым значением:", distance_x_var)
            print(f"decoded_data")
            

            # Поле Number код
            some_data_cmd = str.encode(f"Set new Value", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data_cmd)
            some_data_cmd = str.encode(f"Marking\\NumberSerial.Text=N {NumberSerial}", encoding='UTF-8')
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
            print("Команда Set new Value выполнена с новым значением:", distance_x_var)
            print(f"decoded_data")
            
    
            logging.info(f"************************************")
            logging.info(f"Main - {i} itteration cutting finish")




            
            # Команда резка
            some_data = str.encode(f"Start mark", encoding='UTF-8')
            win32file.WriteFile(pipe, some_data)
            print(f"*****-{message1}")
            time.sleep(0.2)
            
            ##########################*****
            # Очищаем message1 перед началом ожидания
            message1 = ""

            # Флаг успешного завершения
            marking_success = False

            logging.info("Ожидание завершения гравировки...")

            while True:

                # 1. Проверяем успешное завершение
                if "CompletedSuccessfully" in message1 or message1.find("CompletedSuccessfully") != -1:

                    logging.info(f"Гравировка завершена успешно! Ответ оборудования")
                    print(f"Гравировка завершена успешно!")
                    marking_success = True

                    # Обновляем статус
                    status_cutting_plm.config(text=f"{i} иттерация завершена", fg="green", font=("Arial", 9))
                    
                    # Помечаем как промаркированный сделт в проверке
                    SQLSerialProvider.updateMark(id_serial, login_user)
                    logging.info(f"Main - Sent 1 to Mark in DB id={id_serial}")
                    time.sleep(0.5)

                    # отправляем в 1С отчет в поток функции
                    id_serial1С = id_serial

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
                    
                    status_cutting_plm.config(text=f"Гравировка {i} детали завершена", fg="green", font=("Arial", 9))
                    break

                # 2. Тормозим если получили ответ от потка 1С что данные не ушли
                elif pause_1С == True:
                    logging.error(f"Программа не смогла отправить отчет в 1С, ставим на паузу программу")
                    print (f"Программа не смогла отправить отчет в 1С, ставим на паузу программу. Обратитиесь к администратору ")
                    break 

                # 3. Проверяем ошибки
                elif "ErrorFromControler" in message1 or "Error" in message1:
                    logging.error(f"Ошибка гравировки:")
                    print(f"Ошибка гравировки")
                    print("Оборудование отключено Ждем данные...")
                    toggle_button.config(state="normal")
                    if stop == True:
                        print (f"нажата кнопка стоп")
                        logging.info(f"Press button stop Cycle cutting")
                    break

                # 5. Если статус не ясен, ждём 1 сек и повторяем
                time.sleep(0.5)
                b=b+1
                print(f"Ожидаем завершения гравировки ...{b}")
                print(f"Получаем сообщение {message1}")


            # Очищаем message1 после выхода из цикла
            message1 = ""

            if marking_success:
                logging.info(f"Деталь {i} успешно промаркирована!")
                status_cutting_plm.config(text=f"Гравировка {i} завершена", fg="green")
            else:
                logging.warning(f"Гравировка детали {i} не удалась!")
                # Дополнительные действия при ошибке...
            ##########################*****

        message1 = ""
    print(f"***///////{message1}")


    print("ФИНИШ гравировки")
    if i:
        status_cutting_plm.config(text=f"Работа заверешена \n отмаркировано {i} деталей", fg="green",font=("Arial", 9))
    else:
        status_cutting_plm.config(text=f"В данном шаблоне, \n Нет неотмаркированных деталей", fg="green",font=("Arial", 9))

    messagebox.showinfo("Гравировка", "Гравировка завершена.")    
######################################################################################################### 

# Стоп гравировки
#########################################################################################################
def stop_cutting_process():
    global stop
    stop = True


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
        path, OrderID, idTemplate, pathFront, typeModule = getPathAPI.getPathTemplate(orders)
        # print(path)
        # print(OrderID)
        # print(idTemplate)
        getPathAPI.save_template_to_project_folder(path, OrderID, idTemplate, pathFront, typeModule)
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

    def LoadSettings():
        """Заполняем поля значениями из базы"""
        try:
            logging.info("Загрузка настроек из базы данных...")
            res = SQLSerialProvider.getSettings()
            if not res or len(res) < 8:
                logging.warning("Получены некорректные или неполные данные: %s", res)
                return
            
            logging.debug("Полученные данные: %s", res)

            user_label.config(text=f"Настройки пользователя: {res[2]}")
            date_label.config(text=f"Дата последнего обновления: {res[1]}")
            distance_x_var.set(res[3])
            speed_x_var.set(res[4])
            laser_power_var.set(res[5])
            marking_speed_var.set(res[6])
            laser_frequency_var.set(res[7])

            logging.info("Настройки успешно загружены и применены.")
        except Exception as e:
            logging.error("Ошибка при загрузке настроек: %s", e, exc_info=True)


    def SaveSettings():
        """Функция обновления значений настроек программы в БД"""
        speed_x_str = speed_x_var.get()
        distance_x_str = distance_x_var.get()
        laser_power_str = laser_power_var.get()
        marking_speed_str = marking_speed_var.get()
        laser_frequency_str = laser_frequency_var.get()

        logging.info("Попытка сохранить настройки...")
        logging.debug("Получены значения (строки): speed_x=%s, distance_x=%s, laser_power=%s, marking_speed=%s, laser_frequency=%s",
                    speed_x_str, distance_x_str, laser_power_str, marking_speed_str, laser_frequency_str)

        try:
            speed_x = float(speed_x_str)
            distance_x = float(distance_x_str)
            laser_power = float(laser_power_str)
            marking_speed = float(marking_speed_str)
            laser_frequency = float(laser_frequency_str)

            logging.debug("Преобразованные значения: speed_x=%.2f, distance_x=%.2f, laser_power=%.2f, marking_speed=%.2f, laser_frequency=%.2f",
                        speed_x, distance_x, laser_power, marking_speed, laser_frequency)

            # Сохраняем настройки в базу данных
            SQLSerialProvider.saveSettings(distance_x, speed_x, laser_power, marking_speed, laser_frequency, login_user)
            logging.info("Настройки успешно сохранены для пользователя: %s", login_user)

        except ValueError as e:
            error_message = "Ошибка: введите вещественное число для одного из полей"
            logging.error("Ошибка преобразования строки в число: %s", e, exc_info=True)
            messagebox.showerror("Ошибка ввода", error_message)
            return None

        except Exception as e:
            logging.error("Неожиданная ошибка при сохранении настроек: %s", e, exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {str(e)}")
            return None

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
    entry_numbering_plm.insert(0, "0")
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
    toggle_button = ttk.Button(frame3, text="Стоп", style="TButton", command=stop_cutting_process, state="disabled")
    toggle_button.grid(row=2, column=0, sticky="ew", pady=(0, 10))

    # Статус 1С
    status_1С = tk.Label(frame3, text="Ожидание отправки данных в 1С", font=font_settings, foreground="red")
    status_1С.grid(row=3, column=0, sticky="w", pady=(0, 10))

    # Прогресс-бар снизу окна
    progress_label = tk.Label(root, text="Кол-во оставшихся деталей", font=font_settings)
    progress_label.grid(row=2, column=0, columnspan=4, sticky="ew", padx=10)


    progress = ttk.Progressbar(root, orient="horizontal", length=800, mode="determinate")  # Увеличили длину
    progress.grid(row=3, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 10))
    progress["value"] = 0 # Установите значение на 0
    ##############################

    ######################## Вкладка "Настройки"
    ttk.Label(settings_frame, text="Настройки приложения", font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 5), padx=10)

    # Сохраняем Label в переменные
    user_label = ttk.Label(settings_frame, text="Настройки пользователя: i.perekalskii", font=font_settings)
    user_label.pack(anchor="w", padx=10, pady=(10, 2))

    date_label = ttk.Label(settings_frame, text="Дата последнего обновления: 14.10.2025", font=font_settings)
    date_label.pack(anchor="w", padx=10, pady=(10, 2))

    # auto_start_var = tk.BooleanVar()
    # ttk.Checkbutton(settings_frame, text="Автоматический запуск", variable=auto_start_var).pack(anchor="w", padx=10, pady=5)

    # ttk.Label(settings_frame, text="Папка сохранения шаблонов:", font=font_settings).pack(anchor="w", padx=10, pady=(15, 5))
    # entry_path = ttk.Entry(settings_frame, font=font_settings, width=40)
    # entry_path.pack(anchor="w", padx=10, pady=5)
    # entry_path.insert(0, "C:/Users/ИмяПользователя/Documents")

    # ttk.Button(settings_frame, text="Сохранить настройки", style="TButton").pack(anchor="w", padx=10, pady=10)
    ttk.Button(settings_frame, text="Выгрузить из БД", command=LoadSettings).pack(anchor="w", padx=10, pady=(10, 5))

    # Предположим, что это пример базы (можно заменить на SQLite или другие источники)
    settings_fields = {
        "distance_x": "190",
        "speed_x": "60",
        "laser_power": "10",
        "marking_speed": "1000",
        "laser_frequency": "20"
    }

    # --- Настройки с именами и полями ввода ---
    # Пары: (отображаемое имя, имя в базе, значение по умолчанию)
    settings_list = [
        ("Дистанция движения по оси X", "distance_x", "190"),
        ("Скорость движения по оси X", "speed_x", "60"),
        ("Мощность лазера маркировки", "laser_power", "10"),
        ("Скорость маркировки", "marking_speed", "1000"),
        ("Частота лазера", "laser_frequency", "20"),
    ]

    # Дистанция движения по оси X
    distance_x_var = tk.StringVar(value="190")
    ttk.Label(settings_frame, text="Дистанция движения по оси X (190.0):", font=font_settings).pack(anchor="w", padx=10, pady=(10, 2))
    ttk.Entry(settings_frame, textvariable=distance_x_var, font=font_settings, width=20).pack(anchor="w", padx=10, pady=(0, 5))
    settings_fields["distance_x"] = distance_x_var

    # Скорость движения по оси X
    speed_x_var = tk.StringVar(value="60")
    ttk.Label(settings_frame, text="Скорость движения по оси X (60.0):", font=font_settings).pack(anchor="w", padx=10, pady=(10, 2))
    ttk.Entry(settings_frame, textvariable=speed_x_var, font=font_settings, width=20).pack(anchor="w", padx=10, pady=(0, 5))
    settings_fields["speed_x"] = speed_x_var

    # Мощность лазера маркировки
    laser_power_var = tk.StringVar(value="10")
    ttk.Label(settings_frame, text="Мощность лазера маркировки (10.0):", font=font_settings).pack(anchor="w", padx=10, pady=(10, 2))
    ttk.Entry(settings_frame, textvariable=laser_power_var, font=font_settings, width=20).pack(anchor="w", padx=10, pady=(0, 5))
    settings_fields["laser_power"] = laser_power_var

    # Скорость маркировки
    marking_speed_var = tk.StringVar(value="1000")
    ttk.Label(settings_frame, text="Скорость маркировки (60.0):", font=font_settings).pack(anchor="w", padx=10, pady=(10, 2))
    ttk.Entry(settings_frame, textvariable=marking_speed_var, font=font_settings, width=20).pack(anchor="w", padx=10, pady=(0, 5))
    settings_fields["marking_speed"] = marking_speed_var

    # Частота лазера
    laser_frequency_var = tk.StringVar(value="20")
    ttk.Label(settings_frame, text="Частота лазера (20.0):", font=font_settings).pack(anchor="w", padx=10, pady=(10, 2))
    ttk.Entry(settings_frame, textvariable=laser_frequency_var, font=font_settings, width=20).pack(anchor="w", padx=10, pady=(0, 5))
    settings_fields["laser_frequency"] = laser_frequency_var


    # --- Кнопки ---
    ttk.Button(settings_frame, text="Обновить в БД", command=SaveSettings).pack(anchor="w", padx=10, pady=(0, 20))

    


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
    t = threading.Thread(target=LogSender_thread)  # передаёшь ID
    t.start()
    root.mainloop()  # Запуск главного цикла Tkinter
    server_thread.join()
    client_thread.join()









    # Before_marking\Movemant_left.DistanceL=
    # Marking\NumberSerial.Text=12345bca