"""Создается сструктура БД, которая будет наполнена из 1С. Обрати внимания здесь же таблица авторизации с пользователями и паролями"""
import requests
import sqlite3
from requests.auth import HTTPBasicAuth
from datetime import datetime
import logging
import getPathAPI

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='API1C %(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_log.log'),  # Лог в файл 'app_log.log'
        logging.StreamHandler()  # Также вывод в консоль
    ]
)

def process_order_data(order_for_production_code, order_for_production_year):
    try:
        # Создаем подключение к базе данных
        logging.info("SQLSerialProvider - Creating database and tables...")

        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()

        # Создание таблицы Orders
        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataAdd DATETIME,
            id_module TEXT,
            catalog_number TEXT,
            templates_for_marking TEXT,
            templates_for_markingFront TEXT,
            serial_numbers INTEGER,
            OrderID TEXT,
            type
            
        ) 
        ''')

        # Создание таблицы Users
        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataAdd DATETIME DEFAULT CURRENT_TIMESTAMP,
            username TEXT,
            password TEXT
        ) 
        ''')

        # Создание таблицы Serial_Numbers
        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Serial_Numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            number8 TEXT,
            number9 TEXT,
            number15 TEXT,
            Marked INTEGER,
            DataMarked TEXT,
            UserId INTEGER,
            FOREIGN KEY (UserId) REFERENCES Users(id),
            FOREIGN KEY (order_id) REFERENCES Orders(id) ON DELETE CASCADE
        ) 
        ''')

        # Закрытие соединения с базой данных после создания таблиц
        conn.commit()
        conn.close()
        logging.info("SQLSerialProvider - Database and tables created successfully!")

    except Exception as e:
        logging.error(f"SQLSerialProvider - Error creating database: {e}")

    # API URL
    url = "https://c.prosyst.ru/prosoft_erp_work/hs/mark/get_mark_info_by_orders"

    # Подготовка данных для запроса
    payload = f"""
    {{
        "order_for_production_module": {{
            "code": "{order_for_production_code}",
            "year": "{order_for_production_year}"
        }}
    }}
    """

    headers = {}

    # Отправка запроса с базовой аутентификацией
    logging.info("SQLSerialProvider - Sending request to API...")

    try:
        response = requests.post(url, headers=headers, data=payload, auth=HTTPBasicAuth('mark_DPA', '123456zZ'), verify=False)

        # Проверка успешности ответа
        if response.status_code == 200:
            data = response.json()  # Преобразуем ответ в JSON

            # Извлекаем данные из ответа
            module = data.get('module', '')
            catalog_number = data.get('catalog_number', '')
            templates_for_marking = data.get('templates_for_marking', [])
            first_path = templates_for_marking[0]['path'] if templates_for_marking else ''
            templates_for_markingFront = data.get('templates_for_marking', [])
            second_path = templates_for_markingFront[1].get('path', '') if len(templates_for_markingFront) > 1 else ''
            serial_numbers = data.get('serial_numbers', [])
            typeModule = templates_for_marking[0].get('type', '')

            # Получаем текущую дату для поля dataAdd
            dataAdd = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Подключаемся к базе данных для вставки данных
            logging.info("SQLSerialProvider - Connecting to database for inserting data...")

            conn = sqlite3.connect('MHistory.db')
            cursor = conn.cursor()

            # Вставляем данные в таблицу Orders
            cursor.execute(''' 
            INSERT INTO Orders (dataAdd, id_module, catalog_number, templates_for_marking, templates_for_markingFront, serial_numbers, OrderID, type) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?) 
            ''', (dataAdd, module, catalog_number, str(first_path), str(second_path), str(len(serial_numbers)), order_for_production_code, typeModule))

            # Получаем ID вставленного заказа
            order_id = cursor.lastrowid

            # Вставляем данные в таблицу Serial_Numbers
            for serial in serial_numbers:
                number8 = serial.get('number8', '')
                number9 = serial.get('number9', '')
                number15 = serial.get('number15', '')

                cursor.execute(''' 
                INSERT INTO Serial_Numbers (order_id, number8, number9, number15) 
                VALUES (?, ?, ?, ?) 
                ''', (order_id, number8, number9, number15))

            # Сохраняем изменения
            conn.commit()

            # Закрываем соединение
            conn.close()

            logging.info("SQLSerialProvider - Data successfully inserted into the database!")
            status = "Data successfully inserted into the database!"
        else:
            logging.error(f"SQLSerialProvider - Error in data request: {response.status_code}")
            status = f"Error in data request: {response.status_code}"

    except Exception as e:
        logging.error(f"SQLSerialProvider - Error while requesting data from API: {e}")
        status = f"Error while requesting data from API: {e}"

    # Выводим данные модуля
    logging.info(f"SQLSerialProvider - Module for processing: {module}")
    return status

"""
# # Пример вызова функции
order_for_production_code = "ЗНП-0005747"
order_for_production_year = "2025"
process_order_data(order_for_production_code, order_for_production_year)


# # Пример вызова функции фронт
order_for_production_code = "ЗНП-0011676"
order_for_production_year = "2025"
process_order_data(order_for_production_code, order_for_production_year)

"""