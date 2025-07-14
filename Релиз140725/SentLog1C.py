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
# url_token = 'https://srv-1c-esb.prosyst.ru/applications/ERP-exchange/sys/token'
# Тестовый получение токена
url_token ='https://srv-1c-esb.prosyst.ru/applications/ERP-exchange-ivshin/sys/token'


# URL для отправки данных
# url_send_data = 'https://srv-1c-esb.prosyst.ru/applications/ERP-exchange/api/exchange/send_mark_info_by_order'
# Тестовый отправка данных
url_send_data = 'https://srv-1c-esb.prosyst.ru/applications/ERP-exchange-ivshin/api/exchange/send_mark_info_by_order'

# Данные для авторизации
username = 'FRUxjKxNcvih3pjuUyWLPoSgAYh_W152arG0GKp4Vvs='
password = '4ROM6Ik3UgxBUQOg8XuDr6ydxzaCz6UUhIc9L77-M50='

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
            return 404
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
                    "id": "RTK_marking_1",
                    "module": module_id,
                    "catalog_number": catalog_number,
                    "marking_modules": [
                        {"login_operator": user_id, "date": data_marked, "number_15": number15}
                    ]
                }

                #"""
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
                #"""
                

                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }

                # Send POST request to API
                response = requests.post(url_send_data, json=payload, headers=headers, verify=False)

                if response.status_code == 200:
                    logging.info("API1C - Data Sent to 1C Success")
                    return 200
                elif response.status_code == 404:
                    logging.info("API1C - Not connection with 1C")
                    return 404
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


def sent_result_To1CFRONT(user_id, order_id, limit_count):
    global token_time
    conn = None

    # Лог входных параметров
    logging.info(f"API1C - Вызвавна функция отправки отчета в 1С для фрональных  user_id='{user_id}', order_id={order_id}, limit_count={limit_count}")
    
    # Проверка параметров
    if not user_id or not order_id or not limit_count:
        logging.warning("API1C - Функция отправки отчета в 1С для фрональных не получила парметры")
        return 404
    
    try:
        token = get_token()
        if not token:
            logging.info("API1C - Can't receive new Token")
            return

        if token_time is None or datetime.now() - token_time > timedelta(minutes=45):
            logging.info("Token expired or not initialized. Getting new token.")
            token = get_token()
            token_time = datetime.now()

        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()

        query = f'''
        WITH LastFive AS (
            SELECT 
                Ser.order_id, 
                Ord.id,      
                Ord.OrderID,
                Ord.id_module,
                Ord.catalog_number,
                Ser.DataMarked,
                Ser.UserId,
                Ser.Marked
            FROM Orders As Ord
            JOIN Serial_Numbers As Ser ON Ord.id = Ser.order_id
            WHERE Ser.order_id = ?
            AND Ser.UserId = ?
            ORDER BY Ser.DataMarked DESC
            LIMIT ?
        )
        SELECT 
            order_id, 
            id,      
            OrderID,
            id_module,
            catalog_number,
            DataMarked,
            UserId,
            (SELECT COUNT(*) FROM LastFive) AS quantity
        FROM LastFive
        LIMIT 1;
        '''

        cursor.execute(query, (order_id, user_id, limit_count))
        row = cursor.fetchone()

        if row:
            _, _, order_for_production_module, module, catalog_number, data_marked, user, quantity = row

            # Форматируем дату в ISO (если нужно — убери это, если дата уже нормальная)
            try:
                formatted_date = datetime.fromisoformat(data_marked).isoformat() + "Z"
            except:
                formatted_date = data_marked  # fallback если формат нестандартный

            payload = {
                "order_for_production_module": order_for_production_module,
                "id": "RTK_marking_1",
                "module": module,
                "type": "front",
                "catalog_number": catalog_number,
                "marking_modules": [
                    {
                        "login_operator": user,
                        "date": formatted_date,
                        "number_15": " ",
                        "quantity": quantity,
                    }
                ]
            }

            logging.debug(f"Payload: {payload}")
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }

            response = requests.post(url_send_data, json=payload, headers=headers, verify=False)

            if response.status_code == 200:
                logging.info("API1C - FRONT data sent successfully.")
                return 200
            elif response.status_code == 404:
                logging.warning("API1C - No connection with 1C.")
                return 404
            else:
                logging.error(f"API1C - FRONT send error: {response.status_code}, {response.text}")
        else:
            logging.warning(f"API1C - No FRONT data found for order_id={order_id}, user_id={user_id}")
            return 204

    except Exception as e:
        logging.error(f"API1C - Error in sent_result_To1CFRONT: {str(e)}")
        return 500
    finally:
        if conn:
            conn.close()
         
# sent_result_To1CFRONT('i.perekalskii', 24, 5)
# a = sent_result_To1C(1051)
# print (a)

# a = sent_result_To1C(7905)
# print (a)
