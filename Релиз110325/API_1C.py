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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_log.log'),  # Лог в файл 'app_log.log'
        logging.StreamHandler()  # Также вывод в консоль
    ]
)

# Функция для обработки данных заказа
def process_order_data(order_for_production_code, order_for_production_year):
    try:
        # Создание базы данных и таблиц, если их еще нет
        logging.info("Creating database and tables...")

        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()

        # Creating Orders table
        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataAdd DATETIME,
            id_module TEXT,
            catalog_number TEXT,
            templates_for_marking TEXT,
            serial_numbers INTEGER,
            OrderID TEXT
        ) 
        ''')

        # Creating Users table
        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataAdd DATETIME,
            username TEXT,
            password TEXT
        ) 
        ''')

        # Creating Serial_Numbers table
        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Serial_Numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            number8 TEXT,
            number9 TEXT,
            number15 TEXT,
            Marked INTEGER,
            DataMarked TEXT,
            UserId
            FOREIGN KEY (UserId) REFERENCES Users(id)           
            FOREIGN KEY (order_id) REFERENCES Orders(id) ON DELETE CASCADE
        ) 
        ''')

        # Committing changes and closing connection
        conn.commit()
        conn.close()
        logging.info("Database and tables created successfully!")

    except Exception as e:
        logging.error(f"Error creating database: {e}")

    # API URL
    url = "http://black/erp_game_antonov/hs/mark/get_mark_info_by_orders"

    # Preparing payload for the request
    payload = f"""
    {{
        "order_for_production_module": {{
            "code": "{order_for_production_code}",
            "year": "{order_for_production_year}"
        }}
    }}
    """

    headers = {}

    # Sending request with basic authentication
    logging.info("Sending request to API...")
    try:
        response = requests.post(url, headers=headers, data=payload, auth=HTTPBasicAuth('mark_DPA', '123456zZ'))

        # Checking if the response is successful
        if response.status_code == 200:
            data = response.json()  # Convert the response to JSON

            # Extracting data from the response
            ######################## id модуля ############################
            module = data.get('module', '')
            #####################################################################
            
            ######################## catalog_number ############################
            catalog_number = data.get('catalog_number', '')
            #####################################################################
            
            ######################## Шаблоны для маркировки ############################
            templates_for_marking = data.get('templates_for_marking', [])
            first_path = templates_for_marking[0]['path']

            ######################## Серийные номера ############################
            # Еслми лицевая серийные не нужны, не берем
            serial_numbers = data.get('serial_numbers', [])
            #####################################################################

            ######################## Дата получения данных ############################
            # Current date for the dataAdd field
            dataAdd = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            #####################################################################

            # Connecting to the database for inserting data
            logging.info("Connecting to database for inserting data...")

            conn = sqlite3.connect('MHistory.db')
            cursor = conn.cursor()

            # Inserting data into Orders table
            cursor.execute(''' 
            INSERT INTO Orders (dataAdd, id_module, catalog_number, templates_for_marking, serial_numbers, OrderID) 
            VALUES (?, ?, ?, ?, ?, ?) 
            ''', (dataAdd, module, catalog_number, str(first_path), str(len(serial_numbers)), order_for_production_code))

            # Getting the ID of the inserted order
            order_id = cursor.lastrowid

            # Inserting data into Serial_Numbers table
            for serial in serial_numbers:
                number8 = serial.get('number8', '')
                number9 = serial.get('number9', '')
                number15 = serial.get('number15', '')

                cursor.execute(''' 
                INSERT INTO Serial_Numbers (order_id, number8, number9, number15) 
                VALUES (?, ?, ?, ?) 
                ''', (order_id, number8, number9, number15))

            # Committing changes
            conn.commit()

            # Closing the connection
            conn.close()

            logging.info("Data successfully inserted into the database!")
            status = "Data successfully inserted into the database!"
        else:
            logging.error(f"Error in data request: {response.status_code}")
            status = "Error in data request: {response.status_code}"
    except Exception as e:
        logging.error(f"Error while requesting data from API: {e}")
        status = f"Error while requesting data from API: {e}"

    # Function to query data from the database
    logging.info(f"Module for processing: {module}")


"""
# # Пример вызова функции
order_for_production_code = "ЗНП-0002143"
order_for_production_year = "2025"
process_order_data(order_for_production_code, order_for_production_year)
"""



