#  pyinstaller --onefile GUIListOrders.py

import tkinter as tk
import sqlite3
from datetime import datetime
import re
from tkinter import filedialog

def get_data(order_id):
    conn = sqlite3.connect('MHistory.db')
    cursor = conn.cursor()
    query = """
    SELECT S.id, S.number9 AS QR, S.number8 AS Serial, S.Marked, S.DataMarked
    FROM Serial_Numbers AS S
    LEFT JOIN Orders AS O ON S.order_id = O.id
    WHERE S.Order_id = ?;
    """
    cursor.execute(query, (order_id,))
    data = cursor.fetchall()
    conn.close()
    return data

def update_data(frame, order_id):
    data = get_data(order_id)
    for widget in frame.winfo_children():
        widget.destroy()

    num_columns = 6
    for i, row in enumerate(data):
        marked = row[3]
        bg_color = "green" if marked == 1 else "white"

        row_index = i // num_columns
        column_index = i % num_columns

        checkbox = tk.Checkbutton(frame, text=row[1] + " " + row[2],
                                  bg=bg_color,
                                  command=lambda i=i: toggle_marked(i, order_id))
        checkbox.grid(row=row_index, column=column_index, padx=5, pady=5, sticky="w")
        checkbox.var = tk.IntVar(value=marked)
        checkbox.config(variable=checkbox.var)

    frame.after(2000, update_data, frame, order_id)

def toggle_marked(index, order_id):
    conn = sqlite3.connect('MHistory.db')
    cursor = conn.cursor()
    query = """
    SELECT id, Marked, DataMarked FROM Serial_Numbers
    WHERE Order_id = ?
    LIMIT 1 OFFSET ?;
    """
    cursor.execute(query, (order_id, index))
    row = cursor.fetchone()

    if row[1] == 0:
        new_marked_value = 1
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_query = """
        UPDATE Serial_Numbers
        SET Marked = ?, DataMarked = ?
        WHERE id = ?;
        """
        cursor.execute(update_query, (new_marked_value, current_time, row[0]))
    else:
        new_marked_value = 0
        update_query = """
        UPDATE Serial_Numbers
        SET Marked = ?, DataMarked = NULL
        WHERE id = ?;
        """
        cursor.execute(update_query, (new_marked_value, row[0]))

    conn.commit()
    conn.close()

def extract_order_id_from_filename(filename):
    match = re.search(r'_(\d+)\.le$', filename)
    if match:
        return int(match.group(1))
    else:
        return None

def select_file_and_load_data(frame, load_button):
    filepath = filedialog.askopenfilename(
        title="Выберите документ",
        filetypes=[("LE Files", "*.le")]
    )

    if filepath:
        order_id = extract_order_id_from_filename(filepath)
        if order_id is not None:
            update_data(frame, order_id)
            load_button.config(state='disabled')
        else:
            error_label = tk.Label(frame, text="Ошибка: не найден номер заказа в имени документа!", fg="red")
            error_label.grid(row=0, column=0, padx=10, pady=10)

def run_gui():
    root = tk.Tk()
    root.title("Data Viewer")

    canvas = tk.Canvas(root)
    v_scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    h_scrollbar = tk.Scrollbar(root, orient="horizontal", command=canvas.xview)

    canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    v_scrollbar.pack(side="right", fill="y")
    h_scrollbar.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # Прокрутка колесом мыши (кроссплатформенно)
    def _on_mousewheel(event):
        if event.delta:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

    # Привязка колесика мыши
    canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows
    canvas.bind_all("<Button-4>", _on_mousewheel)    # Linux (up)
    canvas.bind_all("<Button-5>", _on_mousewheel)    # Linux (down)

    # Кнопка загрузки
    load_button = tk.Button(root, text="Выбрать файл и загрузить данные",
                            command=lambda: select_file_and_load_data(scrollable_frame, load_button))
    load_button.pack(padx=10, pady=5)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
