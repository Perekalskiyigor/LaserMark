import logging
import sqlite3
import requests
import time
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
import os

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_log.log'),  # Лог в файл 'app_log.log'
        logging.StreamHandler()  # Также вывод в консоль
    ]
)

# URL для получения токена
url_token = 'https://srv-1c-esb.prosyst.ru/applications/ERP-EXCHANGE-TEST/sys/token'
# URL для отправки данных
url_send_data = 'https://srv-1c-esb.prosyst.ru/applications/ERP-EXCHANGE-TEST/api/exchange/send_mark_info_by_order'


# Данные для авторизации
username = 'TtaUUbENdTERztAkKaKs8IozTKJhoeUIBrsJnWZJNrM='
password = 'GCgBWDhQvq_q8eXozBWUKiZZtZ1e2AEoNbN37MxPmaE='

# Время получения токена
token_time = None

# Функция для получения токена
def get_token():
    data = {'grant_type': 'CLIENT_CREDENTIALS'}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        # Добавляем verify=False для игнорирования проверки SSL-сертификата
        response = requests.post(url_token, data=data, headers=headers, auth=HTTPBasicAuth(username, password), verify=False)

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('id_token')
            logging.info(f"API1C - Recieve new Token")
            return access_token
        else:
            return None
    except Exception as e:
        logging.error(f"API1C - Error Recieve new Token {str(e)}")
    

        # Ensure the database connection is closed
# Функция для отправки данных
def sent_result_To1C(id_serial):
    global token_time # Время получения токена
    conn = None
    try:
        token = get_token()
        if not token:
            logging.info(f"API1C - Can't Recieve new Token")
            return
        
        # Initialize token_time if it is None
        if token_time is None:
            token_time = datetime.now()
            
        # Проверяем, прошло ли больше часа с момента получения токена
        if datetime.now() - token_time > timedelta(minutes=45):
            print("Время токена истекло, получаем новый токен...")
            token = get_token()
            token_time = datetime.now()
        
        # Соединение с базой данных SQLite
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        if id_serial:
            # Параметризованный запрос для обновления Ser.Marked
            update_query = '''
            SELECT O.OrderID, O.id_module, O.catalog_number, S.UserId, S.DataMarked, S.number15
            FROM Serial_Numbers AS S
            JOIN Orders AS O ON O.id = S.order_id
            WHERE  S.id = ?;
            '''

            # Запрос к бд получеия данных для отправки в 1С
            cursor.execute(update_query, (id_serial,))
            result = cursor.fetchone()  # Fetch the result
            if result:
                order_id, module_id, catalog_number, user_id, data_marked, number15 = result
                # Prepare payload to send to API
                payload = {
                    "order_for_production_module": order_id,
                    "id": "123",
                    "module": module_id,
                    "catalog_number": catalog_number,
                    "marking_modules": [
                        {"login_operator": user_id, "date": data_marked, "number_15": number15}
                    ]
                }

                """
                # Print each element in the payload with its name
                print("Payload to be sent:")
                print(f"order_for_production_module: {catalog_number}")
                print(f"id: {order_id}")
                print(f"module: {module_id}")
                print(f"catalog_number: {catalog_number}")
                print("marking_modules:")
                print(f"login_operator {user_id}")
                print(f"login_operator {user_id}")
                print(f"date {data_marked}")
                print(f"number_15: {number15}")
                """
                

                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }

                # Send POST request to API
                response = requests.post(url_send_data, json=payload, headers=headers, verify=False)

                if response.status_code == 200:
                    logging.info("API1C - Data Sent to 1C Success")
                else:
                    logging.error(f"API1C - Error Data Sent to 1C: {response.status_code}, {response.text}")
            else:
                logging.warning(f"API1C - No data found for serial id {id_serial}.")
        else:
            logging.warning("API1C - No serial number ID provided")

    except Exception as e:
        logging.error(f"API1C - Error in sent_result_To1C: {str(e)}")
    
    finally:
        # Ensure the database connection is closed
        if conn:
            conn.close()
                
            
# sent_result_To1C(2)


