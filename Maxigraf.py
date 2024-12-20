# maxigraf_launcher.py
from elevate import elevate

# Запросить права администратора
elevate()

# Глобальные переменные для диапазона
start_range = None
end_range = None

import time
import sys
import win32pipe, win32file, pywintypes
import asyncio
import multiprocessing
import subprocess
import threading


from threading import Thread
from time import sleep
from pathlib import Path

exit = False
quit = False

# Событие для управления паузами
pause_event = threading.Event()

def get_range():
    """Функция для ввода диапазона, если он еще не задан."""
    global start_range, end_range
    if start_range is None or end_range is None:
        start_range = int(input("Введите начальное значение диапазона: "))
        end_range = int(input("Введите конечное значение диапазона: "))
        # Проверка корректности введенного диапазона
        if start_range > end_range:
            print("Начальное значение диапазона должно быть меньше или равно конечному значению.")
            start_range = 1
            end_range = 1

def thread_start():
    print("thread_start_1")
    subprocess.Popen([r'C:\MaxiGraf\MaxiGraf.exe', "PipeU", "MaxiGrafPipe"], stdout=subprocess.PIPE) #.communicate("MaxiGrafPipe")
    print("thread_start_2")

#Принимаем сообщения по обратному каналу 
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
                msg = msg + bytes(data).decode(encoding = 'unicode_escape') 
                rtnvalue, data = win32file.ReadFile(handle, 256, pywintypes.OVERLAPPED())               
            if rtnvalue == 0: 
                msg = msg + bytes(data).decode(encoding = 'unicode_escape')
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
   print(exit);
   print("3")       
    
#Основной поток управления    
def pipe_server():
    print("pipe server")
    count = 0
    
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

        counter = 1  # Инициализация счетчика
            
        while exit is False:
            print(exit);           
            
            mes = input('Enter your coomand:')
            print(mes)
            
            if mes == "Quit":     
                some_data = str.encode(f"Bay-Bay", encoding = 'UTF-8')
                win32file.WriteFile(pipe, some_data)
                global quit
                quit = True                
                exit = True
            elif mes == "Start":
                some_data = str.encode(f"Start mark", encoding = 'UTF-8')
                win32file.WriteFile(pipe, some_data)
            elif mes == "Stop":
                some_data = str.encode(f"Stop", encoding = 'UTF-8')
                win32file.WriteFile(pipe, some_data)
            elif mes == "JoyR":
                some_data = str.encode(f"Show Rectangular Joystick", encoding = 'UTF-8')
                win32file.WriteFile(pipe, some_data)
            elif mes == "JoyC":
                some_data = str.encode(f"Show Cross Joystick", encoding = 'UTF-8')
                print(some_data)
                win32file.WriteFile(pipe, some_data)

            elif mes == "pusk":

                # Получение диапазона, если он не задан
                get_range()

                
                # Ставим шаблон
                comand = str.encode(f"LoadLE", encoding = 'UTF-8')
                print(comand)
                win32file.WriteFile(pipe, comand)

                comand = str.encode(r"C:\MaxiGraf\patern.le", encoding = 'UTF-8')
                print(comand)
                win32file.WriteFile(pipe, comand)                     
                msg = ''
                rtnvalue, data = win32file.ReadFile(pipe, 256, pywintypes.OVERLAPPED())
                    
                while rtnvalue == 234:
                    msg = msg + bytes(data).decode(encoding = 'UTF-8') 
                    rtnvalue, data = win32file.ReadFile(pipe, 256, pywintypes.OVERLAPPED())
                if rtnvalue == 0: 
                    msg = msg + bytes(data).decode(encoding = 'UTF-8', errors='ignore')
                  
                print('Result: ' + msg)   
                sleep(1)
                
                
        
                counter = start_range  # Устанавливаем начальное значение счетчика

                while counter <= end_range:
                    if not pause_event.is_set():  # Если пауза не активна
                        #cut = str.encode(f"Start mark", encoding = 'UTF-8')
                        #win32file.WriteFile(pipe, cut)
                        some_data = str.encode(f"Set new Value", encoding='UTF-8')
                        win32file.WriteFile(pipe, some_data)
                        pause_event.wait(1)
                        some_data = str.encode(f"Textblock1.Data=ID_{counter}", encoding='UTF-8')
                        win32file.WriteFile(pipe, some_data)
                        print(f"Sent value_{counter}")
                        counter += 1
                        pause_event.wait(2)


                        #cut = str.encode(f"Start mark", encoding = 'UTF-8')
                        #win32file.WriteFile(pipe, cut)
                        #pause_event.wait(7)
                        
                        pause_event.wait(7)  # Задержка между отправками (1 секунда)
                        print('режем')
                        cut = str.encode(f"Start mark", encoding = 'UTF-8')
                        win32file.WriteFile(pipe, cut)
                    else:
                        pause_event.wait()  # Ждать, пока пауза не будет снята

            elif mes == "GetObjects":
                some_text = f"GetObjects"
                some_data = str.encode(some_text, encoding='UTF-8')
                print(some_data)
                win32file.WriteFile(pipe, some_data)
                msg = ''
                rtnvalue, data = win32file.ReadFile(pipe, 256, pywintypes.OVERLAPPED())
                    
                while rtnvalue == 234:
                    msg = msg + bytes(data).decode(encoding = 'UTF-8') 
                    rtnvalue, data = win32file.ReadFile(pipe, 256, pywintypes.OVERLAPPED())
                if rtnvalue == 0: 
                    msg = msg + bytes(data).decode(encoding = 'UTF-8', errors='ignore')
                  
                print('Result: ' + msg)  



            elif mes == "Script":
                ScriptName = input('Enter path to file:')
                print(ScriptName)
                
                my_file = Path(ScriptName)
                
                if my_file.exists():
                    some_data = str.encode(f"This is a TXT file", encoding = 'UTF-8')
                    win32file.WriteFile(pipe, some_data)                   
                    
                    file1 = open(ScriptName, 'r', encoding = 'UTF-8')
                    Lines = file1.readlines()                    
                    
                    for line in Lines:
                        cur = '*?'
                        res = line.rstrip() + cur                          
                        print(res)
                        str_1_encoded = res.encode(encoding = 'UTF-8', errors='ignore')
                        win32file.WriteFile(pipe, str_1_encoded)
                        sleep(0.1)
                            
                    some_data = str.encode(f"This is the end of file", encoding = 'UTF-8')
                    win32file.WriteFile(pipe, some_data)
                                        
                    msg = ''
                    rtnvalue, data = win32file.ReadFile(pipe, 256, pywintypes.OVERLAPPED())
                    
                    while rtnvalue == 234:
                        msg = msg + bytes(data).decode(encoding = 'UTF-8') 
                        rtnvalue, data = win32file.ReadFile(pipe, 256, pywintypes.OVERLAPPED())
                    if rtnvalue == 0: 
                        msg = msg + bytes(data).decode(encoding = 'UTF-8')
                  
                    print('Result: ' + msg)   
                else:
                    print('File not found')
            elif mes == "LE":   
                FileName = input('Enter path to file:')
                
                print(FileName)
                
                my_file = Path(FileName)
                
                if my_file.exists():
                    some_data = str.encode(f"This is a LE file", encoding = 'UTF-8')                                       
                    win32file.WriteFile(pipe, some_data)   
                    
                    buffer_size=256
                    
                    file = open(FileName, mode="rb")
                    byte = file.read(buffer_size)
                    while byte:
                        print(byte)
                        win32file.WriteFile(pipe, byte)
                        sleep(0.1)
                        byte = file.read(buffer_size)
                       
                    some_data = str.encode(f"This is the end of file", encoding = 'UTF-8')
                    win32file.WriteFile(pipe, some_data)
                                        
                    msg = ''
                    rtnvalue, data = win32file.ReadFile(pipe, 256, pywintypes.OVERLAPPED())
                    
                    while rtnvalue == 234:
                        msg = msg + bytes(data).decode(encoding = 'UTF-8') 
                        rtnvalue, data = win32file.ReadFile(pipe, 256, pywintypes.OVERLAPPED())
                    if rtnvalue == 0: 
                        msg = msg + bytes(data).decode(encoding = 'UTF-8', errors='ignore')
                  
                    print('Result: ' + msg)   
                    
                    
                else:
                    print('File not found')

            elif mes == "LoadLE":   

                some_data = str.encode(f"LoadLE", encoding = 'UTF-8')
                print(some_data)
                win32file.WriteFile(pipe, some_data)

                some_data = str.encode(r"C:\MaxiGraf\patern.le", encoding = 'UTF-8')
                print(some_data)
                win32file.WriteFile(pipe, some_data)
                                        
                msg = ''
                rtnvalue, data = win32file.ReadFile(pipe, 256, pywintypes.OVERLAPPED())
                    
                while rtnvalue == 234:
                    msg = msg + bytes(data).decode(encoding = 'UTF-8') 
                    rtnvalue, data = win32file.ReadFile(pipe, 256, pywintypes.OVERLAPPED())
                if rtnvalue == 0: 
                    msg = msg + bytes(data).decode(encoding = 'UTF-8', errors='ignore')
                  
                print('Result: ' + msg)   
                    

            else:
                print("Don't know this command.")
            
            sleep(1)
                
        print("finished now")
    finally:
        win32file.CloseHandle(pipe)
        
#Создаем обратный канал и подключаем основной канал
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
                
                if(connect):
                    msg = ''
                    rtnvalue, data = win32file.ReadFile(handle, 256, pywintypes.OVERLAPPED())
                    while rtnvalue == 234:
                        msg = msg + bytes(data).decode(encoding = 'unicode_escape') 
                        rtnvalue, data = win32file.ReadFile(handle, 256, pywintypes.OVERLAPPED())
                        print(msg)
                    if rtnvalue == 0: #end of stream is reached
                        msg = msg + bytes(data).decode(encoding = 'unicode_escape')
                        print(msg)
                        
                    print(f'The rtnvalue is {rtnvalue}')    
                    print(f'The message is {msg}' + ' .end')
                
                    some_data = str.encode("Yes I can do BakcMaxiGrafPipe")
                    win32file.WriteFile(handle, some_data)            
                    print("Yes I can do BakcMaxiGrafPipe")
                    
                    if(connect):
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
                    

   

   

if __name__ == '__main__':  
    
    x = threading.Thread(target=thread_start)  
    x.start()

    time.sleep(15)

    #pipe_server()
    server_thread = threading.Thread(target=pipe_server)
    server_thread.start()

    time.sleep(1)  # Пауза для того, чтобы сервер успел создать и ждать соединения

    client_thread = threading.Thread(target=pipe_client)
    client_thread.start()

    # Добавьте код для ожидания завершения работы потоков, если это необходимо
    server_thread.join()
    client_thread.join()