from datetime import datetime
import logging
import os
import sqlite3
import Authorization

# Set up logging to file
logging.basicConfig(
    level=logging.DEBUG,  # Adjust the logging level as needed
    format='SQL %(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('app_log.log'), logging.StreamHandler()]
)


# Получаем последний номер серийник для обработки из бд для заказа, который неотмарикрован
def get_serial_number_info(order_id, serial_order_id):
    conn = None
    try:
        logging.info("SQLSerialProvider - Connecting to the database 'MHistory.db'...")
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        logging.info("SQLSerialProvider - Connection established successfully.")

        # Параметризованный запрос для получения Ser.id
        query = '''
        SELECT Ser.id, Ser.order_id, Ser.number8 AS N, Ser.number9 AS QrCode,
               Ord.catalog_number AS S, Ser.Marked, Ord.serial_numbers AS Count
        FROM Orders AS Ord
        LEFT JOIN Serial_Numbers AS Ser
            ON Ser.order_id = Ord.id
        WHERE Ser.order_id = ?
          AND (Ser.Marked <> 1 OR Ser.Marked IS NULL)
          AND Ord.OrderID = ?
        LIMIT 1;
        '''

        logging.info(f"SQLSerialProvider - Executing query for OrderID: {order_id}, SerialOrderID: {serial_order_id}")
        cursor.execute(query, (serial_order_id, order_id))

        result = cursor.fetchone()

        if result:
            logging.info(f"SQLSerialProvider - Found serial number info for OrderID {order_id}: {result}")
        else:
            logging.warning(f"SQLSerialProvider - No serial number info found for OrderID {order_id}")

        return result

    except Exception as e:
        logging.error(f"SQLSerialProvider - Error in get_serial_number_info: {str(e)}", exc_info=True)

    finally:
        if conn:
            conn.close()
            logging.info("SQLSerialProvider - Database connection closed.")


# Общее кол-во серийников для заказа
def get_total_count(order_id, OrderID):
    conn = None
    try:
        logging.info("SQLSerialProvider - Connecting to the database 'MHistory.db'...")
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        logging.info("SQLSerialProvider - Connection established successfully.")

        # Формируем запрос с параметрами
        sql_query = '''
        SELECT COUNT(*) AS TotalCount
        FROM (
            SELECT Ser.id, Ser.order_id, Ser.number9, Ser.number8 AS N,
                   Ser.number9 AS QrCode, Ord.catalog_number AS S, Ser.Marked
            FROM Orders AS Ord
            LEFT JOIN Serial_Numbers AS Ser
                ON Ser.order_id = Ord.id
            WHERE Ser.order_id = ?
              AND Ord.OrderID = ?
              AND (Ser.Marked <> 1 OR Ser.Marked IS NULL)
        )
        '''

        logging.info(f"SQLSerialProvider - Executing count query for OrderID: {OrderID}, SerialOrderID: {order_id}")
        cursor.execute(sql_query, (OrderID, order_id))

        total_count = cursor.fetchone()[0]
        logging.info(f"SQLSerialProvider - Retrieved total count: {total_count}")

        return total_count

    except Exception as e:
        logging.error(f"SQLSerialProvider - Error in get_total_count: {str(e)}", exc_info=True)
        return None

    finally:
        if conn:
            conn.close()
            logging.info("SQLSerialProvider - Database connection closed.")

# Отметка о марикровки серийника для лицевых
def updateMarkFRONT(order_id_value, user="Default"):
    logging.info("SQLOrderUpdater - вызываем функцию установки отмаркированного объекта updateMarkFRONT")
    conn = None
    try:
        logging.info("SQLOrderUpdater - Connecting to the database 'MHistory.db'...")
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        logging.info("SQLOrderUpdater - Connection established successfully.")


        # Текущая дата в формате YYYY-MM-DD
        current_date = datetime.now().strftime("%Y-%m-%d")
        insert_query = '''
        INSERT INTO Serial_Numbers (UserId, DataMarked, Marked, order_id)
        VALUES (?, ?, 2, ?);
        '''
        cursor.execute(insert_query, (user, current_date, order_id_value))
        conn.commit()

        logging.info(f"Функция updateMarkFRONT отаботала с парметрами {user}, {current_date}, {order_id_value}")

    except Exception as e:
        logging.error(f"SQLOrderUpdater - Error updating serial_numbers: {str(e)}", exc_info=True)

    finally:
        if conn:
            conn.close()
            logging.info("SQLOrderUpdater - Database connection closed.")


# Отметка о марикровки серийника для боковых
def updateMark(id_serial, user="Default"):
    conn = None
    try:
        logging.info("SQLSerialProvider - Connecting to the database 'MHistory.db'...")
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        logging.info("SQLSerialProvider - Connection established successfully.")

        if id_serial:
            # Текущая дата и время
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # SQL-запрос на обновление
            update_query = '''
            UPDATE Serial_Numbers
            SET Marked = 1,
                UserId = ?,
                DataMarked = ?
            WHERE id = ?;
            '''

            logging.info(f"SQLSerialProvider - Executing update for Ser.id = {id_serial} by user '{user}'")
            cursor.execute(update_query, (user, current_date, id_serial))
            conn.commit()
            logging.info(f"SQLSerialProvider - Successfully updated Marked = 1 for Ser.id = {id_serial}")

        else:
            logging.warning("SQLSerialProvider - No serial number ID provided for update.")

    except Exception as e:
        logging.error(f"SQLSerialProvider - Error in updateMark: {str(e)}", exc_info=True)

    finally:
        if conn:
            conn.close()
            logging.info("SQLSerialProvider - Database connection closed.")



def extract_order_info(file_path, separator='_'):
    try:
        logging.info(f"SQLSerialProvider - Extracting order info from file path: {file_path}")

        # Проверяем, что путь — это строка и содержит хотя бы один разделитель
        if not isinstance(file_path, str) or separator not in file_path:
            logging.error(f"SQLSerialProvider - Invalid file path or separator not found: {file_path}")
            return None, None

        # Разделяем путь по разделителю
        path_parts = file_path.split(separator)

        if len(path_parts) == 3:
            OrderID = path_parts[1]
            # Убираем расширение, если оно есть
            seril_id = os.path.splitext(path_parts[2])[0]

            logging.info(f"SQLSerialProvider - Extracted OrderID: {OrderID}, SerialID: {seril_id}")
            return OrderID, seril_id
        # Если фронтальные то тащим уже другие данные учитываем префикс фронт
        elif len(path_parts) == 4:
            OrderID = path_parts[2]
            # Убираем расширение, если оно есть
            seril_id = os.path.splitext(path_parts[3])[0]
            logging.info(f"SQLSerialProvider - Extracted OrderID: {OrderID}, SerialID: {seril_id}")
            return OrderID, seril_id
        else:
            logging.error(f"SQLSerialProvider - Path format is invalid: {file_path}")
            return None, None

    except Exception as e:
        logging.error(f"SQLSerialProvider - Error in extract_order_info: {str(e)}", exc_info=True)
        return None, None
    


# Отмарикрованные серийники для левых боковых
def marked_serial(order_id, OrderID):
    conn = None
    try:
        logging.info(f"SQLSerialProvider - Connecting to the database 'MHistory.db' to count marked serials for OrderID: {OrderID}, SerialOrderID: {order_id}")
        
        # Создаем подключение к базе данных
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        logging.info("SQLSerialProvider - Database connection established successfully.")

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
              AND Ser.Marked = 1
        )
        '''

        logging.info(f"SQLSerialProvider - Executing query for marked serials in OrderID: {OrderID}, SerialOrderID: {order_id}")
        cursor.execute(sql_query, (OrderID, order_id))

        # Получаем результат
        total_count = cursor.fetchone()[0]

        logging.info(f"SQLSerialProvider - Retrieved total marked serial count: {total_count}")

        return total_count

    except Exception as e:
        logging.error(f"SQLSerialProvider - Error in marked_serial: {str(e)}", exc_info=True)
        return None

    finally:
        if conn:
            conn.close()
            logging.info("SQLSerialProvider - Database connection closed.")

# Отмарикрованные серийники
def marked_serialFRONT(id, OrderID):
    conn = None
    try:
        logging.info(f"SQLSerialProvider - Connecting to the database 'MHistory.db' to count marked serials for OrderID: {OrderID}, SerialOrderID: {id}")
        
        # Создаем подключение к базе данных
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        logging.info("SQLSerialProvider - Database connection established successfully.")

        # Формируем запрос с параметрами
        sql_query = '''
        SELECT Ord.serial_numbers AS TotalCount
        FROM Orders AS Ord
            WHERE Ord.id = ?
              AND Ord.OrderID = ?
        '''

        logging.info(f"SQLSerialProvider - Executing query for marked serials in OrderID: {OrderID}, SerialOrderID: {id}")
        cursor.execute(sql_query, (id, OrderID))

        # Получаем результат
        total_count = cursor.fetchone()[0]
        if total_count == None:
           total_count = 0

        logging.info(f"SQLSerialProvider - Retrieved total marked serial count: {total_count}")

        return total_count

    except Exception as e:
        logging.error(f"SQLSerialProvider - Error in marked_serial: {str(e)}", exc_info=True)
        return None

    finally:
        if conn:
            conn.close()
            logging.info("SQLSerialProvider - Database connection closed.")
    

# Получаем кол-во отмарикрованных для прогрес бара.
def totalforprogressbar(order_id, OrderID):
    conn = None
    try:
        logging.info(f"SQLSerialProvider - Connecting to the database 'MHistory.db' to count total serials for OrderID: {OrderID}, SerialOrderID: {order_id}")

        # Создаем подключение к базе данных
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        logging.info("SQLSerialProvider - Database connection established successfully.")

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
        )
        '''

        logging.info(f"SQLSerialProvider - Executing query for total serials in OrderID: {OrderID}, SerialOrderID: {order_id}")
        cursor.execute(sql_query, (OrderID, order_id))

        # Получаем результат
        total_count = cursor.fetchone()[0]

        logging.info(f"SQLSerialProvider - Retrieved total serial count: {total_count}")

        return total_count

    except Exception as e:
        logging.error(f"SQLSerialProvider - Error in totalforprogressbar: {str(e)}", exc_info=True)
        return None

    finally:
        if conn:
            conn.close()
            logging.info("SQLSerialProvider - Database connection closed.")


# Сохранение настроек программы в бд
def saveSettings(distance_x, speed_x, laser_power, marking_speed, laser_frequency, user):
    """
    Сохраняет настройки в базу данных SQLite.
    
    Параметры:
    - distance_x: Movement_left_DistanceL
    - speed_x: Movement_left_SpeedMoveAxis
    - laser_power: Marking_Power
    - marking_speed: Marking_Speed
    - laser_frequency: Marking_Freq
    """
    try:
        # Получаем текущую дату и время
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Предполагаем, что пользователь берется из системы или другой логики
        
        # Создаем подключение к базе данных
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        
        # Вставляем новые настройки
        cursor.execute('''
            INSERT INTO Settings (
                data, 
                user, 
                Movemant_left_DistanceL, 
                ovemant_left_SpeedMoveAxis, 
                Marking_Power, 
                Marking_Speed, 
                Marking_Freq
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_date, 
            user, 
            distance_x, 
            speed_x, 
            laser_power, 
            marking_speed, 
            laser_frequency
        ))
        
        # Сохраняем изменения и закрываем соединение
        conn.commit()
        conn.close()
        
        logging.info(f"Настройки успешно сохранены: "
                     f"Дата: {current_date}, "
                     f"Пользователь: {user}, "
                     f"DistanceX: {distance_x}, "
                     f"SpeedX: {speed_x}, "
                     f"LaserPower: {laser_power}, "
                     f"MarkingSpeed: {marking_speed}, "
                     f"LaserFrequency: {laser_frequency}")
        
        return True
    
    except sqlite3.Error as e:
        logging.error(f"Ошибка при сохранении настроек в базу данных: {e}")
        return False
    except Exception as e:
        logging.error(f"Неожиданная ошибка: {e}")
        return False



# Функция получения настроек из базы
def getSettings():
    # Подключение к базе данных
    # Создаем подключение к базе данных
    conn = sqlite3.connect('MHistory.db')
    cursor = conn.cursor()

    # Выполнение запроса с сортировкой по дате и выбором последней строки
    query = """
        SELECT id,
               data,
               user,
               Movemant_left_DistanceL,
               ovemant_left_SpeedMoveAxis,
               Marking_Power,
               Marking_Speed,
               Marking_Freq
        FROM Settings
        ORDER BY data DESC
        LIMIT 1;
    """
    cursor.execute(query)
    result = cursor.fetchone()

    # Отладочный вывод в консоль
    #print("Последние настройки:", result)

    # Закрытие соединения
    conn.close()

    return result


"""
# Пример использования функции:
file_path = "C:/MaxiGraf/Templates/2025-02-20 11-58-10_ЗНП-0002143_76.le"
order, seril_id = extract_order_info(file_path)
seril_id = 76
OrderID = 'ЗНП-0002143'

total_count = get_total_count(seril_id, OrderID)
print(f"Total Count: {total_count}")

marked_count = marked_serial(seril_id, OrderID)
print(f"marked_count: {marked_count}")

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
updateMarkFRONT(order_id_value=18, internal_id='ЗНП-0011676')
"""
# Пример использования функции:
# ЗНП-0011676 18


# updateMarkFRONT(order_id_value=18, internal_id='ЗНП-0011676')

# Из модуля получить какой сейчас заказ и его айди





# updateMark(2906, user = "i.perekalskii")

# saveSettings(5, 6, 10, 50, 20, "i.perekalskii")
res = getSettings()
print (res)