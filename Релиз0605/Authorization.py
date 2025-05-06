from datetime import datetime
import logging
import sqlite3
import getpass

# Set up logging to file
logging.basicConfig(
    level=logging.DEBUG,  # Adjust the logging level as needed
    format='%(asctime)s - Authorization - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('app_log.log'), logging.StreamHandler()]
)

    

# Функция для создания таблицы, если её нет
def create_table_if_not_exists():
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
        templates_for_markingFront TEXT,
        serial_numbers INTEGER,
        OrderID TEXT
    ) 
    ''')

    # Creating Serial_Numbers table with corrected syntax
    cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS Serial_Numbers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        number8 TEXT,
        number9 TEXT,
        number15 TEXT,
        Marked INTEGER,
        DataMarked TEXT,
        UserId INTEGER,  -- Correcting missing type for UserId
        FOREIGN KEY (UserId) REFERENCES Users(id),  -- Adding a comma
        FOREIGN KEY (order_id) REFERENCES Orders(id) ON DELETE CASCADE
    ) 
    ''')

    # Creating Users table
    cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataAdd DEFAULT CURRENT_TIMESTAMP,
        username TEXT,
        password TEXT
    ) 
    ''')

    # Committing changes and closing connection
    conn.commit()
    conn.close()

def create_user():
    try:
        # Соединение с базой данных SQLite
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        
        # Текущая дата и время
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Вставляем 2 пользователей с явным указанием пароля и времени
        users = [
            ('i.perekalskii', '1', current_time),  # Первый пользователь
            ('i.alekseev', '1', current_time),     # Второй пользователь
        ]
        
        # Вставляем пользователей в таблицу с явным указанием пароля и времени
        cursor.executemany('''
        INSERT INTO Users (username, password, dataAdd) 
        VALUES (?, ?, ?)
        ''', users)
        
        # Логируем успешное создание пользователей
        logging.info("Authorization - Try Create users Success")
        
    except Exception as e:
        logging.error(f"Authorization - Try Create users Error: {e}")
    finally:
        # Закрываем соединение с базой данных
        conn.commit()  # Применяем изменения
        conn.close()



def get_user_from_db(username, password):
    try:
        # Соединение с базой данных SQLite
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT username, password FROM Users WHERE username = ? AND password = ?
        ''', (username, password))
        # Проверяем, был ли найден пользователь
        passwuser = cursor.fetchone()
        
        # Выполним запрос для поиска пользователя с данным username и password
        cursor.execute('''
        SELECT username, password FROM Users WHERE username = ?
        ''', (username,))
        
        # Проверяем, был ли найден пользователь
        onlyuser = cursor.fetchone()

        if passwuser:
            logging.info(f"User '{username}' input in system Correct password")
            return 200
        elif onlyuser: 
            logging.info(f"User '{username}' is already exists")
            return 404
        else:
            return 500
        
    except Exception as e:
        logging.error(f"Error during user authentication: {e}")
        return False
    finally:
        # Закрываем соединение с базой данных
        conn.close()

def set_system_user_info():
    
    try:
        # Соединение с базой данных SQLite
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        
        # Текущая дата и время
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Получаем имя текущего пользователя
        current_user = getpass.getuser()
        
        # Вставляем  пользователя с явным указанием пароля и времени
        users = [
            (current_user, '1', current_time),
        ]
        
        # Вставляем пользователей в таблицу с явным указанием пароля и времени
        cursor.executemany('''
        INSERT INTO Users (username, password, dataAdd) 
        VALUES (?, ?, ?)
        ''', users)
        
        # Логируем успешное создание пользователей
        logging.info("Authorization - Try Create system users Success")
        return current_user
        
    except Exception as e:
        logging.error(f"Authorization - Try Create system users Error: {e}")
    finally:
        # Закрываем соединение с базой данных
        conn.commit()  # Применяем изменения
        conn.close()



"""
# Проверка существования таблицы пользователей
create_table_if_not_exists()
# Создаем 2 пользователей. если надо
create_user()
# Даем пользователя и пароль. если есть истинв если нет ложь.
# Если не нашли берем системного
username = 'i.perekalskii'
password = '1'
is_authenticated = get_user_from_db(username, password)
print (is_authenticated)
"""

