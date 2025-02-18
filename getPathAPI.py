import sqlite3
import os
import shutil
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_log.log'),  # Лог в файл 'getPathAPI_log.log'
        logging.StreamHandler()  # Также вывод в консоль
    ]
)

# 1. Функция для получения заказов из базы данных
def fetch_orders_from_db(Module):
    try:
        # Создаем подключение к базе данных (если база данных не существует, она будет создана)
        logging.info(f"getPathAPI - Connecting to database to fetch orders for module: {Module}")
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()

        # SQL запрос с использованием параметризованного запроса
        sql_query = "SELECT dataAdd, id_module, templates_for_marking FROM Orders WHERE id_module = ? ORDER BY dataAdd DESC LIMIT 1"
        cursor.execute(sql_query, (Module,))  # Передаем значение Module как параметр
        orders = cursor.fetchall()

        # Если данные найдены, возвращаем их
        if orders:
            logging.info(f"getPathAPI - Found {len(orders)} orders for module: {Module}")
            return orders
        else:
            logging.warning(f"getPathAPI - No orders found for module: {Module}")
            return None
    except Exception as e:
        logging.error(f"getPathAPI - Error fetching orders from database: {e}")
    finally:
        # Закрываем соединение, если оно было успешно создано
        if 'conn' in locals():
            conn.close()
            logging.info("getPathAPI - Database connection closed.")

# 2. Функция для копирования шаблона в папку Templates
def save_template_to_project_folder(dataAdd, id_module, template_path):
    # Генерируем новое имя файла на основе данных из БД, заменяя двоеточие на подчеркивание
    safe_dataAdd = dataAdd.replace(":", "_")
    
    # Путь к папке Templates текущего проекта
    templates_folder = "Templates"
    
    # Проверяем, существует ли папка Templates, если нет, создаем её
    if not os.path.exists(templates_folder):
        os.makedirs(templates_folder)
        logging.info(f"getPathAPI - Created 'Templates' folder at {templates_folder}")
    
    # Путь назначения для файла
    file_name = f"{safe_dataAdd}_{id_module}.le"
    destination_path = os.path.join(templates_folder, file_name)
    
    # Копируем файл по новому пути
    try:
        shutil.copy(template_path, destination_path)
        logging.info(f"getPathAPI - File successfully copied to {destination_path}")
    except FileNotFoundError:
        logging.error(f"getPathAPI - Error: file not found at {template_path}")
    except Exception as e:
        logging.error(f"getPathAPI - Error copying file: {e}")

# 3. Основная логика для получения данных и копирования шаблонов
def process_templates(Module):
    logging.info(f"getPathAPI - Starting template processing for module: {Module}")
    
    # Получаем данные из базы
    orders = fetch_orders_from_db(Module)
    
    if orders:
        for order in orders:
            # Данные из результата запроса
            dataAdd, id_module, template_path = order

            file_path = template_path.strip('[]')  # Удаляем квадратные скобки


            logging.info(f"getPathAPI - Processing template file path: {file_path}")
            
            # Проверяем, что путь к файлу не пустой
            if file_path:
                # Вызываем функцию сохранения шаблона
                save_template_to_project_folder(dataAdd, id_module, file_path)
            else:
                logging.warning(f"getPathAPI - No template path found for order with id_module {id_module}")
    else:
        logging.error("getPathAPI - Error: No orders retrieved from the database.")
        return "Error retrieving data from database"
