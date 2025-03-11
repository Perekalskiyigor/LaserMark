from datetime import datetime
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
def fetch_orders_from_db(OrderID):
    try:
        # Создаем подключение к базе данных (если база данных не существует, она будет создана)
        logging.info(f"getPathAPI - Connecting to database to fetch order: {OrderID}")
        conn = sqlite3.connect('MHistory.db')
        cursor = conn.cursor()

        # SQL запрос с использованием параметризованного запроса
        sql_query = "SELECT id, dataAdd, id_module, templates_for_marking, OrderID FROM Orders WHERE OrderID = ? ORDER BY dataAdd DESC LIMIT 1"
        cursor.execute(sql_query, (OrderID,))  # Передаем значение Module как параметр
        orders = cursor.fetchall()

        # Если данные найдены, возвращаем их
        if orders:
            logging.info(f"getPathAPI - Found {len(orders)} orders for module: {OrderID}")
            return orders
        else:
            logging.warning(f"getPathAPI - No orders found for module: {OrderID}")
            return None
    except Exception as e:
        logging.error(f"getPathAPI - Error fetching orders from database: {e}")
    finally:
        # Закрываем соединение, если оно было успешно создано
        if 'conn' in locals():
            conn.close()
            logging.info("getPathAPI - Database connection closed.")

# 3. Получаем путь до шаблона.
def getPathTemplate(orders):
    if orders:
        for order in orders:      
            logging.info(f"getPathAPI - Recived path:{order[2]}")
            path = order[3] 
            OrderID = order[4]
            idTemplate = order[0]
            return path, OrderID, idTemplate
        else:
            logging.info(f"getPathAPI - NO path Template")
            return ""
        
# 4. Функция для копирования шаблона в папку Templates
def save_template_to_project_folder(template_path, OrderID, idTemplate):
    if template_path and OrderID:
        # Получаем текущее время
        safe_dataAdd = datetime.now().strftime('%Y-%m-%d %H-%M-%S')  # Форматируем время

        logging.info(f"getPathAPI - Current time for pathtemplate: {safe_dataAdd}")

        # Путь к папке Templates текущего проекта
        templates_folder = "Templates"

        # Проверяем, существует ли папка Templates, если нет, создаем её
        if not os.path.exists(templates_folder):
            os.makedirs(templates_folder)
            logging.info(f"getPathAPI - Created 'Templates' folder at {templates_folder}")
            
        # Путь назначения для файла
        file_name = f"{safe_dataAdd}_{OrderID}_{idTemplate}.le"
        destination_path = os.path.join(templates_folder, file_name)
        
        # Копируем файл по новому пути
        try:
            shutil.copy(template_path, destination_path)
            logging.info(f"getPathAPI - File successfully copied to {destination_path}")
        except FileNotFoundError:
            logging.error(f"getPathAPI - Error: file not found at {template_path}")
        except Exception as e:
            logging.error(f"getPathAPI - Error copying file: {e}")
    else:
        logging.error(f"getPathAPI - Not path in ave_template_to_project_folder")
        return 
    

"""
# Получаем один последний шалон для заказа
orders = fetch_orders_from_db('ЗНП-0002186')
print(orders)
path, OrderID, idTemplate = getPathTemplate(orders)
print(path)
print(OrderID)
print(idTemplate)
save_template_to_project_folder(path, OrderID, idTemplate)

"""




