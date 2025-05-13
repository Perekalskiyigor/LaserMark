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
    try:
        # Connecting to SQLite database
        logging.info("Connecting to the SQLite database 'MHistory.db'...")
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        
        # Creating Orders table if it does not exist
        logging.info("Creating Orders table if it does not exist...")
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
        logging.info("Orders table is ready (or already exists).")

        # Creating Serial_Numbers table if it does not exist
        logging.info("Creating Serial_Numbers table if it does not exist...")
        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Serial_Numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            number8 TEXT,
            number9 TEXT,
            number15 TEXT,
            Marked INTEGER,
            DataMarked TEXT,
            UserId INTEGER,  -- Corrected missing type for UserId
            FOREIGN KEY (UserId) REFERENCES Users(id),  -- Adding a comma for syntax correction
            FOREIGN KEY (order_id) REFERENCES Orders(id) ON DELETE CASCADE
        ) 
        ''')
        logging.info("Serial_Numbers table is ready (or already exists).")

        # Creating Users table if it does not exist
        logging.info("Creating Users table if it does not exist...")
        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataAdd DEFAULT CURRENT_TIMESTAMP,
            username TEXT,
            password TEXT
        ) 
        ''')
        logging.info("Users table is ready (or already exists).")
        
        # Committing changes to the database
        conn.commit()
        logging.info("Changes committed to the database.")
        
    except sqlite3.Error as e:
        logging.error(f"SQLite error occurred: {e}")
    
    finally:
        # Closing the database connection
        if conn:
            conn.close()
            logging.info("Database connection closed.")

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
        # Connect to the SQLite database
        logging.info(f"Attempting to authenticate user: {username}")
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        
        # Check for user with correct username and password
        cursor.execute(''' 
        SELECT username, password FROM Users WHERE username = ? AND password = ?
        ''', (username, password))
        
        passwuser = cursor.fetchone()
        
        if passwuser:
            logging.info(f"User '{username}' logged in successfully with correct password.")
            return 200  # Success: Correct username and password
        else:
            # Check if the username exists without matching the password
            cursor.execute('''
            SELECT username FROM Users WHERE username = ?
            ''', (username,))
            onlyuser = cursor.fetchone()

            if onlyuser:
                logging.info(f"User '{username}' exists, but password is incorrect.")
                return 404  # User exists but password doesn't match
            else:
                logging.warning(f"User '{username}' does not exist.")
                return 500  # User does not exist

    except Exception as e:
        logging.error(f"Error during user authentication: {e}")
        return 500  # Internal server error
    finally:
        # Close the database connection
        if conn:
            conn.close()
            logging.info("Database connection closed.")

def set_system_user_info():
    try:
        # Connect to the SQLite database
        logging.info("Attempting to create system user...")
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()
        
        # Get the current date and time
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Get the current system user (this may depend on the environment you're using)
        current_user = getpass.getuser()
        
        # Insert the system user into the Users table
        users = [
            (current_user, '1', current_time),  # Default password '1', should be hashed in production
        ]
        
        cursor.executemany('''
        INSERT INTO Users (username, password, dataAdd) 
        VALUES (?, ?, ?)
        ''', users)
        
        # Commit the transaction
        conn.commit()
        logging.info(f"System user '{current_user}' created successfully.")

        return current_user
        
    except Exception as e:
        logging.error(f"Error creating system user: {e}")
        return None  # Return None if there was an error
    
    finally:
        # Close the database connection
        if conn:
            conn.close()
            logging.info("Database connection closed.")


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

