import multiprocessing
import time

# Функция сервера MaxiGraf
def server(pipe_server_conn):
    print("[SERVER] Ожидание сообщения от клиента...")
    # Считываем сообщение от клиента
    received_message = pipe_server_conn.recv()
    print(f"[SERVER] Получено сообщение: '{received_message}'")
    
    # Отправляем ответ клиенту
    response = f"Yes I can do {received_message}"
    print(f"[SERVER] Отправка ответа: '{response}'")
    pipe_server_conn.send(response)
    print("[SERVER] Ответ отправлен.")

# Функция клиента MaxiGraf
def client(pipe_client_conn):
    print("[CLIENT] Запуск клиента MaxiGraf...")
    time.sleep(2)  # Имитация ожидания запуска сервера
    
    # Отправляем сообщение серверу
    message = "BackMaxiGrafPipe"
    print(f"[CLIENT] Отправка сообщения серверу: '{message}'")
    pipe_client_conn.send(message)
    
    # Ожидание ответа от сервера
    print("[CLIENT] Ожидание ответа от сервера...")
    response = pipe_client_conn.recv()
    print(f"[CLIENT] Получен ответ от с ервера: '{response}'")

# Главная функция
if __name__ == "__main__":
    print("[MAIN] Запуск программы для работы с MaxiGraf через Pipe каналы...")
    
    # Создаем канал для связи
    pipe_server_conn, pipe_client_conn = multiprocessing.Pipe()

    # Создаем процессы для сервера и клиента
    server_process = multiprocessing.Process(target=server, args=(pipe_server_conn,))
    client_process = multiprocessing.Process(target=client, args=(pipe_client_conn,))

    # Запускаем сервер и клиент
    server_process.start()
    client_process.start()

    # Ждем завершения процессов
    server_process.join()
    client_process.join()

    print("[MAIN] Завершение работы программы.")
