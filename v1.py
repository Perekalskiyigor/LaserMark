from elevate import elevate

# Запросить права администратора
elevate()


import os
import time
import win32pipe
import win32file
import subprocess


# Название именованных каналов
PIPE_NAME = "MaxiGrafPipe"
BACK_PIPE_NAME = f"Back{PIPE_NAME}"

# Функция запуска MaxiGraf
def start_maxigraf():
    print("Запуск MaxiGraf...")
    process = subprocess.Popen(
        ["MaxiGraf.exe", "Pipe", "MaxiGrafPipe"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(7)
    return process

# Функция подключения к каналу
def connect_to_pipe(pipe_name):
    print(f"Подключение к каналу {pipe_name}...")
    pipe = win32pipe.CreateFile(
        f"\\\\.\\pipe\\{pipe_name}",
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0,
        None,
        win32file.OPEN_EXISTING,
        0,
        None
    )
    return pipe

# Функция отправки данных в канал
def write_to_pipe(pipe, message):
    print(f"Отправка сообщения: {message.strip()}")
    win32file.WriteFile(pipe, message.encode("utf-8").ljust(256, b'\0'))

# Функция чтения данных из канала
def read_from_pipe(pipe):
    result, data = win32file.ReadFile(pipe, 256)
    message = data.decode("utf-8").strip()
    print(f"Получено сообщение: {message}")
    return message

def main():
    # Шаг 1: Запуск MaxiGraf
    process = start_maxigraf()

    try:
        # Шаг 2: Подключение к обратному каналу
        back_pipe = connect_to_pipe(BACK_PIPE_NAME)

        # Шаг 3: Ожидание сообщения от MaxiGraf
        welcome_message = read_from_pipe(back_pipe)
        expected_message = f"You can do {BACK_PIPE_NAME}"
        if welcome_message != expected_message:
            print(f"Ошибка: ожидалось '{expected_message}', получено '{welcome_message}'")
            return

        # Шаг 4: Создание серверного канала
        print(f"Создание сервера {PIPE_NAME}...")
        server_pipe = win32pipe.CreateNamedPipe(
            f"\\\\.\\pipe\\{PIPE_NAME}",
            win32pipe.PIPE_ACCESS_DUPLEX,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
            1, 256, 256, 0, None
        )
        win32pipe.ConnectNamedPipe(server_pipe, None)

        # Шаг 5: Ответ по обратному каналу
        write_to_pipe(back_pipe, f"Yes I can do {BACK_PIPE_NAME}")

        # Шаг 6: Ожидание подключения клиента
        print("Ожидание подключения клиента к серверу...")
        client_connected = win32pipe.ConnectNamedPipe(server_pipe, None)

        if client_connected:
            print("Клиент подключен!")

        # Программа завершает работу, но MaxiGraf остается запущенным
        print("Подключение завершено. MaxiGraf запущен.")
    
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        # Завершаем процесс MaxiGraf, если нужно
        process.terminate()
        print("MaxiGraf завершен.")

if __name__ == "__main__":
    main()
