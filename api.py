import requests
from requests.auth import HTTPBasicAuth
import sqlite3

# Создаем подключение к базе данных (если база данных не существует, она будет создана)
conn = sqlite3.connect('MHistory.db')
cursor = conn.cursor()

# Создаем таблицу Orders
cursor.execute('''
CREATE TABLE IF NOT EXISTS Orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataAdd DATETIME,
    id_module TEXT,
    catalog_number TEXT,
    templates_for_marking TEXT,
    serial_numbers INTEGER
)
''')

# Создаем таблицу Serial_Numbers
cursor.execute('''
CREATE TABLE IF NOT EXISTS Serial_Numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    number8 TEXT,
    number9 TEXT,
    number15 TEXT,
    FOREIGN KEY (order_id) REFERENCES Orders(id) ON DELETE CASCADE
)
''')

# Сохраняем изменения и закрываем соединение
conn.commit()

# Закрываем соединение
conn.close()

print("База данных и таблицы успешно созданы!")


import sqlite3
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

# URL API
url = "http://black/erp_game_antonov/hs/mark/get_mark_info_by_orders"

# Параметры для запроса
order_for_production_code = "ЗНП-0076791"
order_for_production_year = "2024"
order_for_marking_code = "ЗНП-0076792"
order_for_marking_year = "2024"

# Формируем payload для запроса
payload = f"""
{{
    "order_for_production_module": {{
        "code": "{order_for_production_code}",
        "year": "{order_for_production_year}"
    }},
    "order_for_marking_body": {{
        "code": "{order_for_marking_code}",
        "year": "{order_for_marking_year}"
    }}
}}
"""

headers = {}

# Отправляем запрос с базовой аутентификацией
response = requests.post(url, headers=headers, data=payload, auth=HTTPBasicAuth('mark_DPA', '123456zZ'))

# Проверка успешности ответа
if response.status_code == 200:
    data = response.json()  # Преобразуем ответ в JSON

    # Извлекаем данные из ответа
    module = data.get('module', '')
    catalog_number = data.get('catalog_number', '')
    templates_for_marking = data.get('templates_for_marking', [])
    serial_numbers = data.get('serial_numbers', [])

    # Текущая дата для поля dataAdd
    dataAdd = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Подключаемся к базе данных SQLite
    conn = sqlite3.connect('MHistory.db')
    cursor = conn.cursor()

    # Вставляем данные в таблицу Orders
    cursor.execute('''
    INSERT INTO Orders (dataAdd, id_module, catalog_number, templates_for_marking, serial_numbers)
    VALUES (?, ?, ?, ?, ?)
    ''', (dataAdd, module, catalog_number, str(templates_for_marking), str(len(serial_numbers))))

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

    print("Данные успешно вставлены в базу данных!")
else:
    print(f"Ошибка при запросе данных: {response.status_code}")
