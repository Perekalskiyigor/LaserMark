import tkinter as tk
import sqlite3
from datetime import datetime

# Функция для получения данных из базы данных
def get_data():
    conn = sqlite3.connect('MHistory.db')  # Подключаемся к базе данных
    cursor = conn.cursor()
    query = """
    SELECT S.id, S.number9 AS QR, S.number8 AS Serial, S.Marked, S.DataMarked
    FROM Serial_Numbers AS S
    LEFT JOIN Orders AS O
    ON S.order_id = O.id
    WHERE S.Order_id = 76;
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data

# Функция для обновления отображаемых данных
def update_data(frame):
    data = get_data()  # Получаем новые данные из базы
    for widget in frame.winfo_children():
        widget.destroy()  # Удаляем старые виджеты

    # Определяем, сколько записей разместить в одном столбце
    num_columns = 4
    for i, row in enumerate(data):
        marked = row[3]
        bg_color = "green" if marked == 1 else "white"
        
        # Индекс строки и столбца для размещения виджетов
        row_index = i // num_columns  # Индекс строки
        column_index = i % num_columns  # Индекс столбца

        # Создаем чекбокс и лейбл для каждой записи
        checkbox = tk.Checkbutton(frame, text=row[1] + " " + row[2], 
                                  bg=bg_color, 
                                  command=lambda i=i: toggle_marked(i))
        checkbox.grid(row=row_index, column=column_index, padx=5, pady=5, sticky="w")
        checkbox.var = tk.IntVar(value=marked)
        checkbox.config(variable=checkbox.var)
    
    frame.after(2000, update_data, frame)  # Обновляем данные каждые 2 секунды

# Функция для обновления значения S.Marked и добавления/удаления времени
def toggle_marked(index):
    conn = sqlite3.connect('MHistory.db')
    cursor = conn.cursor()
    
    # Получаем id текущей записи
    query = """
    SELECT id, Marked, DataMarked FROM Serial_Numbers
    WHERE Order_id = 76
    LIMIT 1 OFFSET ?;
    """
    cursor.execute(query, (index,))
    row = cursor.fetchone()
    
    # Если галочку ставим, добавляем текущее время
    if row[1] == 0:
        new_marked_value = 1
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Текущее время
        update_query = """
        UPDATE Serial_Numbers
        SET Marked = ?, DataMarked = ?
        WHERE id = ?;
        """
        cursor.execute(update_query, (new_marked_value, current_time, row[0]))
    else:
        # Если галочку снимаем, удаляем время
        new_marked_value = 0
        update_query = """
        UPDATE Serial_Numbers
        SET Marked = ?, DataMarked = NULL
        WHERE id = ?;
        """
        cursor.execute(update_query, (new_marked_value, row[0]))
    
    conn.commit()
    conn.close()

# Основной интерфейс
def run_gui():
    root = tk.Tk()
    root.title("Data Viewer")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    # Начальная загрузка данных
    update_data(frame)

    root.mainloop()

# Этот код будет выполняться только если скрипт запускается напрямую
if __name__ == "__main__":
    run_gui()
