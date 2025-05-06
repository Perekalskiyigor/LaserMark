from datetime import datetime
import logging
import sqlite3
import Authorization

# Set up logging to file
logging.basicConfig(
    level=logging.DEBUG,  # Adjust the logging level as needed
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('app_log.log'), logging.StreamHandler()]
)


def get_serial_number_info(order_id, serial_order_id):
    try:
        # Соединение с базой данных SQLite
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()

        # Параметризованный запрос для получения Ser.id
        query = '''
        SELECT Ser.id, Ser.order_id, Ser.number8 AS N, Ser.number9 AS QrCode, Ord.catalog_number AS S, Ser.Marked, Ord.serial_numbers AS Count
        FROM Orders AS Ord
        LEFT JOIN Serial_Numbers AS Ser
        ON Ser.order_id = Ord.id
        WHERE Ser.order_id = ?
        AND (Ser.Marked <> 1 OR Ser.Marked IS NULL)
        AND Ord.OrderID = ?
        LIMIT 1;
        '''

        # Выполнение запроса с параметрами
        cursor.execute(query, (serial_order_id, order_id))

        # Получение результата
        result = cursor.fetchone()

        if result:
            logging.info(f"SQLSerialProvider - Found serial number info for OrderID {order_id}: {result}")
        else:
            logging.warning(f"SQLSerialProvider - No serial number info found for OrderID {order_id}")

        return result
    except Exception as e:
        logging.error(f"SQLSerialProvider - Error in get_serial_number_info: {str(e)}")
    finally:
        conn.close()

def get_total_count(order_id, OrderID):
    try:
        # Создаем подключение к базе данных
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()

        # Формируем запрос с параметрами
        sql_query = '''
        SELECT COUNT(*) AS TotalCount
        FROM (
            SELECT Ser.id, Ser.order_id, Ser.number9, Ser.number8 AS N, Ser.number9 AS QrCode, Ord.catalog_number AS S, Ser.Marked
            FROM Orders AS Ord
            LEFT JOIN Serial_Numbers AS Ser
            ON Ser.order_id = Ord.id
            WHERE Ser.order_id = ?
            AND Ord.OrderID = ?
            AND (Ser.Marked <> 1 OR Ser.Marked IS NULL)
        )
        '''

        # Выполняем запрос с параметрами
        cursor.execute(sql_query, (OrderID, order_id))

        # Получаем результат
        total_count = cursor.fetchone()[0]

        # Закрываем соединение
        conn.close()

        return total_count
    except Exception as e:
        print(f"Error: {e}")
        return None




def updateMark(id_serial, user = "Default"):
    try:
        # Соединение с базой данных SQLite
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()

        if id_serial:

            # Get the current date in YYYY-MM-DD format
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Параметризованный запрос для обновления Ser.Marked, UserId и DataMarked
            update_query = '''
            UPDATE Serial_Numbers
            SET Marked = 1, UserId = ?, DataMarked = ?
            WHERE id = ?;
            '''

            # Выполнение обновления
            cursor.execute(update_query, (user, current_date, id_serial))  # Pass `user`, `current_date`, and `id_serial`
            conn.commit()

            logging.info(f"SQLSerialProvider - Updated Ser.Marked to 1 for Ser.id = {id_serial}")
        else:
            logging.warning("SQLSerialProvider - No serial number ID provided to update.")
    except Exception as e:
        logging.error(f"SQLSerialProvider - Error in updateMark: {str(e)}")
    finally:
        conn.close()


def extract_order_info(file_path, separator='_'):
    # Разделяем путь по разделителю '_'
    path_parts = file_path.split(separator)
    
    if len(path_parts) >= 3:
        # Получаем OrderID и id (цифры) из пути
        OrderID = path_parts[1]
        seril_id = path_parts[2].split('.')[0]  # Убираем расширение .le

        # Возвращаем OrderID и id
        return OrderID, seril_id
    else:
        logging.error(f"SQLSerialProvider - Invalid path format: {file_path}")
        return None, None


"""
# Пример использования функции:
file_path = "C:/MaxiGraf/Templates/2025-02-20 11-58-10_ЗНП-0002143_76.le"
order, seril_id = extract_order_info(file_path)
seril_id = 76
OrderID = 'ЗНП-0002143'

total_count = get_total_count(seril_id, OrderID)
print(f"Total Count: {total_count}")

"""


"""
# Пример использования функции:
file_path = "C:/MaxiGraf/Templates/2025-02-20 11-58-10_ЗНП-0002143_76.le"
order, seril_id = extract_order_info(file_path)

# Выводим результат
if order and seril_id:
    print(f"OrderID: {order}")
    print(f"File ID: {seril_id}")


serial_order_id = get_serial_number_info(order, seril_id)

print (serial_order_id)

updateMark(serial_order_id[0], user = "user")

"""

"""
username = 'i.perekalskii'
password = '3'
is_authenticated = Authorization.get_user_from_db(username, password)
print (is_authenticated)
updateMark(2, user = 1)

"""

